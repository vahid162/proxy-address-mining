"""Read-only Phase 11 controlled filter packet-path evidence collector."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.adapters.phase11_read_only_command import Phase11ReadOnlyCommandAdapter, ReadOnlyCommandResult, all_static_allowed_argv
from mpf.domain.phase11_controlled_filter_packet_path import (
    BACKEND_CONTAINER,
    BACKEND_PORT,
    BLOCKED,
    COMPOSE_PROJECT,
    COMPOSE_SERVICE,
    CONTROLLED_CUSTOMERS,
    DOCKER_NETWORK,
    EXPECTED_VERSION,
    INVALID,
    NEXT_REQUIRED_STEP,
    REQUIRED_PHASE_FLAGS,
)
from mpf.services.phase11_controlled_filter_packet_path_bundle_service import canonical_json_bytes, sha256_bytes, verify_packet_path_bundle, write_packet_path_bundle
from mpf.services.phase11_controlled_filter_packet_path_decision_service import decide_controlled_filter_packet_path
from mpf.services.phase11_controlled_filter_packet_path_graph_service import build_packet_path_graph
from mpf.services.phase11_packet_path_topology_resolver import resolve_docker_bridge, validate_backend_ipv4, verify_backend_membership
from mpf.services.phase11_firewall_packet_path_parser import parse_iptables_save_topology


def build_controlled_filter_packet_path_plan(*, adapter: Phase11ReadOnlyCommandAdapter | None = None, phase_status_text: str | None = None) -> dict[str, Any]:
    return _collect(adapter=adapter or Phase11ReadOnlyCommandAdapter(), phase_status_text=phase_status_text, write_dir=None)["summary"]


def collect_controlled_filter_packet_path_bundle(*, output_dir: Path | str, adapter: Phase11ReadOnlyCommandAdapter | None = None, phase_status_text: str | None = None) -> dict[str, Any]:
    result = _collect(adapter=adapter or Phase11ReadOnlyCommandAdapter(), phase_status_text=phase_status_text, write_dir=Path(output_dir))
    return result["summary"]


def verify_controlled_filter_packet_path_bundle(*, evidence_dir: Path | str) -> dict[str, Any]:
    return verify_packet_path_bundle(evidence_dir)


def read_only_command_allowlist() -> dict[str, Any]:
    allowed = all_static_allowed_argv()
    allowed["ip_route_get_backend"] = ["ip", "-json", "route", "get", "<validated-current-backend-ipv4>"]
    allowed["ip_route_get_backend_ingress"] = ["ip", "-json", "route", "get", "<validated-current-backend-ipv4>", "from", "198.51.100.77", "iif", "<validated-ingress-interface>"]
    return {"allowlist": allowed, "shell": False, "mutation_commands_allowed": False, "mutation_performed": False}


def _collect(*, adapter: Phase11ReadOnlyCommandAdapter, phase_status_text: str | None, write_dir: Path | None) -> dict[str, Any]:
    collection_id = str(uuid.uuid4())
    collected_at = _now()
    commands: list[ReadOnlyCommandResult] = []
    invalid: list[str] = []

    def run(command_id: str, **kwargs: Any) -> ReadOnlyCommandResult:
        res = adapter.run(command_id, **kwargs)
        commands.append(res)
        return res

    hostname_res = run("hostname", require_non_empty=True)
    uname_res = run("uname_kernel", require_non_empty=True)
    ipt4 = run("iptables_save", require_non_empty=True)
    ipt6 = run("ip6tables_save", require_non_empty=True)
    run("iptables_version", require_non_empty=True)
    run("ip6tables_version", require_non_empty=True)
    docker_inspect = run("docker_inspect_backend", redact_stdout=True, require_non_empty=True)
    docker_net = run("docker_network_inspect", redact_stdout=True, require_non_empty=True)
    docker_ps = run("docker_ps_compose", require_non_empty=False)
    ip_addr = run("ip_address", require_non_empty=True)
    ip_link = run("ip_link", require_non_empty=True)
    ip_route_all = run("ip_route_all", require_non_empty=True)
    ip_rule = run("ip_rule", require_non_empty=True)
    bridge = run("bridge_link", require_non_empty=False)
    ss = run("ss_listeners", require_non_empty=False)
    ss_backend = run("ss_backend_listener", require_non_empty=False)

    hostname = _stdout(hostname_res).strip() or socket.gethostname()
    kernel = _stdout(uname_res).strip()
    phase_text = phase_status_text if phase_status_text is not None else _read_phase_status_text()
    phase_flags = _extract_phase_flags(phase_text)
    phase_blockers = [f"phase_gate_missing_or_mismatch:{k}" for k, v in REQUIRED_PHASE_FLAGS.items() if phase_flags.get(k) != v]

    docker_raw = _stdout(docker_inspect) if docker_inspect.return_code == 0 else ""
    net_raw = _stdout(docker_net) if docker_net.return_code == 0 else ""
    backend = _sanitize_backend(docker_raw, ss_backend_stdout=_stdout(ss_backend))
    network = _sanitize_network(net_raw, docker_ps_stdout=_stdout(docker_ps), expected_container_id=str(backend.get("container_id") or ""))
    backend = _join_backend_network_projection(backend, network)
    invalid.extend(str(item) for item in backend.get("blockers", []) if str(item).endswith("json_invalid"))
    invalid.extend(str(item) for item in network.get("blockers", []) if str(item).endswith("json_invalid"))
    backend_ip = str(backend.get("resolved_ipv4") or "")
    if backend_ip:
        _, backend_ip_blockers = validate_backend_ipv4(backend_ip, source=str(backend.get("backend_target_source") or "unknown"))
        if backend_ip_blockers:
            backend["status"] = "blocked"
            backend.setdefault("blockers", []).extend(backend_ip_blockers)
    if backend_ip and backend.get("backend_target_source") in {"docker_inspect_verified", "docker_network_inspect_verified", "operator_package_bound"}:
        route_get = run("ip_route_get_backend", backend_ipv4=backend_ip, require_non_empty=True)
    else:
        route_get = None

    parsed4 = parse_iptables_save_topology(_stdout(ipt4), ipv6=False).to_dict()
    parsed6 = parse_iptables_save_topology(_stdout(ipt6), ipv6=True).to_dict()
    ip_addr_json, e = _json_required("ip_address", _stdout(ip_addr)); invalid.extend(e)
    ip_link_json, e = _json_required("ip_link", _stdout(ip_link)); invalid.extend(e)
    ip_route_json, e = _json_required("ip_route_all", _stdout(ip_route_all)); invalid.extend(e)
    ip_rule_json, e = _json_required("ip_rule", _stdout(ip_rule)); invalid.extend(e)
    route_get_json, e = _json_required("route_get", _stdout(route_get), required=route_get is not None); invalid.extend(e)
    bridge_json, e = _json_required("bridge_link", _stdout(bridge), required=bool(_stdout(bridge).strip()) and bridge.return_code == 0); invalid.extend(e)
    bridge_resolution = resolve_docker_bridge(network=network, links=ip_link_json, routes=ip_route_json, parsed_ipv4=parsed4)
    if bridge_resolution.get("bridge_name"):
        network.update({k: v for k, v in bridge_resolution.items() if k != "blockers"})
        network.setdefault("blockers", []).extend(bridge_resolution.get("blockers", []))
        if bridge_resolution.get("blockers"):
            network["status"] = "blocked"
        fdb_res = run("bridge_fdb_backend", bridge_name=str(bridge_resolution.get("bridge_name")), require_non_empty=False)
        link_master_res = run("ip_link_master_bridge", bridge_name=str(bridge_resolution.get("bridge_name")), require_non_empty=False)
    else:
        fdb_res = None
        link_master_res = None
    fdb_json, e = _json_required("bridge_fdb_backend", _stdout(fdb_res), required=bool(fdb_res and _stdout(fdb_res).strip() and fdb_res.return_code == 0)); invalid.extend(e)
    link_master_json, e = _json_required("ip_link_master_bridge", _stdout(link_master_res), required=bool(link_master_res and _stdout(link_master_res).strip() and link_master_res.return_code == 0)); invalid.extend(e)
    combined_links = ip_link_json + link_master_json
    membership = verify_backend_membership(bridge_name=str(network.get("bridge_name") or ""), backend=backend, links=combined_links, fdb_entries=fdb_json if fdb_json else bridge_json)
    backend_bridge_membership_verified = membership["verified"]
    external_ingress_interfaces = _external_ingress_interfaces(ip_addr_json, str(network.get("bridge_name") or ""))
    route_get_backend_by_ingress: dict[str, list[Any]] = {}
    route_get_backend_by_ingress_refs: dict[str, dict[str, Any]] = {}
    for ingress in external_ingress_interfaces:
        ifname = str(ingress.get("ifname") or "")
        if backend_ip and ifname:
            res = adapter.run("ip_route_get_backend_ingress", backend_ipv4=backend_ip, ingress_ifname=ifname, require_non_empty=True)
            res = replace(res, command_id=f"ip_route_get_backend_ingress:{ifname}")
            commands.append(res)
            rows, err = _json_required(f"route_get_backend_ingress:{ifname}", _stdout(res), required=True)
            invalid.extend(err)
            route_get_backend_by_ingress[ifname] = rows
            route_get_backend_by_ingress_refs[ifname] = {"command_id": res.command_id, "stdout_sha256": res.stdout_sha256, "evidence_ref": f"command-results.json:{res.command_id}"}
    firewall_backend = _firewall_backend_consistency(_stdout(next((c for c in commands if c.command_id == "iptables_version"), None)), _stdout(next((c for c in commands if c.command_id == "ip6tables_version"), None)))
    nat_analysis = _nat_insertion_analysis(parsed4, external_ingress_interfaces)
    host_topology = {
        "collection_id": collection_id,
        "hostname": hostname,
        "host_addresses": _host_addresses(ip_addr_json),
        "links": ip_link_json,
        "bridge_link_master": link_master_json,
        "bridge_fdb": fdb_json,
        "routes": ip_route_json,
        "policy_rules": ip_rule_json,
        "route_get_backend": route_get_json,
        "route_get_backend_by_ingress": route_get_backend_by_ingress,
        "route_get_backend_by_ingress_refs": route_get_backend_by_ingress_refs,
        "bridge_links": bridge_json,
        "backend_bridge_membership_verified": backend_bridge_membership_verified,
        "backend_bridge_membership_status": membership["status"],
        "backend_bridge_membership_evidence": membership.get("methods", membership.get("evidence", [])),
        "ip_forward": _read_proc_value("/proc/sys/net/ipv4/ip_forward"),
        "sysctl": _sysctl_evidence([str(item.get("ifname")) for item in external_ingress_interfaces if isinstance(item, dict)]),
        "route_localnet": _route_localnet_values(),
        "listening_sockets": _stdout(ss).splitlines(),
        "external_ingress_interfaces": external_ingress_interfaces,
        "firewall_backend": firewall_backend,
        "nat_insertion_analysis": nat_analysis,
        "mutation_performed": False,
    }
    parsed_firewall = {"collection_id": collection_id, "hostname": hostname, "ipv4": parsed4, "ipv6": parsed6, "mutation_performed": False}
    graph_obj = build_packet_path_graph(collection_id=collection_id, hostname=hostname, backend=backend, network=network, topology=host_topology, parsed_ipv4=parsed4)
    graph = graph_obj.to_dict()
    graph["proposed_review_only_graph"] = [
        "external_ingress", "nat PREROUTING", "future controlled MPF NAT entry", f"DNAT dynamic backend IPv4:{BACKEND_PORT}",
        "post-DNAT route decision", "verified built-in filter path", "verified user-policy hook", "future MPF filter entry",
        "customer dispatch using proven post-DNAT/original-destination semantics", "whitelist/default-deny", "connlimit/hashlimit", "accounting", "backend bridge", "backend container",
    ]
    command_meta = [c.metadata() for c in commands]
    evidence = {
        "component": "phase11_controlled_filter_packet_path_evidence",
        "repository_version": __version__,
        "expected_version": EXPECTED_VERSION,
        "hostname": hostname,
        "kernel_version": kernel,
        "collection_id": collection_id,
        "collected_at": collected_at,
        "phase_status_sha256": hashlib.sha256(phase_text.encode()).hexdigest(),
        "authoritative_current_phase_flags": phase_flags,
        "phase_gate_blockers": phase_blockers,
        "parse_errors": invalid,
        "sanitized_config_projection": {"controlled_scope": list(CONTROLLED_CUSTOMERS), "backend_container": BACKEND_CONTAINER, "docker_network": DOCKER_NETWORK, "backend_port": BACKEND_PORT},
        "sanitized_config_projection_hash": sha256_bytes(canonical_json_bytes({"controlled_scope": list(CONTROLLED_CUSTOMERS), "backend_container": BACKEND_CONTAINER, "docker_network": DOCKER_NETWORK, "backend_port": BACKEND_PORT})),
        "backend_target": backend,
        "docker_network": network,
        "host_topology": host_topology,
        "packet_path_schema_version": "0.1.252",
        "component_statuses": {"backend_container_status": backend.get("status"), "docker_network_identity_status": "ok" if network.get("network_id") and network.get("network_name") == DOCKER_NETWORK else "blocked", "docker_bridge_resolution_status": "ok" if network.get("bridge_name_verified") else "blocked", "backend_route_status": "ok" if route_get_json else "blocked", "backend_bridge_membership_status": membership.get("status"), "firewall_parse_status": "ok" if not parsed4.get("errors") and not parsed6.get("errors") else "blocked", "firewall_backend_status": firewall_backend.get("status"), "packet_path_status": "pending_decision"},
        "evidence_hashes": {"iptables_save_sha256": parsed4.get("source_sha256"), "ip6tables_save_sha256": parsed6.get("source_sha256")},
        "proof_scope": "static_pre_apply_topology_and_ruleset",
        "runtime_packet_observed": False,
        "post_apply_runtime_verified": False,
        "mutation_performed": False,
    }
    if phase_blockers:
        invalid.extend(phase_blockers)
    if invalid:
        command_meta.append({"command_id": "collector_precondition", "argv": [], "started_at": collected_at, "finished_at": collected_at, "duration_ms": 0, "return_code": 65, "timed_out": False, "stdout_size": 0, "stderr_size": len(";".join(invalid)), "stdout_sha256": hashlib.sha256(b"").hexdigest(), "stderr_sha256": hashlib.sha256(";".join(invalid).encode()).hexdigest(), "output_truncated": False, "mutation_performed": False})
    decision = decide_controlled_filter_packet_path(evidence=evidence, graph=graph, parsed_firewall=parsed_firewall, command_results=command_meta).to_dict()
    bundle = {
        "evidence": evidence,
        "decision": decision,
        "sanitized_backend_target": {"collection_id": collection_id, "hostname": hostname, **backend},
        "sanitized_docker_network": {"collection_id": collection_id, "hostname": hostname, **network},
        "iptables_save_text": _stdout(ipt4),
        "ip6tables_save_text": _stdout(ipt6),
        "parsed_firewall": parsed_firewall,
        "host_topology": host_topology,
        "graph": graph,
        "command_results": command_meta,
    }
    write_result = None
    if write_dir is not None:
        write_result = write_packet_path_bundle(bundle, write_dir)
    summary = {
        "component": "phase11_controlled_filter_packet_path",
        "repository_version": __version__,
        "collection_id": collection_id,
        "hostname": hostname,
        "final_decision": decision["final_decision"],
        "collection_preflight_safe": decision["final_decision"] != INVALID,
        "proof_scope": decision["proof_scope"],
        "runtime_packet_observed": False,
        "post_apply_runtime_verified": False,
        "controlled_artifact_package_ready": False,
        "artifact_graph_binding_ready": False,
        "production_execution_available": False,
        "next_required_step": NEXT_REQUIRED_STEP,
        "blockers": decision.get("blockers", []),
        "warnings": decision.get("warnings", []),
        "decision": decision,
        "bundle": write_result,
        "mutation_performed": False,
    }
    return {"bundle": bundle, "summary": summary}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stdout(result: ReadOnlyCommandResult | None) -> str:
    return "" if result is None or result.stdout is None else result.stdout


def _json_required(command_id: str, text: str, *, required: bool = True) -> tuple[list[Any], list[str]]:
    if not text.strip():
        return [], [] if not required else [f"{command_id}_json_empty"]
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return [], [f"{command_id}_json_invalid"]
    if not isinstance(value, list):
        return [], [f"{command_id}_json_not_array"]
    return value, []


def _backend_bridge_membership_status(bridge_links: list[Any], backend: dict[str, Any], network: dict[str, Any]) -> dict[str, Any]:
    bridge = str(network.get("bridge_name") or "")
    endpoint_id = str(backend.get("endpoint_id") or "")
    mac = str(backend.get("mac_address") or "").lower()
    if not bridge_links or not bridge or not endpoint_id:
        return {"verified": False, "status": "unresolved", "evidence": []}
    evidence: list[dict[str, Any]] = []
    for item in bridge_links:
        if not isinstance(item, dict):
            continue
        if item.get("master") != bridge and item.get("ifname") != bridge and item.get("link") != bridge:
            continue
        item_endpoint = str(item.get("endpoint_id") or item.get("docker_endpoint_id") or "")
        item_mac = str(item.get("address") or item.get("mac_address") or "").lower()
        if item_endpoint and item_endpoint == endpoint_id:
            evidence.append({"method": "endpoint_id", "ifname": item.get("ifname"), "endpoint_id": endpoint_id})
        elif mac and item_mac and item_mac == mac:
            evidence.append({"method": "mac_address", "ifname": item.get("ifname"), "mac_address": mac})
    if evidence:
        return {"verified": True, "status": "verified", "evidence": evidence}
    return {"verified": False, "status": "unresolved", "evidence": []}


def _read_phase_status_text() -> str:
    try:
        return Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_phase_flags(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip("- `")
        val = val.strip(" `")
        if key in REQUIRED_PHASE_FLAGS and key not in out:
            out[key] = val
    return out


def _sanitize_backend(raw: str, *, ss_backend_stdout: str) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        parsed = json.loads(raw)
        container = parsed[0] if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) else {}
    except json.JSONDecodeError:
        container = {}
        blockers.append("docker_inspect_json_invalid")
    if not container:
        blockers.append("backend_container_missing")
    state = container.get("State", {}) if isinstance(container.get("State"), dict) else {}
    config = container.get("Config", {}) if isinstance(container.get("Config"), dict) else {}
    labels = config.get("Labels", {}) if isinstance(config.get("Labels"), dict) else {}
    host_config = container.get("HostConfig", {}) if isinstance(container.get("HostConfig"), dict) else {}
    net_settings = container.get("NetworkSettings", {}) if isinstance(container.get("NetworkSettings"), dict) else {}
    networks = net_settings.get("Networks", {}) if isinstance(net_settings.get("Networks"), dict) else {}
    net = networks.get(DOCKER_NETWORK, {}) if isinstance(networks.get(DOCKER_NETWORK), dict) else {}
    running = state.get("Running") is True
    health_obj = state.get("Health") if isinstance(state.get("Health"), dict) else None
    health = health_obj.get("Status") if isinstance(health_obj, dict) else None
    if labels.get("com.docker.compose.project") != COMPOSE_PROJECT:
        blockers.append("backend_container_compose_project_mismatch")
    if labels.get("com.docker.compose.service") != COMPOSE_SERVICE:
        blockers.append("backend_container_compose_service_mismatch")
    if not running:
        blockers.append("backend_container_not_running")
    if health is None:
        blockers.append("backend_container_health_missing")
    elif health != "healthy":
        blockers.append("backend_container_unhealthy")
    if DOCKER_NETWORK not in networks:
        blockers.append("backend_container_expected_network_missing")
    publishes = _published_ports(net_settings)
    if any(p.get("public") for p in publishes):
        blockers.append("backend_docker_publish_public")
    listeners = [line for line in ss_backend_stdout.splitlines() if ":60010" in line]
    public_listener = any(("0.0.0.0:60010" in line or "*:60010" in line or "[::]:60010" in line) for line in listeners)
    if public_listener:
        blockers.append("backend_host_listener_public")
    ip = str(net.get("IPAddress") or "")
    fingerprint_input = {"container_name": BACKEND_CONTAINER, "container_id": container.get("Id"), "network_name": DOCKER_NETWORK, "network_id": net.get("NetworkID"), "endpoint_id": net.get("EndpointID"), "resolved_ipv4": ip, "backend_port": BACKEND_PORT}
    return {
        "status": "ok" if not blockers else "blocked",
        "container_name": container.get("Name", "").lstrip("/") or BACKEND_CONTAINER,
        "container_id": container.get("Id"),
        "image_id": container.get("Image"),
        "running": running,
        "health_state": health,
        "network_mode": host_config.get("NetworkMode"),
        "restart_policy": host_config.get("RestartPolicy", {}).get("Name") if isinstance(host_config.get("RestartPolicy"), dict) else None,
        "compose_project": labels.get("com.docker.compose.project"),
        "compose_service": labels.get("com.docker.compose.service"),
        "connected_networks": sorted({name: {"network_id": val.get("NetworkID"), "ipv4_address": val.get("IPAddress"), "prefix_len": val.get("IPPrefixLen")} for name, val in networks.items() if isinstance(val, dict)}.items()),
        "network_id": net.get("NetworkID"),
        "endpoint_id": net.get("EndpointID"),
        "backend_target_source": "docker_inspect_verified" if ip else "unknown",
        "mac_address": net.get("MacAddress"),
        "resolved_ipv4": ip,
        "container_ipv4_prefix": net.get("IPPrefixLen"),
        "backend_port": BACKEND_PORT,
        "published_port_bindings": publishes,
        "exposed_ports": sorted((config.get("ExposedPorts") or {}).keys()) if isinstance(config.get("ExposedPorts"), dict) else [],
        "backend_public_exposure": any(p.get("public") for p in publishes) or public_listener,
        "host_listener_state": {"listeners": listeners, "public": public_listener},
        "docker_publish_state": {"public": any(p.get("public") for p in publishes), "bindings": publishes},
        "public_exposure_classification": "public" if any(p.get("public") for p in publishes) or public_listener else "non_public",
        "historical_hardcoded_target_assumed": False,
        "target_fingerprint_input": fingerprint_input,
        "target_fingerprint": sha256_bytes(canonical_json_bytes(fingerprint_input)),
        "blockers": sorted(set(blockers)),
        "mutation_performed": False,
    }


def _join_backend_network_projection(backend: dict[str, Any], network: dict[str, Any]) -> dict[str, Any]:
    connected = network.get("connected_allowlisted_mpf_containers", [])
    backend_id = str(backend.get("container_id") or "")
    backend_ip = str(backend.get("resolved_ipv4") or "")
    row = None
    for item in connected if isinstance(connected, list) else []:
        if isinstance(item, dict) and item.get("container_id") == backend_id:
            row = item
            break
    backend["network_inspect_container_id_match"] = row is not None
    backend["network_inspect_ipv4_match"] = bool(row and str(row.get("ipv4_address") or "") == backend_ip)
    backend["network_id"] = backend.get("network_id") or network.get("network_id") if row is not None else backend.get("network_id")
    if row is None:
        backend.setdefault("blockers", []).append("backend_container_missing_from_network_inspect")
    elif str(row.get("ipv4_address") or "") != backend_ip:
        backend.setdefault("blockers", []).append("backend_ipv4_mismatch_between_inspects")
    if backend.get("blockers"):
        backend["status"] = "blocked"
    return backend


def _sanitize_network(raw: str, *, docker_ps_stdout: str, expected_container_id: str) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        parsed = json.loads(raw)
        net = parsed[0] if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) else {}
    except json.JSONDecodeError:
        net = {}
        blockers.append("docker_network_inspect_json_invalid")
    if not net:
        blockers.append("docker_network_missing")
    ipam = net.get("IPAM", {}) if isinstance(net.get("IPAM"), dict) else {}
    configs = ipam.get("Config", []) if isinstance(ipam.get("Config"), list) else []
    first_cfg = configs[0] if configs and isinstance(configs[0], dict) else {}
    containers = net.get("Containers", {}) if isinstance(net.get("Containers"), dict) else {}
    allowed_names = {BACKEND_CONTAINER, "mpf-v2raya", "mpf-v2raya-socks-bridge"}
    connected = []
    unknown = []
    for cid, info in containers.items():
        if not isinstance(info, dict):
            continue
        name = str(info.get("Name") or "")
        row = {"container_id": cid, "name": name, "endpoint_id": info.get("EndpointID"), "mac_address": info.get("MacAddress"), "ipv4_address": str(info.get("IPv4Address") or "").split("/")[0], "raw_ipv4": info.get("IPv4Address")}
        if name in allowed_names:
            connected.append(row)
        else:
            unknown.append(row)
    if unknown:
        blockers.append("unknown_connected_container")
    if expected_container_id and not any(item.get("container_id") == expected_container_id for item in connected):
        blockers.append("backend_container_id_missing_from_network")
    if net.get("Name") != DOCKER_NETWORK:
        blockers.append("docker_network_name_mismatch")
    if net.get("Driver") != "bridge":
        blockers.append("docker_network_driver_not_bridge")
    net_id = net.get("Id")
    if not net_id:
        blockers.append("docker_network_id_missing")
    bridge_name = (net.get("Options") or {}).get("com.docker.network.bridge.name") if isinstance(net.get("Options"), dict) else None
    try:
        if first_cfg.get("Subnet"):
            ipaddress.ip_network(str(first_cfg.get("Subnet")), strict=False)
        else:
            blockers.append("docker_network_subnet_missing")
    except ValueError:
        blockers.append("docker_network_subnet_invalid")
    gateway_invalid = False
    try:
        if first_cfg.get("Gateway"):
            ipaddress.ip_address(str(first_cfg.get("Gateway")))
        else:
            gateway_invalid = True
    except ValueError:
        gateway_invalid = True
    if gateway_invalid:
        blockers.append("docker_network_gateway_invalid")
    return {
        "status": "ok" if not blockers else "blocked",
        "network_name": net.get("Name"),
        "network_id": net_id,
        "driver": net.get("Driver"),
        "internal": net.get("Internal"),
        "attachable": net.get("Attachable"),
        "ipv4_subnet": first_cfg.get("Subnet"),
        "gateway": first_cfg.get("Gateway"),
        "gateway_invalid": gateway_invalid,
        "bridge_name_explicit": bridge_name,
        "bridge_name": bridge_name,
        "connected_allowlisted_mpf_containers": connected,
        "unknown_connected_containers": unknown,
        "docker_ps_compose_lines": docker_ps_stdout.splitlines(),
        "blockers": sorted(set(blockers)),
        "mutation_performed": False,
    }


def _published_ports(net_settings: dict[str, Any]) -> list[dict[str, Any]]:
    ports = net_settings.get("Ports", {}) if isinstance(net_settings.get("Ports"), dict) else {}
    out: list[dict[str, Any]] = []
    for container_port, bindings in ports.items():
        for binding in bindings or []:
            if not isinstance(binding, dict):
                continue
            host_ip = str(binding.get("HostIp") or "")
            public = host_ip in {"0.0.0.0", "::"} or (host_ip and not host_ip.startswith("127.") and host_ip not in {"::1", "localhost"})
            out.append({"container_port": container_port, "host_ip": host_ip, "host_port": binding.get("HostPort"), "public": public})
    return out


def _host_addresses(data: list[Any]) -> list[dict[str, Any]]:
    out = []
    for link in data:
        if not isinstance(link, dict):
            continue
        for addr in link.get("addr_info", []) if isinstance(link.get("addr_info"), list) else []:
            if isinstance(addr, dict) and addr.get("family") == "inet":
                out.append({"ifname": link.get("ifname"), "local": addr.get("local"), "prefixlen": addr.get("prefixlen")})
    return out


def _read_proc_value(path: str, *, optional: bool = False) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None if optional else "unavailable"


def _route_localnet_values() -> dict[str, str]:
    out = {}
    root = Path("/proc/sys/net/ipv4/conf")
    try:
        for item in root.iterdir():
            path = item / "route_localnet"
            if path.exists():
                out[item.name] = path.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return out


def _external_ingress_interfaces(ip_addr_json: list[Any], bridge: str) -> list[dict[str, Any]]:
    out=[]
    for item in ip_addr_json:
        if not isinstance(item, dict):
            continue
        name=str(item.get("ifname") or "")
        if not name or name in {"lo", bridge} or name.startswith(("br-", "docker", "veth")):
            continue
        if any(isinstance(a, dict) and a.get("family") == "inet" for a in item.get("addr_info", []) if isinstance(item.get("addr_info"), list)):
            out.append({"ifname": name, "source_class": "external_nonlocal_source"})
    return out


def _sysctl_evidence(ingress_ifnames: list[str]) -> dict[str, Any]:
    rp: dict[str, dict[str, Any]] = {}
    for name in ["all", "default", *ingress_ifnames]:
        path = f"/proc/sys/net/ipv4/conf/{name}/rp_filter"
        value = _read_proc_value(path, optional=True)
        rp[name] = {"available": value is not None, "value": value, "path": path}
    bridge4 = _read_proc_value("/proc/sys/net/bridge/bridge-nf-call-iptables", optional=True)
    bridge6 = _read_proc_value("/proc/sys/net/bridge/bridge-nf-call-ip6tables", optional=True)
    return {
        "net.ipv4.ip_forward": _read_proc_value("/proc/sys/net/ipv4/ip_forward"),
        "net.ipv4.conf.rp_filter": rp,
        "net.bridge.bridge-nf-call-iptables": {"available": bridge4 is not None, "value": bridge4},
        "net.bridge.bridge-nf-call-ip6tables": {"available": bridge6 is not None, "value": bridge6},
    }


def _classify_iptables_backend(version: str) -> str:
    text = version.lower()
    if "nf_tables" in text or "nf_tables" in text.replace("-", "_"):
        return "nf_tables"
    if "legacy" in text:
        return "legacy"
    return "unknown"


def _firewall_backend_consistency(iptables_version: str, ip6tables_version: str) -> dict[str, Any]:
    ipv4 = _classify_iptables_backend(iptables_version)
    ipv6 = _classify_iptables_backend(ip6tables_version)
    blockers: list[str] = []
    if ipv4 == "unknown" or ipv6 == "unknown":
        blockers.append("firewall_backend_unknown")
    if ipv4 != ipv6:
        blockers.append("firewall_backend_mixed")
    return {"iptables_backend": ipv4, "ip6tables_backend": ipv6, "consistent": not blockers, "status": "ok" if not blockers else "blocked", "blockers": blockers}


def _nat_insertion_analysis(parsed4: dict[str, Any], external_ingress_interfaces: list[dict[str, Any]]) -> dict[str, Any]:
    rules = parsed4.get("rules", []) if isinstance(parsed4.get("rules"), list) else []
    prerouting = [r for r in rules if isinstance(r, dict) and r.get("table") == "nat" and r.get("chain") == "PREROUTING"]
    docker = [r for r in rules if isinstance(r, dict) and r.get("table") == "nat" and r.get("chain") == "DOCKER"]
    docker_jump = any((r.get("jump_target") == "DOCKER") and (r.get("match", {}).get("addrtype_dst_type") == "LOCAL") for r in prerouting if isinstance(r.get("match"), dict))
    future_ports = {20001, 20101}
    consumed = []
    for r in docker:
        match = r.get("match", {}) if isinstance(r.get("match"), dict) else {}
        if match.get("destination_port") in future_ports and r.get("jump_target") != "RETURN":
            consumed.append({"rule_index": r.get("rule_index"), "port": match.get("destination_port")})
    reachable = docker_jump and not consumed
    # This collector only proves the existing Docker jump shape and absence of
    # exact future-port consumption. It does not install or execute an MPF NAT
    # rule, so the insertion point remains review-only, not verified.
    return {
        "proposed_nat_parent_chain": "PREROUTING",
        "proposed_nat_insertion_mode": "append_after_existing_docker_jump",
        "nat_insertion_point_reachable": reachable,
        "nat_insertion_point_verified": False,
        "nat_binding_ready": False,
        "future_public_ports": sorted(future_ports),
        "docker_prerouting_addrtype_local_jump": docker_jump,
        "docker_future_port_consumers": consumed,
        "external_ingress_interfaces": [i.get("ifname") for i in external_ingress_interfaces],
    }
