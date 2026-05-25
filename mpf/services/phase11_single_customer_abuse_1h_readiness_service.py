from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

EXPECTED = {"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101, "backend_target": "172.18.0.3:60010"}
ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS = {"0.1.218", __version__}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, miss: str, invalid: str, blockers: list[str]) -> dict[str, object] | None:
    if not path.exists() or not path.is_file():
        blockers.append(miss)
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


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def build_phase11_single_customer_abuse_1h_readiness_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = str(kwargs.get("expected_version", __version__))

    for c in [
        "operator_confirmed", "i_understand_abuse_readiness_only", "i_understand_no_abuse_automation_enable",
        "i_understand_no_hard_block_automation", "i_understand_no_production_traffic_acceptance",
        "i_understand_no_miner_traffic_acceptance", "i_understand_no_db_activation",
    ]:
        if kwargs.get(c) is not True:
            blockers.append(f"missing_confirmation:{c}")

    vis_path = Path(str(kwargs.get("visibility_bundle_json", "")))
    vis = _load(vis_path, "visibility_bundle_missing", "visibility_bundle_invalid", blockers)
    vis_sha = kwargs.get("visibility_bundle_json_sha256")
    if vis is not None and vis_sha is not None and _sha(vis_path) != str(vis_sha):
        blockers.append("visibility_bundle_hash_mismatch")

    source_visibility_bundle_version = vis.get("expected_version") if isinstance(vis, dict) else None
    source_visibility_bundle_repository_version = vis.get("repository_version") if isinstance(vis, dict) else None

    if vis is not None:
        if vis.get("final_decision") != "PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY" or vis.get("visibility_bundle_ready") is not True:
            blockers.append("visibility_bundle_not_ready")
        for k, v in [("candidate_customer_key", EXPECTED["customer_key"]), ("candidate_lane", EXPECTED["lane"]), ("candidate_public_port", EXPECTED["public_port"]), ("candidate_backend_target", EXPECTED["backend_target"])]:
            if vis.get(k) != v:
                blockers.append("visibility_bundle_scope_mismatch")
        for f in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
            if vis.get(f) is not False:
                blockers.append("visibility_bundle_safety_boundary_open")
                break
        if vis.get("expected_version") != "0.1.218":
            blockers.append("unsupported_source_visibility_bundle_version")
        if str(vis.get("repository_version")) not in ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS:
            blockers.append("unsupported_source_visibility_bundle_repository_version")

    abuse_path_obj = kwargs.get("abuse_evidence_json")
    abuse = None
    if abuse_path_obj is None:
        blockers.append("missing_abuse_1h_runtime_coverage_evidence")
    else:
        abuse_path = Path(str(abuse_path_obj))
        abuse = _load(abuse_path, "abuse_evidence_missing", "abuse_evidence_invalid", blockers)
        abuse_sha = kwargs.get("abuse_evidence_json_sha256")
        if abuse is not None and abuse_sha is not None and _sha(abuse_path) != str(abuse_sha):
            blockers.append("abuse_evidence_hash_mismatch")

    if abuse is not None:
        for k, v in [("candidate_customer_key", EXPECTED["customer_key"]), ("lane", EXPECTED["lane"]), ("public_port", EXPECTED["public_port"]), ("visibility_bundle_sha256", str(vis_sha))]:
            if abuse.get(k) != v:
                blockers.append("abuse_evidence_scope_mismatch")
        if abuse.get("expected_version") not in (expected_version, __version__) or abuse.get("repository_version") != __version__:
            blockers.append("abuse_evidence_version_mismatch")

        for k in ["all_active_enabled_lane_customers_scanned", "exemption_policy_validated", "manual_unhard_audited", "restore_point_required_for_hard", "policy_backup_required_for_hard"]:
            if abuse.get(k) is not True:
                blockers.append(f"abuse_contract_failed:{k}")
        if abuse.get("skipped_active_customers") != []:
            blockers.append("abuse_contract_failed:skipped_active_customers")
        if abuse.get("missing_active_customers") != []:
            blockers.append("abuse_contract_failed:missing_active_customers")
        for k in ["silent_skip_detected", "hard_before_threshold_detected", "farms_over_alone_hardens", "worker_over_alone_hardens", "missing_or_stale_evidence_hardens", "db_failure_hardens", "firewall_failure_hardens", "classifier_enabled_automation", "mutation_performed"]:
            if abuse.get(k) is not False:
                blockers.append(f"abuse_contract_failed:{k}")

        hard_threshold = _as_int(abuse.get("hard_threshold_sec"))
        if hard_threshold is None or hard_threshold < 3600:
            blockers.append("abuse_contract_failed:hard_threshold_sec")

        states = abuse.get("state_machine_contract")
        if not isinstance(states, list) or any(not isinstance(x, str) for x in states):
            blockers.append("abuse_contract_failed:state_machine_contract_type")
            states_set = set()
        else:
            states_set = set(states)
        if not {"normal", "over_tracking", "over_grace", "hard"}.issubset(states_set):
            blockers.append("abuse_contract_failed:state_machine_contract")

        trans = abuse.get("transition_coverage")
        if not isinstance(trans, list) or any(not isinstance(x, str) for x in trans):
            blockers.append("abuse_contract_failed:transition_coverage_type")
            trans_set = set()
        else:
            trans_set = set(trans)
        need = {"normal->over_tracking", "over_tracking->over_grace", "over_grace->normal", "over_grace->over_tracking", "over_tracking->hard_after_threshold"}
        if not need.issubset(trans_set):
            blockers.append("abuse_contract_failed:transition_coverage")

        exemptions = abuse.get("exemptions")
        if not isinstance(exemptions, list) or any(not isinstance(x, dict) for x in exemptions):
            blockers.append("abuse_contract_failed:exemptions_type")
            exemptions = []
        for ex in exemptions:
            if not all(ex.get(k) for k in ("reason", "expiry", "operator", "event_audit_ref")):
                blockers.append("abuse_contract_failed:exemption_contract")

    ready = len(blockers) == 0
    return {
        "component": "phase11_single_customer_abuse_1h_readiness",
        "expected_version": expected_version,
        "source_visibility_bundle_version": source_visibility_bundle_version,
        "source_visibility_bundle_repository_version": source_visibility_bundle_repository_version,
        "repository_version": __version__,
        "candidate_customer_key": EXPECTED["customer_key"],
        "candidate_lane": EXPECTED["lane"],
        "candidate_public_port": EXPECTED["public_port"],
        "candidate_backend_target": EXPECTED["backend_target"],
        "visibility_bundle_link": vis.get("final_decision") if isinstance(vis, dict) else None,
        "visibility_bundle_sha256": vis_sha,
        "abuse_evidence_link": abuse.get("final_decision") if isinstance(abuse, dict) else None,
        "abuse_1h_coverage_ready": ready,
        "all_active_customers_coverage_ready": ready,
        "abuse_state_machine_contract_ready": ready,
        "hard_after_1h_contract_ready": ready,
        "no_farms_only_hard_contract_ready": ready,
        "no_worker_only_hard_contract_ready": ready,
        "exemption_contract_ready": ready,
        "no_silent_skip_contract_ready": ready,
        "no_missing_stale_evidence_hard_contract_ready": ready,
        "manual_unhard_audit_contract_ready": ready,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "abuse_automation_enabled": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "next_required_step": "phase11e_restart_container_order_readiness" if ready else "collect_phase11e_abuse_1h_runtime_coverage_evidence",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY" if ready else "BLOCKED",
    }
