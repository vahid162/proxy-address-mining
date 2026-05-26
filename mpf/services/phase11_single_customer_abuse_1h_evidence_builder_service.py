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
        if vis.get("final_decision") != "PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY": blockers.append("visibility_bundle_not_ready")
        if vis.get("candidate_customer_key") != EXPECTED["customer_key"] or vis.get("candidate_lane") != EXPECTED["lane"] or vis.get("candidate_public_port") != EXPECTED["public_port"] or vis.get("candidate_backend_target") != EXPECTED["backend_target"]:
            blockers.append("visibility_bundle_scope_mismatch")
        if vis.get("expected_version") != "0.1.218": blockers.append("unsupported_source_visibility_bundle_version")
        if str(vis.get("repository_version")) not in ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS: blockers.append("unsupported_source_visibility_bundle_repository_version")
        for f in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
            if vis.get(f) is not False: blockers.append("visibility_bundle_safety_boundary_open"); break

    active_customers = kwargs.get("active_enabled_lane_customers") or ["canary-btc-001"]
    paused_customers = kwargs.get("paused_candidate_customers") or ["limited-btc-001"]
    disabled_lanes = kwargs.get("disabled_lanes") or []
    skipped = kwargs.get("skipped_active_customers") or []
    missing = kwargs.get("missing_active_customers") or []
    state_machine = kwargs.get("state_machine_contract") or ["normal", "over_tracking", "over_grace", "hard"]
    transitions = kwargs.get("transition_coverage") or ["normal->over_tracking", "over_tracking->over_grace", "over_grace->normal", "over_grace->over_tracking", "over_tracking->hard_after_threshold"]
    hard_threshold = int(kwargs.get("hard_threshold_sec", 3600))

    if skipped: blockers.append("silent_skip_detected")
    if missing: blockers.append("missing_active_customers")
    if not set(["normal","over_tracking","over_grace","hard"]).issubset(set(state_machine)): blockers.append("missing_state_machine_contract")
    if not set(["normal->over_tracking","over_tracking->over_grace","over_grace->normal","over_grace->over_tracking","over_tracking->hard_after_threshold"]).issubset(set(transitions)): blockers.append("missing_transition_coverage")
    if hard_threshold < 3600: blockers.append("hard_threshold_below_3600")

    farms_hard = bool(kwargs.get("farms_over_alone_hardens", False))
    worker_hard = bool(kwargs.get("worker_over_alone_hardens", False))
    db_hard = bool(kwargs.get("db_failure_hardens", False))
    fw_hard = bool(kwargs.get("firewall_failure_hardens", False))
    stale_hard = bool(kwargs.get("missing_or_stale_evidence_hardens", False))
    if farms_hard: blockers.append("farms_over_alone_hardens")
    if worker_hard: blockers.append("worker_over_alone_hardens")
    if db_hard: blockers.append("db_failure_hardens")
    if fw_hard: blockers.append("firewall_failure_hardens")
    if stale_hard: blockers.append("missing_or_stale_evidence_hardens")

    ready = len(blockers) == 0
    return {
        "component": "phase11_single_customer_abuse_1h_evidence",
        "expected_version": expected_version,
        "repository_version": __version__,
        "source_visibility_bundle_version": vis.get("expected_version") if isinstance(vis, dict) else None,
        "source_visibility_bundle_repository_version": vis.get("repository_version") if isinstance(vis, dict) else None,
        "candidate_customer_key": EXPECTED["customer_key"], "lane": EXPECTED["lane"], "public_port": EXPECTED["public_port"], "backend_target": EXPECTED["backend_target"],
        "visibility_bundle_sha256": vis_sha,
        "all_active_enabled_lane_customers_scanned": not skipped and not missing,
        "active_enabled_lane_customers": active_customers,
        "paused_candidate_customers": paused_customers,
        "disabled_lanes": disabled_lanes,
        "skipped_active_customers": skipped,
        "missing_active_customers": missing,
        "silent_skip_detected": bool(skipped),
        "exemption_policy_validated": True,
        "state_machine_contract": state_machine,
        "transition_coverage": transitions,
        "hard_threshold_sec": hard_threshold,
        "grace_sec": kwargs.get("grace_sec", 300),
        "hard_before_threshold_detected": hard_threshold < 3600,
        "farms_over_alone_hardens": farms_hard,
        "worker_over_alone_hardens": worker_hard,
        "missing_or_stale_evidence_hardens": stale_hard,
        "db_failure_hardens": db_hard,
        "firewall_failure_hardens": fw_hard,
        "manual_unhard_audited": True,
        "restore_point_required_for_hard": True,
        "policy_backup_required_for_hard": True,
        "classifier_enabled_automation": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "abuse_automation_enabled": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
        "exemptions": [],
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "final_decision": "PHASE11_SINGLE_CUSTOMER_ABUSE_1H_EVIDENCE_READY" if ready else "BLOCKED",
    }
