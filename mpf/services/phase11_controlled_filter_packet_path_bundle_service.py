"""Evidence bundle writer and pure offline verifier."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.domain.phase11_controlled_filter_packet_path import INVALID, MANIFESTED_EVIDENCE_FILES, REQUIRED_BUNDLE_FILES


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
    root = Path(evidence_dir)
    blockers: list[str] = []
    if not root.is_dir() or root.is_symlink():
        return _invalid(["evidence_dir_not_safe_directory"])
    names = sorted(p.name for p in root.iterdir())
    if sorted(REQUIRED_BUNDLE_FILES) != names:
        extra = sorted(set(names) - set(REQUIRED_BUNDLE_FILES))
        missing = sorted(set(REQUIRED_BUNDLE_FILES) - set(names))
        blockers.extend([f"unexpected_file:{x}" for x in extra])
        blockers.extend([f"missing_file:{x}" for x in missing])
    for p in root.iterdir():
        if p.is_symlink() or not p.is_file():
            blockers.append(f"unsafe_bundle_entry:{p.name}")
    if blockers:
        return _invalid(blockers)
    raw: dict[str, bytes] = {name: (root / name).read_bytes() for name in REQUIRED_BUNDLE_FILES}
    manifest_sha_line = raw["manifest.sha256"].decode("utf-8", errors="replace").strip().split()[0]
    if manifest_sha_line != sha256_bytes(raw["manifest.json"]):
        blockers.append("manifest_sha256_mismatch")
    manifest = json.loads(raw["manifest.json"])
    for name in MANIFESTED_EVIDENCE_FILES:
        meta = manifest.get("files", {}).get(name)
        if not isinstance(meta, dict):
            blockers.append(f"manifest_missing_file:{name}")
            continue
        if int(meta.get("size", -1)) != len(raw[name]):
            blockers.append(f"file_size_mismatch:{name}")
        if meta.get("sha256") != sha256_bytes(raw[name]):
            blockers.append(f"file_hash_mismatch:{name}")
    docs = {name: json.loads(raw[name]) for name in ("evidence.json", "decision.json", "sanitized-backend-target.json", "sanitized-docker-network.json", "parsed-firewall.json", "host-network-topology.json", "packet-path-graph.json", "command-results.json")}
    collection_id = docs["evidence.json"].get("collection_id")
    hostname = docs["evidence.json"].get("hostname")
    for name, doc in docs.items():
        if isinstance(doc, dict):
            if doc.get("collection_id", collection_id) != collection_id:
                blockers.append(f"collection_id_mismatch:{name}")
            if doc.get("hostname", hostname) != hostname:
                blockers.append(f"hostname_mismatch:{name}")
    if manifest.get("repository_version") != __version__ or docs["evidence.json"].get("repository_version") != __version__:
        blockers.append("version_mismatch")
    if manifest.get("backend_target_fingerprint") != docs["evidence.json"].get("backend_target", {}).get("target_fingerprint"):
        blockers.append("target_fingerprint_mismatch")
    if manifest.get("decision_hash") != sha256_bytes(raw["decision.json"]):
        blockers.append("decision_hash_mismatch")
    if manifest.get("graph_hash") != sha256_bytes(raw["packet-path-graph.json"]):
        blockers.append("graph_hash_mismatch")
    text_scan = b"\n".join(raw[name] for name in REQUIRED_BUNDLE_FILES if name not in {"iptables-save.txt", "ip6tables-save.txt"})
    for forbidden in (b"Config.Env", b'"Env"', b"PASSWORD", b"TOKEN", b"SECRET", b"HostConfig"):
        if forbidden in text_scan:
            blockers.append("raw_docker_environment_or_config_leakage")
            break
    decision = docs["decision.json"]
    command_results = docs["command-results.json"]
    if decision.get("mutation_performed") is not False:
        blockers.append("decision_mutation_not_false")
    for result in command_results if isinstance(command_results, list) else []:
        if result.get("mutation_performed") is not False:
            blockers.append(f"command_mutation_not_false:{result.get('command_id')}")
        if decision.get("final_decision") and str(decision.get("final_decision")).startswith("READY"):
            if result.get("return_code") != 0:
                blockers.append(f"ready_with_failed_command:{result.get('command_id')}")
            if result.get("output_truncated") is True:
                blockers.append(f"ready_with_truncated_command:{result.get('command_id')}")
    if blockers:
        return _invalid(blockers)
    return {"component": "phase11_controlled_filter_packet_path_bundle_verifier", "repository_version": __version__, "final_decision": decision.get("final_decision"), "bundle_integrity_valid": True, "blockers": [], "mutation_performed": False, "manifest_sha256": manifest_sha_line}


def _create_safe_dir(path: Path) -> None:
    parent = path.parent.resolve(strict=True)
    if any(part.is_symlink() for part in [parent, *parent.parents]):
        raise ValueError("symlink_parent_forbidden")
    if path.exists():
        raise FileExistsError(str(path))
    path.mkdir(mode=0o700)


def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def _invalid(blockers: list[str]) -> dict[str, Any]:
    return {"component": "phase11_controlled_filter_packet_path_bundle_verifier", "repository_version": __version__, "final_decision": INVALID, "bundle_integrity_valid": False, "blockers": sorted(set(blockers)), "mutation_performed": False}
