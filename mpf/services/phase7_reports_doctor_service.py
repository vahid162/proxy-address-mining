from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services.phase7_policy_reject_accounting_contract_service import (
    build_phase7_policy_reject_accounting_contract_report,
)
from mpf.services.phase7_usage_accounting_contract_service import (
    build_phase7_usage_accounting_contract_report,
)
from mpf.services.phase7_usage_policy_readiness_service import (
    build_phase7_usage_policy_readiness_report,
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _base_safety_flags() -> dict[str, bool]:
    return {k: False for k in [
        "live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed",
        "iptables_save_executed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed",
        "subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation",
        "db_usage_sample_write_allowed","db_usage_sample_written","db_policy_event_write_allowed","db_policy_event_written",
        "filesystem_write_executed","scheduler_job_created","timer_enabled","usage_collector_runtime_allowed",
        "usage_collector_runtime_started","policy_reject_collector_runtime_allowed","policy_reject_collector_runtime_started",
        "customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed",
        "production_traffic_changed","abuse_automation_allowed_runtime","block_automation_allowed","pause_automation_allowed",
        "ui_allowed_runtime","telegram_allowed_runtime",
    ]}


def build_phase7_reports_summary(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    readme = _read(root / "README.md")
    ai_phase7 = _read(root / "docs/AI_PHASE_7_TASK.md").lower()
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md").lower()

    usage_policy = build_phase7_usage_policy_readiness_report(cfg, repo_root=root)
    usage_contract = build_phase7_usage_accounting_contract_report(cfg, repo_root=root)
    policy_contract = build_phase7_policy_reject_accounting_contract_report(cfg, repo_root=root)

    current_state_present = "## current state" in phase_status.lower()
    phase6_accepted = "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in phase_status
    phase7_working = "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" in phase_status
    current_state_preserved = current_state_present and phase6_accepted and phase7_working
    usage_policy_clean = bool(usage_policy) and not usage_policy.get("blockers")
    usage_contract_clean = bool(usage_contract) and not usage_contract.get("blockers")
    policy_contract_clean = bool(policy_contract) and not policy_contract.get("blockers")
    farm5_present = "synced to 0.1.104" in phase_status
    no_fabricated_sync = all(f"synced to {v}" not in phase_status.lower() for v in ("0.1.105", "0.1.106", "0.1.107"))
    readme_phase7_aligned = "accepted_phase: Phase 6" in readme and "working_phase: Phase 7" in readme
    remaining_aligned = "current target is phase 7 read-only reports/doctor package" in remaining
    ai_reports_doctor_present = "current phase 7 step — read-only reports/doctor" in ai_phase7
    apply_mode = cfg.firewall.apply_mode == "plan_only"
    runtime_disabled = not bool(cfg.proxy.runtime_activation_allowed)

    blockers: list[str] = []
    if not current_state_present: blockers.append("phase_status_current_state_missing")
    if not current_state_preserved: blockers.append("current_state_changed_away_from_phase6_accepted_phase7_working")
    if not farm5_present: blockers.append("latest_recorded_farm5_sync_evidence_missing")
    if not no_fabricated_sync: blockers.append("fabricated_newer_farm5_sync_evidence_present")
    if not usage_policy_clean: blockers.append("usage_policy_readiness_report_has_blockers")
    if not usage_contract_clean: blockers.append("usage_accounting_contract_report_has_blockers")
    if not policy_contract_clean: blockers.append("policy_reject_accounting_contract_report_has_blockers")
    if not readme_phase7_aligned: blockers.append("readme_not_aligned_to_phase7")
    if not ai_reports_doctor_present: blockers.append("ai_phase7_task_missing_reports_doctor_section")
    if not remaining_aligned: blockers.append("remaining_plan_reports_doctor_target_not_aligned")
    if not apply_mode: blockers.append("firewall_apply_mode_not_plan_only")
    if not runtime_disabled: blockers.append("proxy_runtime_activation_enabled")

    summary = {
        "component":"phase7_reports_summary","phase":"Phase 7 — Usage + Policy/Reject Accounting","gate_type":"phase7_reports_summary",
        "final_decision":"BLOCKED","summary_status":"PHASE7_REPORTS_SUMMARY_DEFINED_NOT_ACCEPTED",
        "authorization_status":"PHASE7_REPORTS_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED","inspection_only":True,"report_only":True,
        "preflight_only":True,"dry_run":True,"execution_allowed":False,"phase7_acceptance_allowed":False,
        "production_traffic_authorized":False,"firewall_apply_authorized":False,"iptables_restore_authorized":False,
        "customer_nat_authorized":False,"customer_firewall_rules_authorized":False,"usage_automation_authorized":False,
        "usage_collectors_authorized":False,"policy_reject_collectors_authorized":False,"abuse_automation_authorized":False,
        "phase8_start_allowed":False,"operator_review_required":True,"batched_farm5_sync_required_after_merge":True,
        "fresh_farm5_sync_evidence_required_before_phase7_acceptance":True,
        "current_state_preserved":current_state_preserved,"phase6_accepted":phase6_accepted,"phase7_working":phase7_working,
        "usage_policy_readiness_present": bool(usage_policy),"usage_policy_readiness_clean":usage_policy_clean,
        "usage_accounting_contract_present": bool(usage_contract),"usage_accounting_contract_clean":usage_contract_clean,
        "policy_reject_accounting_contract_present": bool(policy_contract),"policy_reject_accounting_contract_clean":policy_contract_clean,
        "latest_recorded_farm5_sync_evidence_present":farm5_present,"latest_recorded_farm5_sync_version_is_0_1_104":farm5_present,
        "no_fabricated_0_1_105_or_0_1_106_sync_evidence":no_fabricated_sync,"readme_phase7_aligned":readme_phase7_aligned,
        "remaining_plan_reports_doctor_target_aligned":remaining_aligned,"ai_phase7_reports_doctor_present":ai_reports_doctor_present,
        "apply_mode_plan_only":apply_mode,"runtime_activation_disabled":runtime_disabled,"production_traffic_none":"production_traffic: none" in phase_status,
        "firewall_apply_disallowed":"firewall_apply_allowed: no" in phase_status,"customer_nat_disallowed":True,
        "customer_firewall_rules_disallowed":True,"iptables_restore_disallowed":True,"usage_automation_disallowed":True,
        "usage_collectors_disallowed":True,"policy_reject_collectors_disallowed":True,"abuse_automation_disallowed":"abuse_automation_allowed: no" in phase_status,
        "phase8_not_started":True,"abuse_invariant_preserved":"normal -> over_tracking -> over_grace -> hard" in phase_status,
        "blockers":blockers,"errors":[],
    }
    return {**summary, **_base_safety_flags()}


def build_phase7_doctor_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    summary = build_phase7_reports_summary(cfg, repo_root=repo_root)
    usage_policy = build_phase7_usage_policy_readiness_report(cfg, repo_root=repo_root)
    usage_contract = build_phase7_usage_accounting_contract_report(cfg, repo_root=repo_root)
    policy_contract = build_phase7_policy_reject_accounting_contract_report(cfg, repo_root=repo_root)

    child_reports = {
        "usage_policy_readiness": {
            "component": usage_policy.get("component"),"final_decision": usage_policy.get("final_decision"),
            "blocker_count": len(usage_policy.get("blockers", [])),"blockers": usage_policy.get("blockers", []),
            "execution_allowed": usage_policy.get("execution_allowed"),"production_traffic_authorized": usage_policy.get("production_traffic_authorized"),
            "firewall_apply_authorized": usage_policy.get("firewall_apply_authorized"),"customer_nat_authorized": usage_policy.get("customer_nat_authorized"),
            "abuse_automation_authorized": usage_policy.get("abuse_automation_authorized"),
        },
        "usage_accounting_contract": {
            "component": usage_contract.get("component"),"final_decision": usage_contract.get("final_decision"),
            "blocker_count": len(usage_contract.get("blockers", [])),"blockers": usage_contract.get("blockers", []),
            "execution_allowed": usage_contract.get("execution_allowed"),"usage_collector_runtime_authorized": usage_contract.get("usage_collector_runtime_authorized"),
            "usage_db_writes_authorized": usage_contract.get("usage_db_writes_authorized"),"firewall_counter_live_read_authorized": usage_contract.get("firewall_counter_live_read_authorized"),
        },
        "policy_reject_accounting_contract": {
            "component": policy_contract.get("component"),"final_decision": policy_contract.get("final_decision"),
            "blocker_count": len(policy_contract.get("blockers", [])),"blockers": policy_contract.get("blockers", []),
            "execution_allowed": policy_contract.get("execution_allowed"),"policy_reject_collector_runtime_authorized": policy_contract.get("policy_reject_collector_runtime_authorized"),
            "policy_reject_db_writes_authorized": policy_contract.get("policy_reject_db_writes_authorized"),"firewall_counter_live_read_authorized": policy_contract.get("firewall_counter_live_read_authorized"),
        },
    }
    all_children_clean = all(v["blocker_count"] == 0 for v in child_reports.values())
    flags_false = not any(summary[k] for k in [
        "production_traffic_authorized","firewall_apply_authorized","customer_nat_authorized","customer_firewall_rules_authorized",
        "usage_automation_authorized","usage_collectors_authorized","policy_reject_collectors_authorized","abuse_automation_authorized",
        "execution_allowed","phase7_acceptance_allowed","phase8_start_allowed",
    ])
    final_verdict = "OK" if all_children_clean and flags_false and summary["final_decision"] == "BLOCKED" else "BLOCKED"

    checks = [
        ("current_state_preserved", summary["current_state_preserved"]),("phase6_accepted", summary["phase6_accepted"]),("phase7_working", summary["phase7_working"]),
        ("usage_policy_readiness_clean", summary["usage_policy_readiness_clean"]),("usage_accounting_contract_clean", summary["usage_accounting_contract_clean"]),
        ("policy_reject_accounting_contract_clean", summary["policy_reject_accounting_contract_clean"]),("latest_recorded_farm5_sync_evidence_present", summary["latest_recorded_farm5_sync_evidence_present"]),
        ("no_fabricated_newer_sync_evidence", summary["no_fabricated_0_1_105_or_0_1_106_sync_evidence"]),("config_apply_mode_plan_only", summary["apply_mode_plan_only"]),
        ("proxy_runtime_activation_disabled", summary["runtime_activation_disabled"]),("no_production_traffic", summary["production_traffic_none"]),
        ("firewall_apply_disallowed", summary["firewall_apply_disallowed"]),("customer_nat_disallowed", summary["customer_nat_disallowed"]),
        ("customer_firewall_rules_disallowed", summary["customer_firewall_rules_disallowed"]),("no_iptables_restore_authorized", summary["iptables_restore_disallowed"]),
        ("usage_automation_disallowed", summary["usage_automation_disallowed"]),("usage_collectors_disallowed", summary["usage_collectors_disallowed"]),
        ("policy_reject_collectors_disallowed", summary["policy_reject_collectors_disallowed"]),("abuse_automation_disallowed", summary["abuse_automation_disallowed"]),
        ("phase8_not_started", summary["phase8_not_started"]),("abuse_invariant_preserved", summary["abuse_invariant_preserved"]),
        ("batched_farm5_sync_required_after_merge", True),("fresh_farm5_sync_evidence_required_before_phase7_acceptance", True),
    ]
    checklist = [{"item":i,"status":"PASS" if ok else "BLOCKED","evidence":str(ok)} for i,ok in checks]
    blockers = list(summary.get("blockers", []))

    report = {
        "component":"phase7_doctor","phase":"Phase 7 — Usage + Policy/Reject Accounting","gate_type":"phase7_doctor",
        "final_verdict":final_verdict,"final_decision":"BLOCKED","doctor_status":"PHASE7_DOCTOR_REPORT_ONLY",
        "authorization_status":"PHASE7_DOCTOR_RUNTIME_NOT_AUTHORIZED","inspection_only":True,"report_only":True,
        "preflight_only":True,"dry_run":True,"execution_allowed":False,"phase7_acceptance_allowed":False,
        "production_traffic_authorized":False,"firewall_apply_authorized":False,"iptables_restore_authorized":False,
        "customer_nat_authorized":False,"customer_firewall_rules_authorized":False,"usage_automation_authorized":False,
        "usage_collectors_authorized":False,"policy_reject_collectors_authorized":False,"abuse_automation_authorized":False,
        "phase8_start_allowed":False,"operator_review_required":True,"batched_farm5_sync_required_after_merge":True,
        "usage_policy_readiness_clean":summary["usage_policy_readiness_clean"],"usage_accounting_contract_clean":summary["usage_accounting_contract_clean"],
        "policy_reject_accounting_contract_clean":summary["policy_reject_accounting_contract_clean"],
        "latest_recorded_farm5_sync_evidence_present":summary["latest_recorded_farm5_sync_evidence_present"],
        "no_fabricated_0_1_105_or_0_1_106_sync_evidence":summary["no_fabricated_0_1_105_or_0_1_106_sync_evidence"],
        "child_reports":child_reports,"phase7_doctor_checklist":checklist,"blockers":blockers,"errors":[],
    }
    return {**report, **_base_safety_flags()}
