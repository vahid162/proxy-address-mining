from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

EXPECTED = {
    "customer_key": "limited-btc-001",
    "lane": "btc",
    "public_port": 20101,
    "backend_target": "172.18.0.3:60010",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path, missing: str, invalid: str, blockers: list[str]) -> dict[str, object] | None:
    if not path.exists() or not path.is_file():
        blockers.append(missing)
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        blockers.append(invalid)
        return None
    if not isinstance(obj, dict):
        blockers.append(invalid)
        return None
    return obj


def build_phase11_single_customer_visibility_bundle_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []

    expected_version = str(kwargs.get("expected_version", __version__))
    candidate_customer_key = str(kwargs.get("candidate_customer_key", EXPECTED["customer_key"]))
    candidate_lane = str(kwargs.get("candidate_lane", EXPECTED["lane"]))
    candidate_public_port = int(kwargs.get("candidate_public_port", EXPECTED["public_port"]))
    candidate_backend_target = str(kwargs.get("candidate_backend_target", EXPECTED["backend_target"]))

    if (candidate_customer_key, candidate_lane, candidate_public_port, candidate_backend_target) != (
        EXPECTED["customer_key"], EXPECTED["lane"], EXPECTED["public_port"], EXPECTED["backend_target"]
    ):
        blockers.append("candidate_scope_mismatch")

    runtime_path = Path(str(kwargs.get("runtime_path_evidence_json", "")))
    runtime = _load_json(runtime_path, "runtime_path_evidence_missing", "runtime_path_evidence_invalid", blockers)
    runtime_sha = kwargs.get("runtime_path_evidence_json_sha256")
    if runtime is not None and runtime_sha is not None and _sha256(runtime_path) != str(runtime_sha):
        blockers.append("runtime_path_evidence_hash_mismatch")

    stratum_path = Path(str(kwargs.get("stratum_transcript_evidence_json", "")))
    stratum = _load_json(stratum_path, "stratum_transcript_evidence_missing", "stratum_transcript_evidence_invalid", blockers)
    stratum_sha = kwargs.get("stratum_transcript_evidence_json_sha256")
    if stratum is not None and stratum_sha is not None and _sha256(stratum_path) != str(stratum_sha):
        blockers.append("stratum_transcript_evidence_hash_mismatch")

    if runtime is not None:
        if runtime.get("final_decision") != "PHASE11_SINGLE_CUSTOMER_RUNTIME_PATH_EVIDENCE_READY" or runtime.get("runtime_path_evidence_ready") is not True:
            blockers.append("runtime_path_evidence_not_ready")
        if runtime.get("post_apply_evidence_ready") is not True or runtime.get("controlled_apply_recorded") is not True:
            blockers.append("runtime_path_evidence_not_ready")
        if (
            runtime.get("candidate_customer_key") != EXPECTED["customer_key"]
            or runtime.get("candidate_lane") != EXPECTED["lane"]
            or runtime.get("candidate_public_port") != EXPECTED["public_port"]
            or runtime.get("candidate_backend_target") != EXPECTED["backend_target"]
        ):
            blockers.append("runtime_path_evidence_scope_mismatch")
        for flag in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
            expected = False
            if runtime.get(flag) is not expected:
                blockers.append("runtime_path_evidence_safety_boundary_open")
                break

    if stratum is not None:
        if stratum.get("final_decision") != "PHASE11_SINGLE_CUSTOMER_STRATUM_TRANSCRIPT_EVIDENCE_READY" or stratum.get("stratum_transcript_ready") is not True:
            blockers.append("stratum_transcript_evidence_not_ready")
        if (
            stratum.get("candidate_customer_key") != EXPECTED["customer_key"]
            or stratum.get("candidate_lane") != EXPECTED["lane"]
            or stratum.get("candidate_public_port") != EXPECTED["public_port"]
        ):
            blockers.append("stratum_transcript_evidence_scope_mismatch")
        backend = stratum.get("candidate_backend_target")
        if backend not in (None, EXPECTED["backend_target"]):
            blockers.append("stratum_transcript_evidence_scope_mismatch")
        for flag in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
            if stratum.get(flag) is not False:
                blockers.append("stratum_transcript_evidence_safety_boundary_open")
                break

    ready = len(blockers) == 0
    return {
        "component": "phase11_single_customer_visibility_bundle",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": candidate_customer_key,
        "candidate_lane": candidate_lane,
        "candidate_public_port": candidate_public_port,
        "candidate_backend_target": candidate_backend_target,
        "runtime_path_evidence_link": runtime.get("final_decision") if isinstance(runtime, dict) else None,
        "stratum_transcript_link": stratum.get("final_decision") if isinstance(stratum, dict) else None,
        "visibility_bundle_ready": ready,
        "usage_visibility_ready": ready,
        "reject_session_ip_worker_visibility_ready": ready,
        "post_apply_firewall_artifact_visibility_ready": bool(isinstance(runtime, dict) and runtime.get("post_apply_evidence_ready") is True),
        "rollback_readiness_reference_ready": True,
        "abuse_1h_coverage_ready": False,
        "restart_container_order_ready": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
        "next_required_step": "phase11e_abuse_restart_acceptance_pr" if ready else "none",
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "final_decision": "PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY" if ready else "BLOCKED",
    }
