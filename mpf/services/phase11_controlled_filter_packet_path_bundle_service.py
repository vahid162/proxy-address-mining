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
    manifest = {
        "manifest_version": 1,
        "repository_version": __version__,
        "expected_version": EXPECTED_VERSION,
        "hostname": bundle["evidence"].get("hostname"),
        "collection_id": bundle["evidence"].get("collection_id"),
        "collection_timestamp": bundle["evidence"].get("collected_at"),
        "backend_target_fingerprint": bundle["evidence"].get("backend_target", {}).get("target_fingerprint"),
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
        if int(meta.get("size", -1)) != len(raw[name]):
            blockers.append(f"file_size_mismatch:{name}")
        if meta.get("sha256") != sha256_bytes(raw[name]):
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
    if not isinstance(docs["packet-path-graph.json"], dict):
        blockers.append("graph_schema_invalid")
    if not isinstance(docs["parsed-firewall.json"], dict):
        blockers.append("parsed_firewall_schema_invalid")
    if not isinstance(docs["command-results.json"], list):
        blockers.append("command_results_not_array")
    if blockers:
        return _invalid(blockers)

    evidence = docs["evidence.json"]
    decision = docs["decision.json"]
    graph = docs["packet-path-graph.json"]
    parsed = docs["parsed-firewall.json"]
    command_results = docs["command-results.json"]
    _cross_check_manifest(manifest, evidence, decision, graph, parsed, raw, blockers)
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
    return {"component": "phase11_controlled_filter_packet_path_bundle_verifier", "repository_version": __version__, "final_decision": decision.get("final_decision"), "bundle_integrity_valid": True, "blockers": [], "mutation_performed": False, "manifest_sha256": manifest_sha_line}


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


def _cross_check_manifest(manifest: dict[str, Any], evidence: dict[str, Any], decision: dict[str, Any], graph: dict[str, Any], parsed: dict[str, Any], raw: dict[str, bytes], blockers: list[str]) -> None:
    pairs = [
        ("repository_version", __version__, "manifest_repository_version_mismatch"),
        ("expected_version", EXPECTED_VERSION, "manifest_expected_version_mismatch"),
        ("collection_id", evidence.get("collection_id"), "manifest_collection_id_mismatch"),
        ("hostname", evidence.get("hostname"), "manifest_hostname_mismatch"),
        ("collection_timestamp", evidence.get("collected_at"), "manifest_collection_timestamp_mismatch"),
        ("backend_target_fingerprint", evidence.get("backend_target", {}).get("target_fingerprint"), "manifest_target_fingerprint_mismatch"),
        ("phase_state_hash", evidence.get("phase_status_sha256"), "manifest_phase_hash_mismatch"),
        ("final_decision", decision.get("final_decision"), "manifest_final_decision_mismatch"),
    ]
    for key, expected, blocker in pairs:
        if manifest.get(key) != expected:
            blockers.append(blocker)
    if evidence.get("repository_version") != __version__:
        blockers.append("evidence_repository_version_mismatch")
    if evidence.get("expected_version") != EXPECTED_VERSION:
        blockers.append("evidence_expected_version_mismatch")
    for name, doc in {"decision.json": decision, "packet-path-graph.json": graph, "parsed-firewall.json": parsed}.items():
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


def _check_commands(command_results: list[Any], decision: dict[str, Any], blockers: list[str]) -> None:
    required = {"hostname", "uname_kernel", "iptables_save", "ip6tables_save", "iptables_version", "ip6tables_version", "docker_inspect_backend", "docker_network_inspect", "docker_ps_compose", "ip_address", "ip_link", "ip_route_all", "ip_rule", "bridge_link", "ss_listeners", "ss_backend_listener"}
    ids: list[str] = []
    for result in command_results:
        if not isinstance(result, dict):
            blockers.append("command_result_schema_invalid")
            continue
        cid = str(result.get("command_id"))
        ids.append(cid)
        if result.get("mutation_performed") is not False:
            blockers.append(f"command_mutation_not_false:{cid}")
        if decision.get("final_decision") and str(decision.get("final_decision")).startswith("READY"):
            if result.get("return_code") != 0:
                blockers.append(f"ready_with_failed_command:{cid}")
            if result.get("output_truncated") is True:
                blockers.append(f"ready_with_truncated_command:{cid}")
    if len(ids) != len(set(ids)):
        blockers.append("command_ids_not_unique")
    missing = sorted(required - set(ids))
    blockers.extend(f"required_command_missing:{item}" for item in missing)


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
