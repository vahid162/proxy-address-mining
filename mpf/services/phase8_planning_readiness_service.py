from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def build_phase8_planning_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = read_historical_phase_status(root)
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")

    phase7_accepted = "current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in phase_status
    phase8_working = "current_working_phase: Phase 8 — Abuse 1h Core planning/readiness" in phase_status
    current_state_preserved = phase7_accepted and phase8_working
    farm5 = "synced to 0.1.108" in phase_status and "694 passed" in phase_status
    scope_doc = "### Phase 7 Acceptance Scope" in phase_status
    ai_present = "normal -> over_tracking -> over_grace -> hard" in ai_phase8
    rem_aligned = "latest recorded farm5 sync evidence is 0.1.110." in remaining and "Phase 8" in remaining

    checks = [
        ("current_state_preserved", current_state_preserved, "PHASE_STATUS Current State"),
        ("phase7_accepted", phase7_accepted, "PHASE_STATUS accepted phase"),
        ("phase8_working", phase8_working, "PHASE_STATUS working phase"),
        ("farm5_0_1_108_sync_evidence_present", farm5, "PHASE_STATUS evidence block"),
        ("phase7_acceptance_scope_documented", scope_doc, "PHASE_STATUS Phase 7 Acceptance Scope"),
        ("ai_phase8_task_present", ai_present, "docs/AI_PHASE_8_TASK.md"),
        ("remaining_plan_phase8_aligned", rem_aligned, "docs/REMAINING_PHASE_PLAN.md"),
    ]
    blockers = [f"{name}_missing_or_failed" for name, ok, _ in checks if not ok]
    checklist = [{"item": n, "status": "PASS" if ok else "BLOCKED", "evidence": ev} for n, ok, ev in checks]

    invariant = {"state_path": ["normal", "over_tracking", "over_grace", "hard"], "sustained_abuse_seconds": 3600,
                 "farms_over_alone_hardens": False, "worker_over_alone_hardens": False,
                 "all_active_customers_in_enabled_lanes_required": True, "silent_skip_allowed": False,
                 "hardening_requires_evidence": True, "hardening_requires_audit": True,
                 "hardening_requires_restore_reference": True}

    false_flags = {k: False for k in ["live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_save_executed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation","db_usage_sample_write_allowed","db_usage_sample_written","db_policy_event_write_allowed","db_policy_event_written","db_abuse_state_write_allowed","db_abuse_state_written","db_abuse_event_write_allowed","db_abuse_event_written","filesystem_write_executed","scheduler_job_created","timer_enabled","usage_collector_runtime_allowed","usage_collector_runtime_started","policy_reject_collector_runtime_allowed","policy_reject_collector_runtime_started","abuse_runner_runtime_allowed","abuse_runner_runtime_started","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","abuse_automation_allowed_runtime","hard_block_allowed","hard_block_applied","soft_block_allowed","soft_block_applied","pause_automation_allowed","pause_applied","ui_allowed_runtime","telegram_allowed_runtime"]}

    return {
        "component": "phase8_planning_readiness", "phase": "Phase 8 — Abuse 1h Core", "gate_type": "phase8_planning_readiness",
        "final_decision": "BLOCKED", "readiness_status": "PHASE8_PLANNING_READINESS_DEFINED_NOT_ACCEPTED",
        "authorization_status": "PHASE8_PLANNING_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED", "inspection_only": True, "report_only": True,
        "preflight_only": True, "dry_run": True, "execution_allowed": False, "phase8_acceptance_allowed": False,
        "abuse_automation_authorized": False, "abuse_runner_authorized": False, "abuse_state_db_writes_authorized": False,
        "abuse_event_db_writes_authorized": False, "hard_block_authorized": False, "soft_block_authorized": False,
        "pause_automation_authorized": False, "production_traffic_authorized": False, "firewall_apply_authorized": False,
        "iptables_restore_authorized": False, "customer_nat_authorized": False, "customer_firewall_rules_authorized": False,
        "ui_authorized": False, "telegram_authorized": False, "operator_review_required": True,
        "separate_phase8_state_machine_contract_pr_required": True, "fresh_farm5_sync_evidence_required_before_acceptance": True,
        "current_state_preserved": current_state_preserved, "phase7_accepted": phase7_accepted, "phase8_working": phase8_working,
        "phase8_planning_only": True, "farm5_0_1_108_sync_evidence_present": farm5, "phase7_acceptance_scope_documented": scope_doc,
        "ai_phase8_task_present": ai_present, "remaining_plan_phase8_aligned": rem_aligned, "apply_mode_plan_only": True,
        "runtime_activation_disabled": True, "production_traffic_none": True, "firewall_apply_disallowed": True,
        "customer_nat_disallowed": True, "customer_firewall_rules_disallowed": True, "iptables_restore_disallowed": True,
        "abuse_automation_disallowed": True, "abuse_runner_disallowed": True, "abuse_state_db_writes_disallowed": True,
        "abuse_event_db_writes_disallowed": True, "hard_block_disallowed": True, "soft_block_disallowed": True,
        "pause_automation_disallowed": True, "ui_disallowed": True, "telegram_disallowed": True,
        "abuse_invariant_preserved": True, "all_active_customers_coverage_required": True, "no_silent_skip_required": True,
        "abuse_invariant": invariant,
        "future_phase8_contracts": ["abuse state-machine contract","abuse evidence/reporting contract","abuse dry-run evaluator","DB-only controlled transition readiness","runtime/worker integration readiness","final Abuse 1h acceptance"],
        "phase8_planning_readiness_checklist": checklist, "blockers": blockers, "errors": [], **false_flags
    }
