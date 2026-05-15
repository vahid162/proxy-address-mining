from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


def build_phase6_operator_acceptance_decision_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    ps = (root / "docs" / "PHASE_STATUS.md")
    ai = (root / "docs" / "AI_PHASE_6_TASK.md")
    rem = (root / "docs" / "REMAINING_PHASE_PLAN.md")
    phase_status = ps.read_text(encoding="utf-8") if ps.exists() else ""
    ai_text = ai.read_text(encoding="utf-8") if ai.exists() else ""
    rem_text = rem.read_text(encoding="utf-8") if rem.exists() else ""

    accepted = "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in phase_status
    sync = "farm5 synced to 0.1.100" in phase_status and "pytest during sync: 661 passed" in phase_status
    gates_closed = all(x in phase_status for x in ["production_traffic: none", "firewall_apply_allowed: no", "abuse_automation_allowed: no"])
    no_nat = "no customer NAT redirects" in phase_status
    no_ipv4 = "no MPF/customer IPv4 firewall references detected" in phase_status
    no_ipv6 = "no MPF/customer IPv6 firewall references detected" in phase_status
    no_non_deleted = "current customer list: no non-deleted customers" in phase_status
    abuse_ok = all(x in ai_text for x in ["normal -> over_tracking -> over_grace -> hard", "farms-over alone must not harden", "worker-over alone must not harden", "no silent skip"])

    blockers: list[str] = []
    errors: list[str] = []
    if not phase_status:
        blockers.append("docs/PHASE_STATUS.md missing")
    if not sync:
        blockers.append("farm5 0.1.100 sync evidence missing")
    if not accepted:
        blockers.append("Phase 6 accepted in Current State missing")
    if "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" not in phase_status:
        blockers.append("Phase 7 working phase not set in Current State")
    if not gates_closed:
        blockers.append("production/apply/abuse gates are not closed")
    if not abuse_ok:
        blockers.append("abuse invariant missing or weakened")

    final_decision = "ACCEPTED" if accepted and not blockers else "BLOCKED"
    phase7_allowed = final_decision == "ACCEPTED"

    r = {
        "component": "phase6_operator_acceptance_decision",
        "phase": "Phase 6 — Firewall Planner",
        "gate_type": "phase6_operator_acceptance_decision",
        "inspection_only": True, "report_only": True, "preflight_only": True, "dry_run": True,
        "execution_allowed": False, "customer_nat_authorized": False, "customer_firewall_rules_authorized": False,
        "production_traffic_authorized": False, "firewall_apply_authorized": False, "iptables_restore_authorized": False,
        "usage_automation_authorized": False, "abuse_automation_authorized": False, "ui_authorized": False, "telegram_authorized": False,
        "phase7_start_allowed": phase7_allowed, "phase8_start_allowed": False,
        "final_decision": final_decision,
        "acceptance_status": "PHASE6_ACCEPTED_PLANNER_REPORTING_ONLY" if final_decision == "ACCEPTED" else "PHASE6_NOT_ACCEPTED",
        "authorization_status": "PHASE6_ACCEPTED_WITH_RUNTIME_GATES_CLOSED" if final_decision == "ACCEPTED" else "FINAL_OPERATOR_ACCEPTANCE_NOT_GRANTED",
        "phase6_acceptance_allowed": phase7_allowed, "phase6_accepted": phase7_allowed,
        "next_phase": "Phase 7 — Usage + Policy/Reject Accounting" if phase7_allowed else "Phase 6 — Final Operator Acceptance Decision",
        "farm5_0_1_100_sync_evidence_present": sync,
        "phase5_or_phase6_accepted_state_valid": ("current_accepted_phase: Phase 5" in phase_status) or accepted,
        "phase6_accepted_as_planner_only": accepted,
        "phase6_runtime_gates_closed": gates_closed,
        "production_traffic_none": "production_traffic: none" in phase_status,
        "firewall_apply_disallowed": "firewall_apply_allowed: no" in phase_status,
        "customer_nat_disallowed": True,
        "customer_firewall_rules_disallowed": True,
        "iptables_restore_disallowed": True,
        "usage_automation_disallowed": True,
        "abuse_automation_disallowed": "abuse_automation_allowed: no" in phase_status,
        "ui_disallowed": "ui_allowed: no" in phase_status,
        "telegram_disallowed": "telegram_allowed: no" in phase_status,
        "final_acceptance_review_present": "Phase 6 Final Acceptance Review Package" in phase_status,
        "final_acceptance_review_safe": "non-authorizing" in phase_status,
        "final_acceptance_readiness_present": "Phase 6 Final Acceptance Readiness" in phase_status,
        "manual_canary_server_evidence_present": "Manual Canary Customer Server Evidence" in phase_status,
        "apply_gate_readiness_present": "apply-gate-readiness" in rem_text.lower() or "apply-gate" in rem_text.lower(),
        "gate_review_safe": True,
        "no_non_deleted_customer_evidence_present": no_non_deleted,
        "no_customer_nat_redirects_evidenced": no_nat,
        "no_mpf_customer_ipv4_firewall_references_evidenced": no_ipv4,
        "no_mpf_customer_ipv6_firewall_references_evidenced": no_ipv6,
        "abuse_invariant_preserved": abuse_ok,
        "phase7_started_as_planning_only": "planning/readiness" in rem_text.lower() or "planning/readiness" in phase_status.lower(),
        "phase7_not_implemented_in_this_pr": True,
        "phase8_not_implemented_in_this_pr": True,
        "blockers": blockers,
        "errors": errors,
    }
    for k in ["live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation","db_apply_record_write_allowed","db_apply_record_written","filesystem_write_executed","restore_point_write_allowed","restore_point_written","lock_acquisition_allowed","lock_acquired","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","usage_automation_allowed","abuse_automation_allowed_runtime","ui_allowed_runtime","telegram_allowed_runtime"]:
        r[k] = False
    return r
