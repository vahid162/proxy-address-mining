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


def _source_ok(src: object) -> bool:
    if not isinstance(src, str):
        return False
    s = src.strip().lower()
    return bool(s) and s not in {"default", "synthetic", "placeholder", "none"}


def build_phase11_single_customer_abuse_1h_evidence_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    warnings: list[str] = []
    expected_version = str(kwargs.get("expected_version", __version__))

    for c in ["operator_confirmed", "i_understand_evidence_only", "i_understand_no_abuse_automation_enable", "i_understand_no_hard_block", "i_understand_no_firewall_apply", "i_understand_no_db_mutation", "i_understand_no_production_traffic", "i_understand_no_miner_traffic"]:
        if kwargs.get(c) is not True:
            blockers.append(f"missing_confirmation:{c}")

    vis_path = Path(str(kwargs.get("visibility_bundle_json", "")))
    vis = _load(vis_path, "visibility_bundle_missing", "visibility_bundle_invalid", blockers)
    vis_sha = str(kwargs.get("visibility_bundle_json_sha256", ""))
    if vis is not None and _sha(vis_path) != vis_sha:
        blockers.append("visibility_bundle_hash_mismatch")

    if vis is not None:
        if vis.get("final_decision") != "PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY":
            blockers.append("visibility_bundle_not_ready")
        if vis.get("candidate_customer_key") != EXPECTED["customer_key"] or vis.get("candidate_lane") != EXPECTED["lane"] or vis.get("candidate_public_port") != EXPECTED["public_port"] or vis.get("candidate_backend_target") != EXPECTED["backend_target"]:
            blockers.append("visibility_bundle_scope_mismatch")
        if vis.get("expected_version") != "0.1.218":
            blockers.append("unsupported_source_visibility_bundle_version")
        if str(vis.get("repository_version")) not in ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS:
            blockers.append("unsupported_source_visibility_bundle_repository_version")
        for f in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
            if vis.get(f) is not False:
                blockers.append("visibility_bundle_safety_boundary_open")
                break

    se_path = kwargs.get('source_evidence_json')
    se = None
    if se_path is not None:
        sp = Path(str(se_path)); se = _load(sp, 'source_evidence_missing', 'source_evidence_invalid', blockers)
        ssha = kwargs.get('source_evidence_json_sha256')
        if se is not None and ssha is not None and _sha(sp) != str(ssha): blockers.append('source_evidence_hash_mismatch')

    active_customers = (se or {}).get('active_enabled_lane_customers', kwargs.get("active_enabled_lane_customers"))
    paused_customers = (se or {}).get('paused_candidate_customers', kwargs.get("paused_candidate_customers"))
    disabled_lanes = (se or {}).get('disabled_lanes', kwargs.get("disabled_lanes"))
    skipped = kwargs.get("skipped_active_customers")
    missing = kwargs.get("missing_active_customers")
    state_machine = kwargs.get("state_machine_contract")
    transitions = kwargs.get("transition_coverage")
    hard_threshold = kwargs.get("hard_threshold_sec")

    active_src = kwargs.get("active_customer_coverage_source")
    abuse_src = kwargs.get("abuse_contract_source")
    exemption_src = kwargs.get("exemption_contract_source")
    threshold_src = kwargs.get("hard_threshold_source")
    unhard_src = kwargs.get("manual_unhard_audit_source")
    restore_src = kwargs.get("restore_policy_backup_source")

    if not _source_ok(active_src): blockers.append("missing_active_customer_coverage_source")
    if not _source_ok(abuse_src): blockers.append("missing_abuse_state_machine_contract_source")
    if not _source_ok(abuse_src): blockers.append("missing_transition_coverage_source")
    if not _source_ok(threshold_src): blockers.append("missing_hard_threshold_source")
    if not _source_ok(exemption_src): blockers.append("missing_exemption_contract_source")
    if not _source_ok(unhard_src): blockers.append("missing_manual_unhard_audit_source")
    if not _source_ok(restore_src): blockers.append("missing_restore_policy_backup_source")

    if not isinstance(active_customers, list): blockers.append("active_enabled_lane_customers_invalid")
    if isinstance(paused_customers,list) and 'limited-btc-001' not in paused_customers: blockers.append('limited_btc_001_not_paused_candidate')
    if not isinstance(paused_customers, list): blockers.append("paused_candidate_customers_invalid")
    if not isinstance(disabled_lanes, list): blockers.append("disabled_lanes_invalid")
    if not isinstance(skipped, list): blockers.append("skipped_active_customers_invalid")
    if not isinstance(missing, list): blockers.append("missing_active_customers_invalid")
    if isinstance(skipped, list) and skipped: blockers.append("silent_skip_detected")
    if isinstance(missing, list) and missing: blockers.append("missing_active_customers")

    if not isinstance(state_machine, list) or not set(["normal", "over_tracking", "over_grace", "hard"]).issubset(set(state_machine or [])):
        blockers.append("missing_state_machine_contract")
    if not isinstance(transitions, list) or not set(["normal->over_tracking", "over_tracking->over_grace", "over_grace->normal", "over_grace->over_tracking", "over_tracking->hard_after_threshold"]).issubset(set(transitions or [])):
        blockers.append("missing_transition_coverage")

    if isinstance(hard_threshold, bool) or not isinstance(hard_threshold, int):
        blockers.append("hard_threshold_invalid")
    elif hard_threshold < 3600:
        blockers.append("hard_threshold_below_3600")

    exemption_validated = kwargs.get("exemption_policy_validated")
    manual_unhard_audited = kwargs.get("manual_unhard_audited")
    restore_required = kwargs.get("restore_point_required_for_hard")
    policy_backup_required = kwargs.get("policy_backup_required_for_hard")
    farms_hard = kwargs.get("farms_over_alone_hardens")
    worker_hard = kwargs.get("worker_over_alone_hardens")
    db_hard = kwargs.get("db_failure_hardens")
    fw_hard = kwargs.get("firewall_failure_hardens")
    stale_hard = kwargs.get("missing_or_stale_evidence_hardens")

    if exemption_validated is not True: blockers.append("exemption_policy_not_validated")
    if manual_unhard_audited is not True: blockers.append("manual_unhard_not_audited")
    if restore_required is not True: blockers.append("restore_point_not_required_for_hard")
    if policy_backup_required is not True: blockers.append("policy_backup_not_required_for_hard")
    if farms_hard is not False: blockers.append("farms_over_alone_hardens")
    if worker_hard is not False: blockers.append("worker_over_alone_hardens")
    if db_hard is not False: blockers.append("db_failure_hardens")
    if fw_hard is not False: blockers.append("firewall_failure_hardens")
    if stale_hard is not False: blockers.append("missing_or_stale_evidence_hardens")

    ready = len(blockers) == 0
    return {
        "component": "phase11_single_customer_abuse_1h_evidence",
        "expected_version": expected_version,
        "repository_version": __version__,
        "source_visibility_bundle_version": vis.get("expected_version") if isinstance(vis, dict) else None,
        "source_visibility_bundle_repository_version": vis.get("repository_version") if isinstance(vis, dict) else None,
        "candidate_customer_key": EXPECTED["customer_key"], "lane": EXPECTED["lane"], "public_port": EXPECTED["public_port"], "backend_target": EXPECTED["backend_target"],
        "visibility_bundle_sha256": vis_sha,
        "active_customer_coverage_source": active_src,
        "abuse_contract_source": abuse_src,
        "exemption_contract_source": exemption_src,
        "hard_threshold_source": threshold_src,
        "manual_unhard_audit_source": unhard_src,
        "restore_policy_backup_source": restore_src,
        "all_active_enabled_lane_customers_scanned": isinstance(skipped, list) and isinstance(missing, list) and not skipped and not missing,
        "active_enabled_lane_customers": active_customers if isinstance(active_customers, list) else [],
        "paused_candidate_customers": paused_customers if isinstance(paused_customers, list) else [],
        "disabled_lanes": disabled_lanes if isinstance(disabled_lanes, list) else [],
        "skipped_active_customers": skipped if isinstance(skipped, list) else [],
        "missing_active_customers": missing if isinstance(missing, list) else [],
        "silent_skip_detected": bool(skipped) if isinstance(skipped, list) else True,
        "exemption_policy_validated": exemption_validated is True,
        "state_machine_contract": state_machine if isinstance(state_machine, list) else [],
        "transition_coverage": transitions if isinstance(transitions, list) else [],
        "hard_threshold_sec": hard_threshold if isinstance(hard_threshold, int) and not isinstance(hard_threshold, bool) else None,
        "grace_sec": kwargs.get("grace_sec"),
        "hard_before_threshold_detected": (isinstance(hard_threshold, int) and not isinstance(hard_threshold, bool) and hard_threshold < 3600),
        "farms_over_alone_hardens": farms_hard is True,
        "worker_over_alone_hardens": worker_hard is True,
        "missing_or_stale_evidence_hardens": stale_hard is True,
        "db_failure_hardens": db_hard is True,
        "firewall_failure_hardens": fw_hard is True,
        "manual_unhard_audited": manual_unhard_audited is True,
        "restore_point_required_for_hard": restore_required is True,
        "policy_backup_required_for_hard": policy_backup_required is True,
        "classifier_enabled_automation": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "abuse_automation_enabled": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
        "exemptions": kwargs.get("exemptions") if isinstance(kwargs.get("exemptions"), list) else [],
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "final_decision": "PHASE11_SINGLE_CUSTOMER_ABUSE_1H_EVIDENCE_READY" if ready else "BLOCKED",
    }
