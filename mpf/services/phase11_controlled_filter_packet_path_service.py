"""Read-only Phase 11 controlled filter packet-path evidence collector."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
import uuid
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
        try:
            ip = ipaddress.ip_address(backend_ip)
            if not isinstance(ip, ipaddress.IPv4Address) or not ip.is_private or ip.is_loopback or backend_ip == "172.18.0.3":
                backend["status"] = "blocked"
                backend.setdefault("blockers", []).append("backend_ipv4_not_valid_dynamic_private_non_loopback")
        except ValueError:
            backend["status"] = "blocked"
            backend.setdefault("blockers", []).append("backend_ipv4_invalid")
    if backend.get("status") == "ok" and backend_ip:
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
    backend_bridge_membership_verified = _backend_bridge_membership_verified(bridge_json, network)
    host_topology = {
        "collection_id": collection_id,
        "hostname": hostname,
        "host_addresses": _host_addresses(ip_addr_json),
        "links": ip_link_json,
        "routes": ip_route_json,
        "policy_rules": ip_rule_json,
        "route_get_backend": route_get_json,
        "bridge_links": bridge_json,
        "backend_bridge_membership_verified": backend_bridge_membership_verified,
        "ip_forward": _read_proc_value("/proc/sys/net/ipv4/ip_forward"),
        "bridge_nf_call_iptables": _read_proc_value("/proc/sys/net/bridge/bridge-nf-call-iptables", optional=True),
        "bridge_nf_call_ip6tables": _read_proc_value("/proc/sys/net/bridge/bridge-nf-call-ip6tables", optional=True),
        "route_localnet": _route_localnet_values(),
        "listening_sockets": _stdout(ss).splitlines(),
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


def _backend_bridge_membership_verified(bridge_links: list[Any], network: dict[str, Any]) -> bool:
    if not bridge_links:
        return False
    bridge = str(network.get("bridge_name") or "")
    connected = network.get("connected_allowlisted_mpf_containers", [])
    backend_rows = [item for item in connected if isinstance(item, dict) and item.get("name") == BACKEND_CONTAINER]
    if not bridge or not backend_rows:
        return False
    # bridge -json link output varies by iproute2 version. Require at least one
    # link record whose master/ifname references the verified bridge; this proves
    # host bridge membership evidence is present rather than synthesized.
    for item in bridge_links:
        if not isinstance(item, dict):
            continue
        if item.get("master") == bridge or item.get("ifname") == bridge or item.get("link") == bridge:
            return True
    return False


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
    health = state.get("Health", {}).get("Status") if isinstance(state.get("Health"), dict) else None
    if labels.get("com.docker.compose.project") != COMPOSE_PROJECT:
        blockers.append("backend_container_compose_project_mismatch")
    if labels.get("com.docker.compose.service") != COMPOSE_SERVICE:
        blockers.append("backend_container_compose_service_mismatch")
    if not running:
        blockers.append("backend_container_not_running")
    if health is not None and health != "healthy":
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
    fingerprint_input = {"container_name": BACKEND_CONTAINER, "container_id": container.get("Id"), "network_name": DOCKER_NETWORK, "network_id": net.get("NetworkID") or net.get("EndpointID"), "resolved_ipv4": ip, "backend_port": BACKEND_PORT}
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
    if network.get("status") != "ok":
        backend["status"] = "blocked"
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
        row = {"container_id": cid, "name": name, "ipv4_address": str(info.get("IPv4Address") or "").split("/")[0], "raw_ipv4": info.get("IPv4Address")}
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
    if not bridge_name:
        blockers.append("docker_bridge_name_missing")
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
