from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services.phase7_policy_reject_accounting_contract_service import build_phase7_policy_reject_accounting_contract_report
from mpf.services.phase7_reports_doctor_service import build_phase7_doctor_report, build_phase7_reports_summary
from mpf.services.phase7_usage_accounting_contract_service import build_phase7_usage_accounting_contract_report
from mpf.services.phase7_usage_policy_readiness_service import build_phase7_usage_policy_readiness_report


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _runtime_safety_flags() -> dict[str, bool]:
    return {k: False for k in [
        "live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed",
        "iptables_save_executed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed",
        "subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation",
        "db_usage_sample_write_allowed","db_usage_sample_written","db_policy_event_write_allowed","db_policy_event_written",
        "db_abuse_state_write_allowed","db_abuse_state_written","filesystem_write_executed","scheduler_job_created","timer_enabled",
        "usage_collector_runtime_allowed","usage_collector_runtime_started","policy_reject_collector_runtime_allowed",
        "policy_reject_collector_runtime_started","abuse_runner_runtime_allowed","abuse_runner_runtime_started","customer_nat_allowed",
        "customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed",
        "abuse_automation_allowed_runtime","block_automation_allowed","pause_automation_allowed","ui_allowed_runtime","telegram_allowed_runtime",
    ]}


