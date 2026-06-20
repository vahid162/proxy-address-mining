from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services.phase8_abuse_state_machine_contract_service import (
    build_phase8_abuse_state_machine_contract_report,
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def build_phase8_abuse_evidence_reporting_contract_report(
    cfg: MPFConfig,
    repo_root: Path | None = None,
) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    ai_rules = _read(root / "docs/AI_CODING_RULES.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")

    state_machine = build_phase8_abuse_state_machine_contract_report(cfg, repo_root=root)
    phase7_accepted = "current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in phase_status
    phase8_working = "current_working_phase: Phase 8 — Abuse 1h Core planning/readiness" in phase_status

    bools = {
        "current_state_preserved": phase7_accepted and phase8_working,
        "phase7_accepted": phase7_accepted,
        "phase8_working": phase8_working,
        "phase8_planning_only": True,
        "farm5_0_1_110_sync_evidence_present": "synced to 0.1.110" in phase_status,
        "no_farm5_0_1_111_sync_evidence_claimed": "synced to 0.1.111" not in phase_status,
        "no_farm5_0_1_112_sync_evidence_claimed": "synced to 0.1.112" not in phase_status,
        "state_machine_contract_present": state_machine.get("component") == "phase8_abuse_state_machine_contract",
        "state_machine_contract_fail_closed": state_machine.get("final_decision") == "BLOCKED" and not bool(state_machine.get("execution_allowed")),
        "ai_phase8_task_present": "Current Phase 8 Step — Abuse Evidence/Reporting Contract" in ai_phase8,
        "remaining_plan_evidence_reporting_target_aligned": "Current target is Phase 8 abuse evidence/reporting contract package." in remaining,
        "phase_status_current_gate_aligned": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase8_task_current_gate_aligned": "Abuse Evidence/Reporting Contract" in ai_phase8,
        "ai_coding_rules_current_gate_aligned": "Phase 8 evidence/reporting contract" in ai_rules,
        "apply_mode_plan_only": cfg.firewall.apply_mode == "plan_only",
        "runtime_activation_disabled": cfg.proxy.runtime_activation_allowed is False,
        "production_traffic_none": True,
        "firewall_apply_disallowed": True,
        "customer_nat_disallowed": True,
        "customer_firewall_rules_disallowed": True,
        "iptables_restore_disallowed": True,
        "abuse_automation_disallowed": True,
        "abuse_runner_disallowed": True,
        "abuse_state_db_reads_disallowed": True,
        "abuse_state_db_writes_disallowed": True,
        "abuse_event_db_writes_disallowed": True,
        "usage_sample_db_reads_disallowed": True,
        "usage_sample_db_writes_disallowed": True,
        "policy_event_db_reads_disallowed": True,
        "policy_event_db_writes_disallowed": True,
        "conntrack_live_read_disallowed": True,
        "firewall_counter_live_read_disallowed": True,
        "hard_block_disallowed": True,
        "soft_block_disallowed": True,
        "pause_automation_disallowed": True,
        "ui_disallowed": True,
        "telegram_disallowed": True,
        "abuse_invariant_preserved": True,
        "state_path_normal_over_tracking_over_grace_hard": True,
        "sustained_abuse_window_3600_seconds": True,
        "farms_over_alone_does_not_harden": True,
        "worker_over_alone_does_not_harden": True,
        "all_active_customers_coverage_required": True,
        "missing_evidence_report_required": True,
        "stale_evidence_report_required": True,
        "no_silent_skip_required": True,
    }

    blockers=[f"{k}_missing_or_failed" for k,v in bools.items() if not v]
    false_flags = {k: False for k in ["live_firewall_read_allowed","live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_save_executed","iptables_restore_allowed","iptables_restore_executed","conntrack_live_read_executed","firewall_counter_live_read_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_read_executed","db_mutation","db_customer_read_allowed","db_customer_read_executed","db_usage_sample_read_allowed","db_usage_sample_read_executed","db_usage_sample_write_allowed","db_usage_sample_written","db_policy_event_read_allowed","db_policy_event_read_executed","db_policy_event_write_allowed","db_policy_event_written","db_abuse_state_read_allowed","db_abuse_state_read_executed","db_abuse_state_write_allowed","db_abuse_state_written","db_abuse_event_write_allowed","db_abuse_event_written","filesystem_write_executed","scheduler_job_created","timer_enabled","usage_collector_runtime_allowed","usage_collector_runtime_started","policy_reject_collector_runtime_allowed","policy_reject_collector_runtime_started","abuse_runner_runtime_allowed","abuse_runner_runtime_started","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","abuse_automation_allowed_runtime","hard_block_allowed","hard_block_applied","soft_block_allowed","soft_block_applied","pause_automation_allowed","pause_applied","ui_allowed_runtime","telegram_allowed_runtime"]}

    checklist_items=["current_state_preserved","phase7_accepted","phase8_working","farm5_0_1_110_sync_evidence_present","no_farm5_0_1_111_sync_evidence_claimed","no_farm5_0_1_112_sync_evidence_claimed","state_machine_contract_present","state_machine_contract_fail_closed","ai_phase8_task_present","remaining_plan_evidence_reporting_target_aligned","phase_status_current_gate_aligned","phase8_task_current_gate_aligned","ai_coding_rules_current_gate_aligned","evidence_reporting_contract_defined","evidence_source_contract_defined","evidence_snapshot_contract_defined","customer_evaluation_report_contract_defined","coverage_report_contract_defined","missing_evidence_report_contract_defined","operator_summary_contract_defined","failure_mode_report_contract_defined","all_active_customers_coverage_required","missing_evidence_report_required","stale_evidence_report_required","no_silent_skip_required","farms_over_alone_does_not_harden","worker_over_alone_does_not_harden","sustained_abuse_window_3600_seconds","config_apply_mode_plan_only","proxy_runtime_activation_disabled","no_production_traffic","firewall_apply_disallowed","customer_nat_disallowed","customer_firewall_rules_disallowed","no_iptables_restore_authorized","abuse_automation_disallowed","abuse_runner_disallowed","abuse_db_reads_disallowed","abuse_db_writes_disallowed","usage_policy_db_reads_writes_disallowed","live_conntrack_firewall_reads_disallowed","hard_block_disallowed","soft_block_disallowed","pause_automation_disallowed","separate_phase8_dry_run_evaluator_pr_required","fresh_farm5_sync_evidence_required_before_acceptance"]
    mapping={"evidence_reporting_contract_defined":True,"evidence_source_contract_defined":True,"evidence_snapshot_contract_defined":True,"customer_evaluation_report_contract_defined":True,"coverage_report_contract_defined":True,"missing_evidence_report_contract_defined":True,"operator_summary_contract_defined":True,"failure_mode_report_contract_defined":True,"config_apply_mode_plan_only":bools["apply_mode_plan_only"],"proxy_runtime_activation_disabled":bools["runtime_activation_disabled"],"no_production_traffic":bools["production_traffic_none"],"no_iptables_restore_authorized":bools["iptables_restore_disallowed"],"abuse_db_reads_disallowed":bools["abuse_state_db_reads_disallowed"],"abuse_db_writes_disallowed":bools["abuse_state_db_writes_disallowed"] and bools["abuse_event_db_writes_disallowed"],"usage_policy_db_reads_writes_disallowed":all([bools["usage_sample_db_reads_disallowed"],bools["usage_sample_db_writes_disallowed"],bools["policy_event_db_reads_disallowed"],bools["policy_event_db_writes_disallowed"]]),"live_conntrack_firewall_reads_disallowed":bools["conntrack_live_read_disallowed"] and bools["firewall_counter_live_read_disallowed"],"separate_phase8_dry_run_evaluator_pr_required":True,"fresh_farm5_sync_evidence_required_before_acceptance":True}
    checklist=[{"item":i,"status":"PASS" if mapping.get(i,bools.get(i,True)) else "BLOCKED","evidence":i} for i in checklist_items]

    return {
        "component":"phase8_abuse_evidence_reporting_contract","phase":"Phase 8 — Abuse 1h Core","gate_type":"phase8_abuse_evidence_reporting_contract","final_decision":"BLOCKED","contract_status":"ABUSE_EVIDENCE_REPORTING_CONTRACT_DEFINED_NOT_ACCEPTED","authorization_status":"PHASE8_ABUSE_EVIDENCE_REPORTING_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED","inspection_only":True,"report_only":True,"preflight_only":True,"dry_run":True,"execution_allowed":False,"phase8_acceptance_allowed":False,
        "state_machine_contract_present":True,"state_machine_contract_fail_closed":True,"evidence_reporting_contract_defined":True,"evidence_source_contract_defined":True,"evidence_snapshot_contract_defined":True,"coverage_report_contract_defined":True,"missing_evidence_report_contract_defined":True,"operator_summary_contract_defined":True,"failure_mode_report_contract_defined":True,"customer_evaluation_report_contract_defined":True,"future_dry_run_evaluator_pr_required":True,"fresh_farm5_sync_evidence_required_before_acceptance":True,"no_server_sync_evidence_for_0_1_112":True,
        "abuse_runner_authorized":False,"abuse_automation_authorized":False,"abuse_state_db_reads_authorized":False,"abuse_state_db_writes_authorized":False,"abuse_event_db_writes_authorized":False,"usage_sample_db_reads_authorized":False,"usage_sample_db_writes_authorized":False,"policy_event_db_reads_authorized":False,"policy_event_db_writes_authorized":False,"conntrack_live_read_authorized":False,"firewall_counter_live_read_authorized":False,"iptables_save_authorized":False,"iptables_restore_authorized":False,"hard_block_authorized":False,"soft_block_authorized":False,"pause_automation_authorized":False,"firewall_apply_authorized":False,"customer_nat_authorized":False,"customer_firewall_rules_authorized":False,"production_traffic_authorized":False,"ui_authorized":False,"telegram_authorized":False,
        "operator_review_required":True,"separate_phase8_dry_run_evaluator_pr_required":True,
        "abuse_evidence_reporting_contract": {"evidence_sources":{"allowed_future_sources":["flow_sessions","usage_samples","policy_events","worker_events","conntrack_snapshot","firewall_counter_snapshot"],"allowed_in_this_pr":["repository_docs","static_contracts","config_read_only"],"forbidden_in_this_pr":["live_conntrack","live_iptables","live_firewall_counters","db_customer_reads","db_abuse_reads","db_writes","runtime_jobs","abuse_runner"]},"evidence_snapshot_shape":{"required_fields":["customer_id","lane_id","customer_key","port","policy_miners","policy_farms","active_sessions","hot_sessions","unique_source_ips","unique_workers","evidence_source","observed_at","evidence_status","confidence","missing_reasons"],"status_values":["complete","partial","missing","stale","exempt","evaluation_blocked"]},"customer_evaluation_report_shape":{"required_fields":["customer_id","lane_id","port","current_state","proposed_state","miner_over","farms_over","worker_over","sustained_over_seconds","threshold_seconds","grace_seconds","transition_allowed","hardening_allowed","evidence_status","blockers","warnings"],"transition_allowed_in_this_pr":False,"hardening_allowed_in_this_pr":False},"coverage_report_shape":{"required_fields":["enabled_lane_count","active_customer_count","evaluated_customer_count","missing_evidence_customer_count","exempt_customer_count","silent_skip_count","coverage_complete","blockers"],"silent_skip_allowed":False,"all_active_customers_required":True},"missing_evidence_report_shape":{"required_fields":["customer_id","lane_id","port","missing_source","missing_reason","severity","action"],"missing_evidence_hardens":False,"missing_evidence_records_failure_in_future":True},"operator_summary_shape":{"required_fields":["final_decision","execution_allowed","abuse_runner_authorized","customers_total","customers_over_tracking","customers_over_grace","customers_hard","customers_missing_evidence","coverage_complete","blockers","warnings"]},"failure_modes":{"evidence_missing_does_not_harden":True,"stale_evidence_does_not_harden":True,"partial_evidence_does_not_harden_without_policy":True,"db_unavailable_does_not_harden":True,"live_counter_unavailable_does_not_harden":True,"farms_over_alone_does_not_harden":True,"worker_over_alone_does_not_harden":True},"future_acceptance_criteria":["every active customer in every enabled lane appears in coverage report","no silent skip exists","missing evidence creates explicit report entry","stale evidence creates explicit report entry","farms-over alone is report-only and never hardens","worker-over alone is report-only and never hardens","sustained miner-abuse evidence is required before hard","future DB/runtime evaluator remains separately gated"]},
        **bools,
        "phase8_abuse_evidence_reporting_contract_checklist":checklist,
        "blockers":blockers,
        "errors":[],
        **false_flags,
    }
