from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig
from mpf.services import firewall_apply_gate_readiness_service, firewall_manual_canary_customer_acceptance_readiness_service, firewall_manual_canary_customer_proposal_service, firewall_manual_canary_customer_server_evidence_service, firewall_no_customer_runtime_execution_approval_service, firewall_no_customer_runtime_execution_evidence_service


def build_phase6_final_acceptance_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    text = (root / "docs" / "PHASE_STATUS.md").read_text(encoding="utf-8") if (root / "docs" / "PHASE_STATUS.md").exists() else ""
    blockers=[]
    if not text: blockers.append("docs/PHASE_STATUS.md missing")
    current_state_preserved = "## Current State" in text and "current_working_phase: Phase 6 — Firewall Planner" in text
    farm5 = "farm5 synced to 0.1.96" in text and "mpf --version: 0.1.96" in text
    approval = firewall_no_customer_runtime_execution_approval_service.build_no_customer_runtime_execution_approval_report(cfg,repo_root=root)
    controlled = firewall_no_customer_runtime_execution_evidence_service.build_no_customer_runtime_execution_evidence_report(cfg,repo_root=root)
    proposal = firewall_manual_canary_customer_proposal_service.build_manual_canary_customer_proposal_report(cfg,repo_root=root)
    acceptance = firewall_manual_canary_customer_acceptance_readiness_service.build_manual_canary_customer_acceptance_readiness_report(cfg,repo_root=root)
    server_ev = firewall_manual_canary_customer_server_evidence_service.build_manual_canary_customer_server_evidence_report(cfg,repo_root=root)
    readiness = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg,repo_root=root,include_manual_canary_summary=False,include_runtime_approval_summary=False,include_runtime_evidence_summary=False)
    abuse_ok = "normal -> over_tracking -> over_grace -> hard" in (root / "docs" / "AI_PHASE_6_TASK.md").read_text(encoding="utf-8")
    if not current_state_preserved: blockers.append("Current State missing or changed")
    if not farm5: blockers.append("farm5 0.1.96 sync evidence missing")
    if server_ev.get("final_decision")!="BLOCKED": blockers.append("manual canary server evidence is not BLOCKED")
    if server_ev.get("execution_allowed",False): blockers.append("manual canary server evidence execution_allowed true")
    blockers.append("manual canary actual execution evidence missing")
    blockers.append("manual canary final gate not accepted")

    report={"component":"phase6_final_acceptance_readiness","phase":"Phase 6 — Firewall Planner","gate_type":"phase6_final_acceptance_readiness","final_decision":"BLOCKED","acceptance_status":"PHASE6_NOT_ACCEPTED","authorization_status":"FINAL_ACCEPTANCE_READY_CHECK_DEFINED_NOT_GRANTED","inspection_only":True,"report_only":True,"preflight_only":True,"dry_run":True,"execution_allowed":False,"phase6_acceptance_allowed":False,"customer_nat_authorized":False,"customer_firewall_rules_authorized":False,"production_traffic_authorized":False,"operator_approval_required":True,"fresh_farm5_final_acceptance_evidence_required":True,"separate_phase6_acceptance_pr_required":True,
    "current_state_preserved":current_state_preserved,"farm5_0_1_96_sync_evidence_present":farm5,"no_customer_runtime_approval_done":approval.get("final_decision")=="BLOCKED","controlled_no_customer_runtime_evidence_done":controlled.get("final_decision")=="BLOCKED","manual_canary_proposal_done":proposal.get("final_decision")=="BLOCKED","manual_canary_acceptance_readiness_done":acceptance.get("final_decision")=="BLOCKED","manual_canary_server_evidence_present":bool(server_ev),"manual_canary_server_evidence_blocked":server_ev.get("final_decision")=="BLOCKED","manual_canary_server_evidence_execution_disallowed":not server_ev.get("execution_allowed",False),"manual_canary_actual_execution_missing":True,"manual_canary_final_gate_not_accepted":True,"apply_gate_readiness_blocked":readiness.get("final_decision")=="BLOCKED","phase_gate_firewall_apply_disallowed":"firewall_apply_allowed: no" in text,"phase_gate_production_traffic_none":"production_traffic: none" in text,"phase_gate_abuse_automation_disallowed":"abuse_automation_allowed: no" in text,"abuse_invariant_preserved":abuse_ok,"phase7_not_started":True,"phase8_not_started":True,"phase6_final_acceptance_blocked":True}
    for k in ["live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation","db_apply_record_write_allowed","db_apply_record_written","filesystem_write_executed","restore_point_write_allowed","restore_point_written","lock_acquisition_allowed","lock_acquired","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","usage_automation_allowed","abuse_automation_allowed_runtime","ui_allowed_runtime","telegram_allowed_runtime"]:
        report[k]=False
    report["phase6_final_acceptance_readiness_checklist"]=[]
    report["blockers"]=blockers
    report["errors"]=[]
    return report