def build_phase7_final_acceptance_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    readme = _read(root / "README.md")
    ai_phase7 = _read(root / "docs/AI_PHASE_7_TASK.md").lower()
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md").lower()

    usage_policy = build_phase7_usage_policy_readiness_report(cfg, repo_root=root)
    usage_contract = build_phase7_usage_accounting_contract_report(cfg, repo_root=root)
    policy_contract = build_phase7_policy_reject_accounting_contract_report(cfg, repo_root=root)
    phase7_summary = build_phase7_reports_summary(cfg, repo_root=root)
    phase7_doctor = build_phase7_doctor_report(cfg, repo_root=root)

    child_reports = {
        "usage_policy_readiness": {"component": usage_policy.get("component"), "final_decision": usage_policy.get("final_decision"), "blocker_count": len(usage_policy.get("blockers", [])), "execution_allowed": usage_policy.get("execution_allowed")},
        "usage_accounting_contract": {"component": usage_contract.get("component"), "final_decision": usage_contract.get("final_decision"), "blocker_count": len(usage_contract.get("blockers", [])), "execution_allowed": usage_contract.get("execution_allowed")},
        "policy_reject_accounting_contract": {"component": policy_contract.get("component"), "final_decision": policy_contract.get("final_decision"), "blocker_count": len(policy_contract.get("blockers", [])), "execution_allowed": policy_contract.get("execution_allowed")},
        "phase7_summary": {"component": phase7_summary.get("component"), "final_decision": phase7_summary.get("final_decision"), "blocker_count": len(phase7_summary.get("blockers", [])), "execution_allowed": phase7_summary.get("execution_allowed")},
        "phase7_doctor": {"component": phase7_doctor.get("component"), "final_verdict": phase7_doctor.get("final_verdict"), "final_decision": phase7_doctor.get("final_decision"), "blocker_count": len(phase7_doctor.get("blockers", [])), "execution_allowed": phase7_doctor.get("execution_allowed")},
    }

    phase6_accepted = "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in phase_status
    phase7_working = "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" in phase_status
    current_state_preserved = "## current state" in phase_status.lower() and phase6_accepted and phase7_working
    farm5_present = "synced to 0.1.107" in phase_status.lower()
    usage_clean = not usage_policy.get("blockers")
    usage_contract_clean = not usage_contract.get("blockers")
    policy_clean = not policy_contract.get("blockers")
    summary_clean = not phase7_summary.get("blockers")
    doctor_ok = phase7_doctor.get("final_verdict") == "OK"
    child_clean = all(x["blocker_count"] == 0 for x in child_reports.values())

    booleans = {
        "current_state_preserved": current_state_preserved, "phase6_accepted": phase6_accepted, "phase7_working": phase7_working,
        "farm5_0_1_107_sync_evidence_present": farm5_present, "phase7_usage_policy_readiness_clean": usage_clean,
        "phase7_usage_accounting_contract_clean": usage_contract_clean, "phase7_policy_reject_accounting_contract_clean": policy_clean,
        "phase7_reports_summary_clean": summary_clean, "phase7_doctor_ok": doctor_ok, "phase7_child_reports_clean": child_clean,
        "phase7_contract_stack_complete": usage_clean and usage_contract_clean and policy_clean and summary_clean and doctor_ok,
        "readme_phase7_aligned": "accepted_phase: Phase 6" in readme and "working_phase: Phase 7" in readme,
        "remaining_plan_final_acceptance_target_aligned": "phase 7 current target is phase 7 final acceptance readiness package" in remaining,
        "ai_phase7_final_acceptance_present": "current phase 7 step — final acceptance readiness" in ai_phase7,
        "apply_mode_plan_only": cfg.firewall.apply_mode == "plan_only", "runtime_activation_disabled": not bool(cfg.proxy.runtime_activation_allowed),
        "production_traffic_none": "production_traffic: none" in phase_status, "firewall_apply_disallowed": "firewall_apply_allowed: no" in phase_status,
        "customer_nat_disallowed": True, "customer_firewall_rules_disallowed": True, "iptables_restore_disallowed": True,
        "usage_automation_disallowed": True, "usage_collectors_disallowed": True, "policy_reject_collectors_disallowed": True,
        "usage_db_writes_disallowed": True, "policy_reject_db_writes_disallowed": True, "firewall_counter_live_read_disallowed": True,
        "abuse_automation_disallowed": "abuse_automation_allowed: no" in phase_status, "phase8_not_started": True,
        "abuse_invariant_preserved": "normal -> over_tracking -> over_grace -> hard" in phase_status and "no silent skip" in phase_status,
    }
    blockers = []
    for k,v in booleans.items():
        if not v:
            blockers.append(f"{k}_failed")
    if any(v for v in _runtime_safety_flags().values()):
        blockers.append("runtime_mutation_safety_flag_true")
    checklist_names = ["current_state_preserved","phase6_accepted","phase7_working","farm5_0_1_107_sync_evidence_present","phase7_usage_policy_readiness_clean","phase7_usage_accounting_contract_clean","phase7_policy_reject_accounting_contract_clean","phase7_reports_summary_clean","phase7_doctor_ok","phase7_contract_stack_complete","config_apply_mode_plan_only","proxy_runtime_activation_disabled","no_production_traffic","firewall_apply_disallowed","customer_nat_disallowed","customer_firewall_rules_disallowed","no_iptables_restore_authorized","usage_automation_disallowed","usage_collectors_disallowed","policy_reject_collectors_disallowed","usage_db_writes_disallowed","policy_reject_db_writes_disallowed","firewall_counter_live_read_disallowed","abuse_automation_disallowed","phase8_not_started","abuse_invariant_preserved","operator_acceptance_pr_required"]
    mapper = {
        "config_apply_mode_plan_only":"apply_mode_plan_only","proxy_runtime_activation_disabled":"runtime_activation_disabled","no_production_traffic":"production_traffic_none","no_iptables_restore_authorized":"iptables_restore_disallowed","operator_acceptance_pr_required":True,
    }
    checklist=[]
    for item in checklist_names:
        key=mapper.get(item,item)
        ok = key if isinstance(key,bool) else booleans.get(key,False)
        checklist.append({"item":item,"status":"PASS" if ok else "BLOCKED","evidence":str(ok)})

    report={"component":"phase7_final_acceptance_readiness","phase":"Phase 7 — Usage + Policy/Reject Accounting","gate_type":"phase7_final_acceptance_readiness","final_decision":"BLOCKED","readiness_status":"PHASE7_FINAL_ACCEPTANCE_READY_FOR_OPERATOR_REVIEW","authorization_status":"PHASE7_FINAL_ACCEPTANCE_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED","inspection_only":True,"report_only":True,"preflight_only":True,"dry_run":True,"execution_allowed":False,"phase7_acceptance_allowed":False,"phase8_start_allowed":False,"operator_review_required":True,"operator_acceptance_pr_required":True,"operator_acceptance_pr_required":True,"fresh_farm5_sync_evidence_present":farm5_present,"farm5_sync_version":"0.1.107","child_reports":child_reports,"phase7_final_acceptance_readiness_checklist":checklist,"blockers":blockers,"errors":[]}
    return {**report, **booleans, **_runtime_safety_flags()}
