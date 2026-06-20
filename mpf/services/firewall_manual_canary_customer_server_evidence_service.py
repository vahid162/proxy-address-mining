from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig
from mpf.services import (
    firewall_apply_gate_readiness_service,
    firewall_manual_canary_customer_acceptance_readiness_service,
    firewall_manual_canary_customer_proposal_service,
    firewall_no_customer_runtime_execution_evidence_service,
)


def build_manual_canary_customer_server_evidence_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    text = (root / "docs" / "PHASE_STATUS.md").read_text(encoding="utf-8") if (root / "docs" / "PHASE_STATUS.md").exists() else ""
    blockers: list[str] = []
    if not text:
        blockers.append("docs/PHASE_STATUS.md missing")
    current_state_preserved = "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5" in text and "restore_lock_record_execution_allowed: controlled_boundary_only" in text
    if not current_state_preserved:
        blockers.append("Current State missing or changed")
    farm5 = "farm5 synced to 0.1.96" in text and "mpf --version: 0.1.96" in text
    if not farm5:
        blockers.append("farm5 0.1.96 sync evidence missing")

    proposal = firewall_manual_canary_customer_proposal_service.build_manual_canary_customer_proposal_report(cfg, repo_root=root)
    acceptance = firewall_manual_canary_customer_acceptance_readiness_service.build_manual_canary_customer_acceptance_readiness_report(cfg, repo_root=root)
    controlled = firewall_no_customer_runtime_execution_evidence_service.build_no_customer_runtime_execution_evidence_report(cfg, repo_root=root)
    readiness = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg, repo_root=root, include_runtime_approval_summary=False, include_runtime_evidence_summary=False, include_manual_canary_summary=False)

    no_non_deleted = "current customer list: no non-deleted customers" in text
    no_nat = "no customer NAT redirects" in text
    no_ipv4 = "no MPF/customer IPv4 firewall references detected" in text
    no_ipv6 = "no MPF/customer IPv6 firewall references detected" in text
    for ok,msg in [
        (proposal.get("final_decision")=="BLOCKED","manual canary proposal missing/not BLOCKED/execution_allowed true/customer NAT authorized/customer firewall rules authorized"),
        (acceptance.get("final_decision")=="BLOCKED","manual canary acceptance-readiness missing/not BLOCKED/execution_allowed true/customer NAT authorized/customer firewall rules authorized"),
        (controlled.get("final_decision")=="BLOCKED" and not controlled.get("execution_allowed",False),"controlled no-customer runtime evidence missing/not BLOCKED/execution_allowed true"),
        (readiness.get("final_decision")=="BLOCKED","apply-gate-readiness missing/not BLOCKED"),
        (cfg.firewall.apply_mode=="plan_only","firewall.apply_mode is not plan_only"),
        (not cfg.proxy.runtime_activation_allowed,"proxy.runtime_activation_allowed is true"),
        (no_non_deleted,"no non-deleted customer evidence is absent from sync evidence"),
        (no_nat,"no customer NAT redirects evidence is absent"),
        (no_ipv4,"no MPF/customer IPv4 firewall references evidence is absent"),
        (no_ipv6,"no MPF/customer IPv6 firewall references evidence is absent"),
    ]:
        if not ok: blockers.append(msg)

    safety_false = ["live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation","db_apply_record_write_allowed","db_apply_record_written","filesystem_write_executed","restore_point_write_allowed","restore_point_written","lock_acquisition_allowed","lock_acquired","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","usage_automation_allowed","abuse_automation_allowed_runtime","ui_allowed_runtime","telegram_allowed_runtime"]
    report = {
        "component":"firewall_manual_canary_customer_server_evidence","phase":"Phase 6 — Firewall Planner","gate_type":"manual_canary_customer_server_evidence_final_gate_review",
        "final_decision":"BLOCKED","authorization_status":"MANUAL_CANARY_SERVER_EVIDENCE_NOT_ACCEPTED","server_evidence_status":"SERVER_SYNC_EVIDENCED_BUT_CANARY_NOT_EXECUTED",
        "inspection_only":True,"report_only":True,"preflight_only":True,"dry_run":True,"execution_allowed":False,
        "customer_nat_authorized":False,"customer_firewall_rules_authorized":False,"production_traffic_authorized":False,
        "operator_approval_required":True,"fresh_farm5_canary_execution_evidence_required":True,"separate_phase6_final_acceptance_pr_required":True,
        "apply_decision":"BLOCKED","verify_decision":"BLOCKED","rollback_decision":"BLOCKED",
        "current_state_preserved":current_state_preserved,"farm5_0_1_96_sync_evidence_present":farm5,
        "manual_canary_proposal_present":bool(proposal),"manual_canary_proposal_blocked":proposal.get("final_decision")=="BLOCKED","manual_canary_proposal_execution_disallowed":not proposal.get("execution_allowed",False),
        "manual_canary_acceptance_readiness_present":bool(acceptance),"manual_canary_acceptance_readiness_blocked":acceptance.get("final_decision")=="BLOCKED","manual_canary_acceptance_execution_disallowed":not acceptance.get("execution_allowed",False),
        "controlled_no_customer_runtime_evidence_present":bool(controlled),"controlled_no_customer_runtime_evidence_blocked":controlled.get("final_decision")=="BLOCKED","controlled_no_customer_runtime_evidence_execution_disallowed":not controlled.get("execution_allowed",False),
        "apply_gate_readiness_present":bool(readiness),"apply_gate_readiness_blocked":readiness.get("final_decision")=="BLOCKED",
        "apply_mode_plan_only":cfg.firewall.apply_mode=="plan_only","runtime_activation_disabled":not cfg.proxy.runtime_activation_allowed,
        "phase_gate_firewall_apply_disallowed":"firewall_apply_allowed: no" in text,"phase_gate_production_traffic_none":"production_traffic: none" in text,"phase_gate_abuse_automation_disallowed":"abuse_automation_allowed: no" in text,
        "no_non_deleted_customer_evidence_present":no_non_deleted,"no_customer_nat_redirects_evidenced":no_nat,"no_mpf_customer_ipv4_firewall_references_evidenced":no_ipv4,"no_mpf_customer_ipv6_firewall_references_evidenced":no_ipv6,
        "customer_canary_not_executed":True,"customer_nat_disallowed":True,"customer_firewall_rules_disallowed":True,"production_traffic_none":True,"usage_automation_disallowed":True,"abuse_automation_disallowed":True,
    }
    for k in safety_false: report[k]=False
    report["manual_canary_customer_server_evidence_checklist"]=[{"item":i,"status":"PASS" if report.get(i,False) else "BLOCKED","evidence":str(report.get(i))} for i in ["current_state_preserved","farm5_0_1_96_sync_evidence_present","manual_canary_proposal_blocked","manual_canary_proposal_execution_disallowed","manual_canary_acceptance_readiness_blocked","manual_canary_acceptance_execution_disallowed","controlled_no_customer_runtime_evidence_blocked","controlled_no_customer_runtime_evidence_execution_disallowed","apply_gate_readiness_blocked","apply_mode_plan_only","runtime_activation_disabled","no_non_deleted_customer_evidence_present","no_customer_nat_redirects_evidenced","no_mpf_customer_ipv4_firewall_references_evidenced","no_mpf_customer_ipv6_firewall_references_evidenced","customer_canary_not_executed","customer_nat_disallowed","customer_firewall_rules_disallowed","production_traffic_none","usage_automation_disallowed","abuse_automation_disallowed"]]
    report["blockers"]=blockers
    report["errors"]=[]
    return report
