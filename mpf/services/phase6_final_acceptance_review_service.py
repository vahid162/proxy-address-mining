from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services import firewall_apply_gate_readiness_service, firewall_gate_review_service, firewall_manual_canary_customer_acceptance_readiness_service, firewall_manual_canary_customer_proposal_service, firewall_manual_canary_customer_server_evidence_service, firewall_no_customer_runtime_execution_approval_service, firewall_no_customer_runtime_execution_evidence_service, phase6_final_acceptance_readiness_service


def build_phase6_final_acceptance_review_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status_path = root / "docs" / "PHASE_STATUS.md"
    phase_status = phase_status_path.read_text(encoding="utf-8") if phase_status_path.exists() else ""
    ai_task = (root / "docs" / "AI_PHASE_6_TASK.md").read_text(encoding="utf-8") if (root / "docs" / "AI_PHASE_6_TASK.md").exists() else ""

    blockers: list[str] = []
    errors: list[str] = []
    if not phase_status:
        blockers.append("docs/PHASE_STATUS.md missing")
    current_state_preserved = "## Current State" in phase_status and "current_working_phase: Phase 6 — Firewall Planner" in phase_status
    farm5_ev = "farm5 synced to 0.1.98" in phase_status and "pytest during sync: 652 passed" in phase_status
    phase5_accepted = "current_accepted_phase: Phase 5" in phase_status
    phase6_working = "current_working_phase: Phase 6 — Firewall Planner" in phase_status
    no_non_deleted = "current customer list: no non-deleted customers" in phase_status
    no_nat = "no customer NAT redirects" in phase_status
    no_ipv4 = "no MPF/customer IPv4 firewall references detected" in phase_status
    no_ipv6 = "no MPF/customer IPv6 firewall references detected" in phase_status
    abuse_ok = "normal -> over_tracking -> over_grace -> hard" in ai_task and "no silent skip" in ai_task

    approval = firewall_no_customer_runtime_execution_approval_service.build_no_customer_runtime_execution_approval_report(cfg, repo_root=root)
    evidence = firewall_no_customer_runtime_execution_evidence_service.build_no_customer_runtime_execution_evidence_report(cfg, repo_root=root)
    proposal = firewall_manual_canary_customer_proposal_service.build_manual_canary_customer_proposal_report(cfg, repo_root=root)
    acceptance = firewall_manual_canary_customer_acceptance_readiness_service.build_manual_canary_customer_acceptance_readiness_report(cfg, repo_root=root)
    server = firewall_manual_canary_customer_server_evidence_service.build_manual_canary_customer_server_evidence_report(cfg, repo_root=root)
    readiness = phase6_final_acceptance_readiness_service.build_phase6_final_acceptance_readiness_report(cfg, repo_root=root)
    apply_readiness = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg, repo_root=root, include_phase6_final_acceptance_summary=False)

    if not current_state_preserved: blockers.append("Current State missing or changed")
    if not farm5_ev: blockers.append("farm5 0.1.98 sync evidence missing")
    if not (phase5_accepted and phase6_working): blockers.append("Phase 5 accepted / Phase 6 working gate missing")
    if approval.get("final_decision") != "BLOCKED" or approval.get("execution_allowed", False): blockers.append("no-customer runtime approval report invalid")
    if evidence.get("final_decision") != "BLOCKED" or evidence.get("execution_allowed", False): blockers.append("controlled no-customer runtime evidence report invalid")
    if proposal.get("final_decision") != "BLOCKED" or proposal.get("execution_allowed", False): blockers.append("manual canary proposal report invalid")
    if acceptance.get("final_decision") != "BLOCKED" or acceptance.get("execution_allowed", False): blockers.append("manual canary acceptance-readiness report invalid")
    if server.get("final_decision") != "BLOCKED" or server.get("execution_allowed", False): blockers.append("manual canary server evidence report invalid")
    if readiness.get("final_decision") != "BLOCKED" or readiness.get("execution_allowed", False) or readiness.get("phase6_acceptance_allowed", False): blockers.append("Phase 6 final acceptance readiness report invalid")
    if apply_readiness.get("final_decision") != "BLOCKED": blockers.append("apply-gate-readiness missing/not BLOCKED")
    blockers.append("manual canary actual execution evidence is missing")
    blockers.append("manual canary final gate is not accepted")
    if not abuse_ok: blockers.append("abuse invariant missing or weakened")

    report = {
        "component": "phase6_final_acceptance_review", "phase": "Phase 6 — Firewall Planner", "gate_type": "phase6_final_acceptance_review",
        "final_decision": "BLOCKED", "review_status": "READY_FOR_OPERATOR_REVIEW_BUT_NOT_ACCEPTED", "acceptance_status": "PHASE6_NOT_ACCEPTED", "authorization_status": "FINAL_ACCEPTANCE_REVIEW_DEFINED_NOT_GRANTED",
        "inspection_only": True, "report_only": True, "preflight_only": True, "dry_run": True, "execution_allowed": False, "phase6_acceptance_allowed": False,
        "customer_nat_authorized": False, "customer_firewall_rules_authorized": False, "production_traffic_authorized": False, "operator_review_required": True,
        "fresh_farm5_0_1_99_sync_evidence_required": True, "separate_phase6_acceptance_pr_required": True, "phase7_start_allowed": False, "phase8_start_allowed": False,
        "current_state_preserved": current_state_preserved, "farm5_0_1_98_sync_evidence_present": farm5_ev, "phase5_accepted": phase5_accepted, "phase6_working": phase6_working,
        "phase6_not_accepted_yet": True, "no_customer_runtime_approval_done": approval.get("final_decision") == "BLOCKED", "controlled_no_customer_runtime_evidence_done": evidence.get("final_decision") == "BLOCKED",
        "manual_canary_proposal_done": proposal.get("final_decision") == "BLOCKED", "manual_canary_acceptance_readiness_done": acceptance.get("final_decision") == "BLOCKED", "manual_canary_server_evidence_done": server.get("final_decision") == "BLOCKED",
        "phase6_final_acceptance_readiness_done": readiness.get("final_decision") == "BLOCKED", "phase6_final_acceptance_readiness_blocked": readiness.get("final_decision") == "BLOCKED", "manual_canary_actual_execution_missing": True,
        "manual_canary_final_gate_not_accepted": True, "apply_gate_readiness_blocked": apply_readiness.get("final_decision") == "BLOCKED", "gate_review_blocked": True, "gate_review_non_applyable": True, "gate_review_live_apply_disallowed": True,
        "phase_gate_firewall_apply_disallowed": "firewall_apply_allowed: no" in phase_status, "phase_gate_production_traffic_none": "production_traffic: none" in phase_status, "phase_gate_abuse_automation_disallowed": "abuse_automation_allowed: no" in phase_status,
        "no_non_deleted_customer_evidence_present": no_non_deleted, "no_customer_nat_redirects_evidenced": no_nat, "no_mpf_customer_ipv4_firewall_references_evidenced": no_ipv4, "no_mpf_customer_ipv6_firewall_references_evidenced": no_ipv6,
        "abuse_invariant_preserved": abuse_ok, "phase7_not_started": True, "phase8_not_started": True, "phase6_final_acceptance_review_blocked": True,
    }
    for k in ["live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation","db_apply_record_write_allowed","db_apply_record_written","filesystem_write_executed","restore_point_write_allowed","restore_point_written","lock_acquisition_allowed","lock_acquired","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","usage_automation_allowed","abuse_automation_allowed_runtime","ui_allowed_runtime","telegram_allowed_runtime"]:
        report[k]=False
    report["phase6_final_acceptance_review_checklist"]=[
        {"item":"current_state_preserved","status":"PASS" if current_state_preserved else "BLOCKED","evidence":"docs/PHASE_STATUS.md Current State"},
        {"item":"farm5_0_1_98_sync_evidence_present","status":"PASS" if farm5_ev else "BLOCKED","evidence":"docs/PHASE_STATUS.md farm5 0.1.98"},
        {"item":"manual_canary_actual_execution_missing","status":"BLOCKED","evidence":"no non-deleted customers"},
        {"item":"manual_canary_final_gate_not_accepted","status":"BLOCKED","evidence":"report-only non-authorizing"},
        {"item":"no_customer_nat_authorized","status":"PASS","evidence":"customer_nat_authorized=false"},
        {"item":"no_customer_firewall_rules_authorized","status":"PASS","evidence":"customer_firewall_rules_authorized=false"},
        {"item":"no_production_traffic","status":"PASS","evidence":"production_traffic_authorized=false"},
        {"item":"abuse_invariant_preserved","status":"PASS" if abuse_ok else "BLOCKED","evidence":"AI_PHASE_6_TASK abuse invariant"},
    ]
    report["blockers"] = blockers
    report["errors"] = errors
    return report
