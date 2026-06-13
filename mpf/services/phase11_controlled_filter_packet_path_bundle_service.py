"""Evidence bundle writer and pure offline verifier."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.domain.phase11_controlled_filter_packet_path import EXPECTED_VERSION, INVALID, MANIFESTED_EVIDENCE_FILES, REQUIRED_BUNDLE_FILES


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_packet_path_bundle(bundle: dict[str, Any], output_dir: Path | str) -> dict[str, Any]:
    out = Path(output_dir)
    _create_safe_dir(out)
    files: dict[str, bytes] = {
        "evidence.json": canonical_json_bytes(bundle["evidence"]),
        "decision.json": canonical_json_bytes(bundle["decision"]),
        "sanitized-backend-target.json": canonical_json_bytes(bundle["sanitized_backend_target"]),
        "sanitized-docker-network.json": canonical_json_bytes(bundle["sanitized_docker_network"]),
        "iptables-save.txt": str(bundle["iptables_save_text"]).encode("utf-8"),
        "ip6tables-save.txt": str(bundle["ip6tables_save_text"]).encode("utf-8"),
        "parsed-firewall.json": canonical_json_bytes(bundle["parsed_firewall"]),
        "host-network-topology.json": canonical_json_bytes(bundle["host_topology"]),
        "packet-path-graph.json": canonical_json_bytes(bundle["graph"]),
        "command-results.json": canonical_json_bytes(bundle["command_results"]),
    }
    manifest_files = {name: {"size": len(data), "sha256": sha256_bytes(data)} for name, data in sorted(files.items())}
    backend_target = bundle["evidence"].get("backend_target") if isinstance(bundle.get("evidence"), dict) else None
    manifest = {
        "manifest_version": 1,
        "repository_version": __version__,
        "expected_version": EXPECTED_VERSION,
        "hostname": bundle["evidence"].get("hostname"),
        "collection_id": bundle["evidence"].get("collection_id"),
        "collection_timestamp": bundle["evidence"].get("collected_at"),
        "backend_target_fingerprint": backend_target.get("target_fingerprint") if isinstance(backend_target, dict) else None,
        "ipv4_ruleset_hash": bundle["parsed_firewall"].get("ipv4", {}).get("source_sha256"),
        "ipv6_ruleset_hash": bundle["parsed_firewall"].get("ipv6", {}).get("source_sha256"),
        "phase_state_hash": bundle["evidence"].get("phase_status_sha256"),
        "decision_hash": manifest_files["decision.json"]["sha256"],
        "graph_hash": manifest_files["packet-path-graph.json"]["sha256"],
        "final_decision": bundle["decision"].get("final_decision"),
        "files": manifest_files,
    }
    files["manifest.json"] = canonical_json_bytes(manifest)
    manifest_sha = sha256_bytes(files["manifest.json"])
    files["manifest.sha256"] = f"{manifest_sha}  manifest.json\n".encode("utf-8")
    for name, data in files.items():
        _atomic_write(out / name, data)
    return {"output_dir": str(out), "manifest_sha256": manifest_sha, "manifest": manifest, "final_decision": manifest["final_decision"], "mutation_performed": False}


def verify_packet_path_bundle(evidence_dir: Path | str) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        root = Path(evidence_dir)
        if not root.is_dir() or root.is_symlink():
            return _invalid(["evidence_dir_not_safe_directory"])
        entries = list(root.iterdir())
        names = sorted(p.name for p in entries)
        if sorted(REQUIRED_BUNDLE_FILES) != names:
            blockers.extend([f"unexpected_file:{x}" for x in sorted(set(names) - set(REQUIRED_BUNDLE_FILES))])
            blockers.extend([f"missing_file:{x}" for x in sorted(set(REQUIRED_BUNDLE_FILES) - set(names))])
        for p in entries:
            if p.is_symlink() or not p.is_file():
                blockers.append(f"unsafe_bundle_entry:{p.name}")
        if blockers:
            return _invalid(blockers)
        raw = {name: (root / name).read_bytes() for name in REQUIRED_BUNDLE_FILES}
    except OSError as exc:
        return _invalid([f"bundle_read_failed:{type(exc).__name__}"])

    try:
        manifest_sha_line = raw["manifest.sha256"].decode("utf-8").strip().split()[0]
    except (UnicodeDecodeError, IndexError):
        return _invalid(["manifest_sha256_file_invalid"])
    if manifest_sha_line != sha256_bytes(raw["manifest.json"]):
        blockers.append("manifest_sha256_mismatch")
    manifest = _load_json(raw["manifest.json"], "manifest", blockers)
    if not isinstance(manifest, dict):
        blockers.append("manifest_schema_invalid")
        return _invalid(blockers)
    files_meta = manifest.get("files")
    if not isinstance(files_meta, dict):
        blockers.append("manifest_files_schema_invalid")
        return _invalid(blockers)
    for name in MANIFESTED_EVIDENCE_FILES:
        meta = files_meta.get(name)
        if not isinstance(meta, dict):
            blockers.append(f"manifest_missing_file:{name}")
            continue
        try:
            recorded_size = int(meta.get("size", -1))
        except (TypeError, ValueError):
            blockers.append(f"file_size_schema_invalid:{name}")
            recorded_size = -1
        if recorded_size != len(raw[name]):
            blockers.append(f"file_size_mismatch:{name}")
        if not isinstance(meta.get("sha256"), str) or meta.get("sha256") != sha256_bytes(raw[name]):
            blockers.append(f"file_hash_mismatch:{name}")

    docs: dict[str, Any] = {}
    for name in ("evidence.json", "decision.json", "sanitized-backend-target.json", "sanitized-docker-network.json", "parsed-firewall.json", "host-network-topology.json", "packet-path-graph.json", "command-results.json"):
        doc = _load_json(raw[name], name.removesuffix(".json").replace("-", "_"), blockers)
        docs[name] = doc
    if blockers:
        return _invalid(blockers)
    if not isinstance(docs["evidence.json"], dict):
        blockers.append("evidence_schema_invalid")
    if not isinstance(docs["decision.json"], dict):
        blockers.append("decision_schema_invalid")
    if not isinstance(docs["sanitized-backend-target.json"], dict):
        blockers.append("backend_target_schema_invalid")
    if not isinstance(docs["sanitized-docker-network.json"], dict):
        blockers.append("docker_network_schema_invalid")
    if not isinstance(docs["host-network-topology.json"], dict):
        blockers.append("host_topology_schema_invalid")
    if not isinstance(docs["packet-path-graph.json"], dict):
        blockers.append("graph_schema_invalid")
    if not isinstance(docs["parsed-firewall.json"], dict):
        blockers.append("parsed_firewall_schema_invalid")
    elif not isinstance(docs["parsed-firewall.json"].get("ipv4"), dict) or not isinstance(docs["parsed-firewall.json"].get("ipv6"), dict):
        blockers.append("parsed_firewall_schema_invalid")
    if not isinstance(docs["command-results.json"], list):
        blockers.append("command_results_not_array")
    if isinstance(docs["evidence.json"], dict) and not isinstance(docs["evidence.json"].get("backend_target"), dict):
        blockers.append("evidence_backend_target_schema_invalid")
    if blockers:
        return _invalid(blockers)

    evidence = docs["evidence.json"]
    decision = docs["decision.json"]
    graph = docs["packet-path-graph.json"]
    parsed = docs["parsed-firewall.json"]
    command_results = docs["command-results.json"]
    if evidence.get("packet_path_schema_version") != "0.1.252":
        _cross_check_manifest(manifest, evidence, decision, graph, parsed, docs, raw, blockers, allow_legacy_version=True)
        _check_commands(command_results, decision, blockers, legacy=True)
        if blockers:
            return _invalid(blockers)
        return {"component": "phase11_controlled_filter_packet_path_bundle_verifier", "repository_version": __version__, "final_decision": decision.get("final_decision"), "bundle_integrity_valid": True, "readiness_eligible": False, "recollection_required": True, "blockers": ["legacy_packet_path_schema_recollection_required"], "mutation_performed": False, "manifest_sha256": manifest_sha_line, "source_repository_version": evidence.get("repository_version")}
    _cross_check_manifest(manifest, evidence, decision, graph, parsed, docs, raw, blockers)
    _check_packet_path_schema(evidence, decision, graph, docs, command_results, blockers)
    _check_commands(command_results, decision, blockers)
    text_scan = b"\n".join(raw[name] for name in REQUIRED_BUNDLE_FILES if name not in {"iptables-save.txt", "ip6tables-save.txt"})
    for forbidden in (b"Config.Env", b'"Env"', b"PASSWORD", b"TOKEN", b"SECRET", b"HostConfig"):
        if forbidden in text_scan:
            blockers.append("raw_docker_environment_or_config_leakage")
            break
    if decision.get("mutation_performed") is not False or evidence.get("mutation_performed") is not False or graph.get("mutation_performed") is not False:
        blockers.append("mutation_performed_not_false")
    if blockers:
        return _invalid(blockers)
    return {"component": "phase11_controlled_filter_packet_path_bundle_verifier", "repository_version": __version__, "final_decision": decision.get("final_decision"), "bundle_integrity_valid": True, "readiness_eligible": True, "recollection_required": False, "blockers": [], "mutation_performed": False, "manifest_sha256": manifest_sha_line, "source_repository_version": evidence.get("repository_version")}



def _check_packet_path_schema(evidence: dict[str, Any], decision: dict[str, Any], graph: dict[str, Any], docs: dict[str, Any], command_results: list[Any], blockers: list[str]) -> None:
    final = str(decision.get("final_decision") or "")
    ready = final.startswith("READY")
    scenarios = graph.get("packet_scenarios")
    results = graph.get("scenario_results")
    if not isinstance(scenarios, list):
        blockers.append("packet_scenarios_schema_invalid")
        return
    if ready and not scenarios:
        blockers.append("ready_packet_scenarios_empty")
    if not isinstance(results, list):
        blockers.append("scenario_results_schema_invalid")
        if ready:
            blockers.append("ready_scenario_results_missing")
        return
    if ready and not results:
        blockers.append("ready_scenario_results_empty")
    scenario_ids = [s.get("scenario_id") for s in scenarios if isinstance(s, dict)]
    result_ids = [r.get("scenario_id") for r in results if isinstance(r, dict)]
    if len(scenario_ids) != len(set(scenario_ids)):
        blockers.append("duplicate_scenario_id")
    if len(result_ids) != len(set(result_ids)):
        blockers.append("duplicate_scenario_result_id")
    if set(scenario_ids) != set(result_ids):
        blockers.append("scenario_result_id_mismatch")
    required_states = {"NEW", "ESTABLISHED"}
    ingress = {str(s.get("ingress_interface")) for s in scenarios if isinstance(s, dict) and s.get("ingress_interface")}
    if ready and not ingress:
        blockers.append("ready_scenario_ingress_missing")
    for ifname in ingress:
        states = {str(s.get("conntrack_state")) for s in scenarios if isinstance(s, dict) and str(s.get("ingress_interface")) == ifname}
        if states != required_states:
            blockers.append(f"missing_required_scenario:{ifname}")
    command_by_id = {str(c.get("command_id")): c for c in command_results if isinstance(c, dict)}
    topology = evidence.get("host_topology", {}) if isinstance(evidence.get("host_topology"), dict) else {}
    network = evidence.get("docker_network", {}) if isinstance(evidence.get("docker_network"), dict) else {}
    backend = evidence.get("backend_target", {}) if isinstance(evidence.get("backend_target"), dict) else {}
    bridge = str(network.get("bridge_name") or "")
    route_map = topology.get("route_get_backend_by_ingress", {}) if isinstance(topology.get("route_get_backend_by_ingress"), dict) else {}
    route_refs = topology.get("route_get_backend_by_ingress_refs", {}) if isinstance(topology.get("route_get_backend_by_ingress_refs"), dict) else {}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            blockers.append("scenario_schema_invalid")
            continue
        ifname = str(scenario.get("ingress_interface") or "")
        ref = str(scenario.get("route_evidence_ref") or "")
        if ifname not in route_map:
            blockers.append(f"scenario_route_missing:{ifname}")
            continue
        rows = route_map.get(ifname)
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            blockers.append(f"scenario_route_ambiguous:{ifname}")
        elif rows[0].get("dev") != bridge:
            blockers.append(f"scenario_route_bridge_mismatch:{ifname}")
        cmd_id = str((route_refs.get(ifname) or {}).get("command_id") or f"ip_route_get_backend_ingress:{ifname}")
        cmd = command_by_id.get(cmd_id)
        if cmd is None:
            blockers.append(f"scenario_route_command_missing:{ifname}")
        elif cmd.get("return_code") != 0 or cmd.get("output_truncated") is True:
            blockers.append(f"scenario_route_command_failed:{ifname}")
        else:
            stdout_rows = _parse_stdout_json_array(cmd, cmd_id, blockers)
            if stdout_rows != rows:
                blockers.append(f"scenario_route_projection_stdout_mismatch:{ifname}")
            if len(stdout_rows) != 1 or not isinstance(stdout_rows[0], dict) or stdout_rows[0].get("dev") != bridge:
                blockers.append(f"scenario_route_command_bridge_mismatch:{ifname}")
        expected_ref = str((route_refs.get(ifname) or {}).get("evidence_ref") or f"command-results.json:{cmd_id}")
        if ref and ifname not in ref and ref != expected_ref:
            blockers.append(f"scenario_route_ref_mismatch:{ifname}")
    for item in results:
        if isinstance(item, dict) and ready and item.get("ready") is not True:
            blockers.append("ready_decision_with_unresolved_scenario")
    evidence_rows = topology.get("backend_bridge_membership_evidence")
    if backend.get("mac_address") and topology.get("backend_bridge_membership_verified") is True and not evidence_rows:
        blockers.append("backend_membership_evidence_missing")
    if isinstance(evidence_rows, list):
        for row in evidence_rows:
            if not isinstance(row, dict):
                blockers.append("backend_membership_evidence_schema_invalid")
                continue
            method = str(row.get("method") or "")
            if method == "fdb_mac_to_host_veth":
                fdb_cmd = command_by_id.get("bridge_fdb_backend")
                link_cmd = command_by_id.get("ip_link_master_bridge")
                if fdb_cmd is None or link_cmd is None:
                    blockers.append("fdb_membership_required_commands_missing")
                if row.get("mac_address") != backend.get("mac_address") or row.get("bridge") != bridge:
                    blockers.append("fdb_membership_backend_binding_mismatch")
                if fdb_cmd is not None and link_cmd is not None:
                    fdb_rows = _parse_stdout_json_array(fdb_cmd, "bridge_fdb_backend", blockers)
                    link_rows = _parse_stdout_json_array(link_cmd, "ip_link_master_bridge", blockers)
                    host_ifname = str(row.get("host_ifname") or "")
                    mac = _norm_mac(backend.get("mac_address"))
                    fdb_match = any(isinstance(x, dict) and _norm_mac(x.get("mac") or x.get("lladdr")) == mac and str(x.get("dev") or x.get("ifname") or "") == host_ifname for x in fdb_rows)
                    link_match = any(isinstance(x, dict) and x.get("ifname") == host_ifname and x.get("master") == bridge for x in link_rows)
                    if not fdb_match or not link_match:
                        blockers.append("fdb_membership_source_record_mismatch")
            if method == "netns_eth0_iflink_to_host_veth":
                if "nsenter_backend_eth0_link" not in command_by_id or "nsenter_backend_eth0_address" not in command_by_id:
                    blockers.append("netns_membership_required_commands_missing")
                if row.get("mac_address") != backend.get("mac_address") or row.get("bridge") != bridge:
                    blockers.append("netns_membership_backend_binding_mismatch")
    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    node_ids = [n.get("id") for n in nodes if isinstance(n, dict)]
    if len(node_ids) != len(set(node_ids)):
        blockers.append("duplicate_graph_node_id")


def _parse_stdout_json_array(command: dict[str, Any], command_id: str, blockers: list[str]) -> list[Any]:
    stdout = command.get("stdout")
    if not isinstance(stdout, str) or not stdout.strip():
        blockers.append(f"command_stdout_missing:{command_id}")
        return []
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        blockers.append(f"command_stdout_json_invalid:{command_id}")
        return []
    if not isinstance(parsed, list):
        blockers.append(f"command_stdout_json_not_array:{command_id}")
        return []
    recorded_hash = command.get("stdout_sha256")
    if not isinstance(recorded_hash, str) or len(recorded_hash) != 64 or any(ch not in "0123456789abcdef" for ch in recorded_hash):
        blockers.append(f"command_stdout_hash_invalid:{command_id}")
    elif recorded_hash == "0" * 64:
        blockers.append(f"command_stdout_hash_zero:{command_id}")
    elif recorded_hash != sha256_bytes(stdout.encode()):
        blockers.append(f"command_stdout_hash_mismatch:{command_id}")
    return parsed


def _norm_mac(value: Any) -> str:
    return str(value or "").lower()

def _load_json(raw: bytes, label: str, blockers: list[str]) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        blockers.append(f"{label}_json_unicode_invalid")
    except json.JSONDecodeError:
        blockers.append(f"{label}_json_invalid")
    except (TypeError, ValueError):
        blockers.append(f"{label}_json_invalid")
    return None


def _cross_check_manifest(manifest: dict[str, Any], evidence: dict[str, Any], decision: dict[str, Any], graph: dict[str, Any], parsed: dict[str, Any], docs: dict[str, Any], raw: dict[str, bytes], blockers: list[str], *, allow_legacy_version: bool = False) -> None:
    backend_target = evidence.get("backend_target")
    if not isinstance(backend_target, dict):
        blockers.append("evidence_backend_target_schema_invalid")
        backend_target = {}
    pairs = [
        ("collection_id", evidence.get("collection_id"), "manifest_collection_id_mismatch"),
        ("hostname", evidence.get("hostname"), "manifest_hostname_mismatch"),
        ("collection_timestamp", evidence.get("collected_at"), "manifest_collection_timestamp_mismatch"),
        ("backend_target_fingerprint", backend_target.get("target_fingerprint"), "manifest_target_fingerprint_mismatch"),
        ("phase_state_hash", evidence.get("phase_status_sha256"), "manifest_phase_hash_mismatch"),
        ("final_decision", decision.get("final_decision"), "manifest_final_decision_mismatch"),
    ]
    source_bundle_compat = evidence.get("packet_path_schema_version") == EXPECTED_VERSION
    if not allow_legacy_version:
        if source_bundle_compat:
            manifest_repository_versions = {__version__, EXPECTED_VERSION}
            evidence_repository_versions = {__version__, EXPECTED_VERSION}
            pairs.append(("expected_version", EXPECTED_VERSION, "manifest_expected_version_mismatch"))
        else:
            manifest_repository_versions = {__version__}
            evidence_repository_versions = {__version__}
            pairs.extend([
                ("expected_version", EXPECTED_VERSION, "manifest_expected_version_mismatch"),
            ])
        if manifest.get("repository_version") not in manifest_repository_versions:
            blockers.append("manifest_repository_version_mismatch")
    for key, expected, blocker in pairs:
        if manifest.get(key) != expected:
            blockers.append(blocker)
    if not allow_legacy_version and evidence.get("repository_version") not in evidence_repository_versions:
        blockers.append("evidence_repository_version_mismatch")
    if not allow_legacy_version and evidence.get("expected_version") != EXPECTED_VERSION:
        blockers.append("evidence_expected_version_mismatch")
    for name in ("decision.json", "packet-path-graph.json", "parsed-firewall.json", "sanitized-backend-target.json", "sanitized-docker-network.json", "host-network-topology.json"):
        doc = docs.get(name)
        if not isinstance(doc, dict):
            continue
        if doc.get("collection_id", evidence.get("collection_id")) != evidence.get("collection_id"):
            blockers.append(f"collection_id_mismatch:{name}")
        if doc.get("hostname", evidence.get("hostname")) != evidence.get("hostname"):
            blockers.append(f"hostname_mismatch:{name}")
    if manifest.get("decision_hash") != sha256_bytes(raw["decision.json"]):
        blockers.append("decision_hash_mismatch")
    if manifest.get("graph_hash") != sha256_bytes(raw["packet-path-graph.json"]):
        blockers.append("graph_hash_mismatch")
    if manifest.get("ipv4_ruleset_hash") != parsed.get("ipv4", {}).get("source_sha256"):
        blockers.append("ipv4_ruleset_hash_mismatch")
    if manifest.get("ipv6_ruleset_hash") != parsed.get("ipv6", {}).get("source_sha256"):
        blockers.append("ipv6_ruleset_hash_mismatch")
    if parsed.get("ipv4", {}).get("source_sha256") != sha256_bytes(raw["iptables-save.txt"]):
        blockers.append("ipv4_raw_ruleset_hash_mismatch")
    if parsed.get("ipv6", {}).get("source_sha256") != sha256_bytes(raw["ip6tables-save.txt"]):
        blockers.append("ipv6_raw_ruleset_hash_mismatch")


def _check_commands(command_results: list[Any], decision: dict[str, Any], blockers: list[str], *, legacy: bool = False) -> None:
    required = {"hostname", "uname_kernel", "iptables_save", "ip6tables_save", "iptables_version", "ip6tables_version", "docker_inspect_backend", "docker_network_inspect", "docker_ps_compose", "ip_address", "ip_link", "ip_route_all", "ip_rule", "bridge_link", "ss_listeners", "ss_backend_listener"}
    ready_required = {"ip_route_get_backend"} if legacy else {"ip_route_get_backend", "bridge_fdb_backend", "ip_link_master_bridge"}
    ids: list[str] = []
    for result in command_results:
        if not isinstance(result, dict):
            blockers.append("command_result_schema_invalid")
            continue
        cid = str(result.get("command_id"))
        ids.append(cid)
        if result.get("mutation_performed") is not False:
            blockers.append(f"command_mutation_not_false:{cid}")
        if not isinstance(result.get("return_code"), int) or not isinstance(result.get("output_truncated"), bool) or not isinstance(result.get("mutation_performed"), bool):
            blockers.append(f"command_result_field_schema_invalid:{cid}")
        if decision.get("final_decision") and str(decision.get("final_decision")).startswith("READY"):
            if result.get("return_code") != 0:
                blockers.append(f"ready_with_failed_command:{cid}")
            if result.get("output_truncated") is True:
                blockers.append(f"ready_with_truncated_command:{cid}")
    if len(ids) != len(set(ids)):
        blockers.append("command_ids_not_unique")
    missing = sorted(required - set(ids))
    blockers.extend(f"required_command_missing:{item}" for item in missing)
    if decision.get("final_decision") and str(decision.get("final_decision")).startswith("READY"):
        missing_ready = sorted(ready_required - set(ids))
        blockers.extend(f"ready_required_command_missing:{item}" for item in missing_ready)


def _create_safe_dir(path: Path) -> None:
    _reject_symlink_components(path.parent)
    if path.exists() or path.is_symlink():
        raise FileExistsError(str(path))
    path.mkdir(mode=0o700)


def _reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor) if path.is_absolute() else Path(".")
    parts = path.parts[1:] if path.is_absolute() else path.parts
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink_parent_forbidden:{current}")
    path.resolve(strict=True)


def _atomic_write(path: Path, data: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(str(path))
    tmp = path.with_name(f".{path.name}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if path.exists() or path.is_symlink():
        try:
            tmp.unlink()
        finally:
            raise FileExistsError(str(path))
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def _invalid(blockers: list[str]) -> dict[str, Any]:
    return {"component": "phase11_controlled_filter_packet_path_bundle_verifier", "repository_version": __version__, "final_decision": INVALID, "bundle_integrity_valid": False, "blockers": sorted(set(blockers)), "mutation_performed": False}
