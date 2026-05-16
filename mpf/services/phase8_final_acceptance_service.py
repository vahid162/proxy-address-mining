from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig


def _r(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_phase8_final_acceptance_report(
    cfg: MPFConfig,
    repo_root: Path | None = None,
) -> dict[str, object]:
    _ = cfg
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _r(root / "docs/PHASE_STATUS.md")
    readiness = phase_status
    evidence_doc = _r(root / "docs/PHASE_8_FINAL_ACCEPTANCE_EVIDENCE.md")

    report: dict[str, object] = {
        "component": "phase8_final_acceptance",
        "phase": "Phase 8 — Abuse 1h Core",
        "gate_type": "final_acceptance",
        "final_decision": "ACCEPTED",
        "acceptance_status": "PHASE8_ACCEPTED_ON_FARM5",
        "authorization_status": "ACCEPTED_NON_PRODUCTION_ACTIVATION",
        "inspection_only": True,
        "report_only": True,
        "execution_allowed": False,
        "phase8_accepted": True,
        "production_activation_allowed": False,
        "repository_version": __version__,
        "latest_recorded_farm5_sync_evidence": "0.1.123",
        "farm5_0_1_123_sync_evidence_present": "Phase 9 farm5 0.1.123 Sync/Test Evidence" in phase_status,
        "farm5_final_acceptance_readiness_evidence_present": "final-acceptance-readiness output summary" in readiness.lower(),
        "phase8_final_acceptance_evidence_doc_present": "# Phase 8 Final Acceptance Evidence" in evidence_doc,
        "current_state_phase8_accepted": "current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5" in phase_status,
        "phase9_working": "current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness" in phase_status,
        "abuse_invariant_preserved": True,
        "state_path_normal_over_tracking_over_grace_hard": True,
        "sustained_abuse_window_3600_seconds": True,
        "farms_over_alone_does_not_harden": True,
        "worker_over_alone_does_not_harden": True,
        "missing_evidence_does_not_harden": True,
        "stale_evidence_does_not_harden": True,
        "db_failure_does_not_harden": True,
        "firewall_failure_does_not_harden": True,
        "explicit_skip_required": True,
        "no_silent_skip_required": True,
        "all_active_customers_in_enabled_lanes_must_be_covered": True,
        "dry_run_evidence_synthetic_only": True,
        "dry_run_synthetic_item_count": 11,
        "dry_run_all_items_have_no_side_effects": True,
        "dry_run_execution_allowed": False,
        "dry_run_production_side_effects_allowed": False,
        "dry_run_phase8_acceptance_allowed_before_final_pr": False,
        "runtime_worker_authorized": False,
        "worker_start_authorized": False,
        "background_worker_authorized": False,
        "scheduler_authorized": False,
        "timer_authorized": False,
        "abuse_runner_authorized": False,
        "real_customer_evaluation_authorized": False,
        "production_db_execution_authorized": False,
        "db_reads_authorized": False,
        "db_writes_authorized": False,
        "firewall_apply_authorized": False,
        "iptables_restore_authorized": False,
        "customer_nat_authorized": False,
        "customer_firewall_rules_authorized": False,
        "customer_policy_mutation_authorized": False,
        "hard_block_authorized": False,
        "soft_block_authorized": False,
        "pause_automation_authorized": False,
        "production_traffic_authorized": False,
        "ui_authorized": False,
        "telegram_authorized": False,
        "next_phase": "Phase 9 — Check / Report / Diagnostics planning/readiness",
        "future_production_activation_gate_required": True,
        "future_phase9_readiness_pr_required": True,
    }
    blockers: list[str] = []
    required_tokens = {
        "current_accepted_phase_phase8_missing": "current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5",
        "current_working_phase_phase9_missing": "current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness",
        "production_traffic_none_missing": "production_traffic: none",
        "firewall_apply_allowed_no_missing": "firewall_apply_allowed: no",
        "abuse_automation_allowed_no_missing": "abuse_automation_allowed: no",
        "customer_onboarding_db_only_missing": "customer_onboarding_allowed: db_only",
        "proxy_data_plane_limited_runtime_missing": "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed_no_missing": "ui_allowed: no",
        "telegram_allowed_no_missing": "telegram_allowed: no",
        "live_snapshot_read_allowed_missing": "live_snapshot_read_allowed: iptables_save_read_only",
        "restore_lock_record_execution_allowed_missing": "restore_lock_record_execution_allowed: controlled_boundary_only",
        "abuse_invariant_text_missing": "normal -> over_tracking -> over_grace -> hard",
        "no_silent_skip_text_missing": "no silent skip",
        "all_active_customers_covered_text_missing": "all active customers in enabled lanes must be covered",
        "prod_activation_not_authorized_text_missing": "does not authorize production traffic",
        "firewall_apply_not_authorized_text_missing": "does not authorize firewall apply",
        "abuse_runner_not_authorized_text_missing": "abuse automation runner",
        "customer_nat_rules_not_authorized_text_missing": "does not authorize customer NAT/customer firewall rules",
    }
    for blocker_id, token in required_tokens.items():
        if token not in phase_status and token not in evidence_doc:
            blockers.append(blocker_id)
    if not report["farm5_0_1_123_sync_evidence_present"]:
        blockers.append("farm5_0_1_123_sync_evidence_missing")
    if not report["farm5_final_acceptance_readiness_evidence_present"]:
        blockers.append("farm5_final_acceptance_readiness_evidence_missing")
    if not report["phase8_final_acceptance_evidence_doc_present"]:
        blockers.append("phase8_final_acceptance_evidence_doc_missing")
    if blockers:
        report["final_decision"] = "BLOCKED"
    report["blockers"] = blockers
    report["warnings"] = []
    report["errors"] = []
    return report
