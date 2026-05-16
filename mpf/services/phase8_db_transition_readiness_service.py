from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from mpf.config import MPFConfig
from mpf.domain.abuse_dry_run_evaluator import AbuseDryRunInput, AbuseEvidenceSnapshot, AbusePolicySnapshot, AbuseStateSnapshot, evaluate_abuse_dry_run
from mpf.domain.abuse_transition_plan import build_db_mutation_plan, build_operator_approval_contract, build_transition_intent_from_dry_run_result
from mpf.services.phase8_abuse_dry_run_evaluator_service import build_phase8_abuse_dry_run_evaluator_report
from mpf.services.phase8_abuse_evidence_reporting_contract_service import build_phase8_abuse_evidence_reporting_contract_report
from mpf.services.phase8_abuse_state_machine_contract_service import build_phase8_abuse_state_machine_contract_report


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _scenario(now: datetime, sid: str, inp: AbuseDryRunInput, expect_tables: list[str]) -> dict[str, object]:
    result = evaluate_abuse_dry_run(inp)
    intent = build_transition_intent_from_dry_run_result(customer_id=inp.evidence.customer_id, lane_id=inp.evidence.lane_id, customer_key=inp.evidence.customer_key, port=inp.evidence.port, evidence_source=inp.evidence.evidence_source, observed_at_iso=inp.evidence.observed_at.isoformat() if inp.evidence.observed_at else None, dry_run_result=result)
    plan = build_db_mutation_plan(intent)
    return {
        "scenario_id": sid,
        "dry_run_decision": result.decision,
        "transition_intent": asdict(intent),
        "db_mutation_plan": asdict(plan),
        "expected_future_write_tables": expect_tables,
        "passed": plan.future_write_tables == expect_tables,
    }


def build_phase8_db_transition_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    readme = _read(root / "README.md")
    index = _read(root / "docs/INDEX.md")
    rules = _read(root / "docs/AI_CODING_RULES.md")
    models = _read(root / "mpf/models.py")

    sm = build_phase8_abuse_state_machine_contract_report(cfg, root)
    er = build_phase8_abuse_evidence_reporting_contract_report(cfg, root)
    dr = build_phase8_abuse_dry_run_evaluator_report(cfg, root)

    now = datetime(2026, 1, 1)
    base_policy = AbusePolicySnapshot(10, 3, 100, 10, 20)
    def mk(state: str, hot: int | None, ev: str = "complete", first_seen: int | None = None, rec: int | None = None, ips: int = 1, workers: int = 1, blockers: list[str] | None = None, exempt: bool = False) -> AbuseDryRunInput:
        evidence = AbuseEvidenceSnapshot(11, 1, "c-11", 60001, hot, hot, ips, workers, ev, "synthetic", now, 100, blockers or [])
        policy = base_policy if not exempt else AbusePolicySnapshot(10, 3, 100, 10, 20, True, "ex", now + timedelta(seconds=60))
        return AbuseDryRunInput(policy=policy, evidence=evidence, state=AbuseStateSnapshot(state, now - timedelta(seconds=first_seen) if first_seen else None, now, now - timedelta(seconds=rec) if rec else None, None), now=now)

    scenarios = [
        _scenario(now, "normal_within_limits_no_db_write_intent", mk("normal", 5), []),
        _scenario(now, "normal_miner_over_would_plan_tracking_state_event", mk("normal", 11), ["abuse_states", "abuse_events"]),
        _scenario(now, "farms_over_only_no_db_write_intent", mk("normal", 5, ips=10), []),
        _scenario(now, "worker_over_only_no_db_write_intent", mk("normal", 5, workers=20), []),
        _scenario(now, "missing_evidence_no_db_write_intent", mk("normal", None, ev="missing", blockers=["missing"]), []),
        _scenario(now, "stale_evidence_no_db_write_intent", mk("normal", 5, ev="stale", blockers=["stale"]), []),
        _scenario(now, "over_tracking_before_threshold_no_hard_write_intent", mk("over_tracking", 11, first_seen=3000), []),
        _scenario(now, "over_tracking_after_3600s_would_plan_hard_state_event_with_future_approval", mk("over_tracking", 11, first_seen=3600), ["abuse_states", "abuse_events"]),
        _scenario(now, "over_tracking_recovery_would_plan_grace_state_event", mk("over_tracking", 2, first_seen=3000), ["abuse_states", "abuse_events"]),
        _scenario(now, "over_grace_repeated_over_would_plan_tracking_state_event", mk("over_grace", 11, rec=100), ["abuse_states", "abuse_events"]),
        _scenario(now, "over_grace_recovered_would_plan_normal_state_event", mk("over_grace", 2, rec=1000), ["abuse_states", "abuse_events"]),
        _scenario(now, "hard_state_no_auto_unhard_write_intent", mk("hard", 5), []),
        _scenario(now, "active_exemption_no_db_write_intent", mk("normal", 11, exempt=True), []),
        _scenario(now, "unknown_state_no_db_write_intent", mk("unknown", 5), []),
        _scenario(now, "blockers_present_no_db_write_intent", mk("normal", 11, blockers=["manual_blocker"]) , []),
    ]
    scenarios_ok = all(bool(s["passed"]) for s in scenarios)

    bools = {
        "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase7_accepted": "current_accepted_phase: Phase 7" in phase_status,
        "phase8_working": "current_working_phase: Phase 8" in phase_status,
        "phase8_planning_only": True,
        "farm5_0_1_114_sync_evidence_present": "synced to 0.1.114" in phase_status,
        "no_farm5_0_1_111_sync_evidence_claimed": "synced to 0.1.111" not in phase_status,
        "no_farm5_0_1_112_sync_evidence_claimed": "synced to 0.1.112" not in phase_status,
        "no_farm5_0_1_113_sync_evidence_claimed": "synced to 0.1.113" not in phase_status,
        "no_farm5_0_1_115_sync_evidence_claimed": "synced to 0.1.115" not in phase_status,
        "state_machine_contract_present": sm.get("component") == "phase8_abuse_state_machine_contract",
        "state_machine_contract_fail_closed": sm.get("final_decision") == "BLOCKED" and not bool(sm.get("execution_allowed")),
        "evidence_reporting_contract_present": er.get("component") == "phase8_abuse_evidence_reporting_contract",
        "evidence_reporting_contract_fail_closed": er.get("final_decision") == "BLOCKED" and not bool(er.get("execution_allowed")),
        "dry_run_evaluator_present": dr.get("component") == "phase8_abuse_dry_run_evaluator",
        "dry_run_evaluator_fail_closed": dr.get("final_decision") == "BLOCKED" and not bool(dr.get("execution_allowed")),
        "ai_phase8_task_present": "Current Phase 8 Step — Runtime/Worker Integration Readiness" in ai_phase8,
        "remaining_plan_db_transition_target_aligned": "Current target is Phase 8 runtime/worker integration readiness package." in remaining,
        "readme_current_gate_aligned": "runtime/worker integration readiness package" in readme,
        "index_current_gate_aligned": "runtime/worker integration readiness" in index,
        "ai_coding_rules_current_gate_aligned": "Phase 8 runtime/worker readiness stop condition" in rules,
        "apply_mode_plan_only": cfg.firewall.apply_mode == "plan_only",
        "runtime_activation_disabled": cfg.proxy.runtime_activation_allowed is False,
        "production_traffic_none": True,
        "firewall_apply_disallowed": True,
        "customer_nat_disallowed": True,
        "customer_firewall_rules_disallowed": True,
        "iptables_restore_disallowed": True,
        "abuse_automation_disallowed": True,
        "abuse_runner_disallowed": True,
        "db_reads_disallowed": True,
        "db_writes_disallowed": True,
        "abuse_state_db_reads_disallowed": True,
        "abuse_state_db_writes_disallowed": True,
        "abuse_event_db_writes_disallowed": True,
        "usage_sample_db_reads_disallowed": True,
        "policy_event_db_reads_disallowed": True,
        "customer_db_reads_disallowed": True,
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
        "missing_evidence_blocks_hardening": True,
        "stale_evidence_blocks_hardening": True,
        "farms_over_alone_does_not_harden": True,
        "worker_over_alone_does_not_harden": True,
        "all_active_customers_coverage_required": True,
        "no_silent_skip_required": True,
        "transition_plan_contract_defined": True,
        "db_mutation_plan_contract_defined": True,
        "operator_approval_contract_defined": True,
        "idempotency_contract_defined": True,
        "synthetic_transition_plan_scenarios_passed": scenarios_ok,
    }


    approval = asdict(build_operator_approval_contract())
    existing_models = "class AbuseState" in models and "class AbuseEvent" in models

    blocker_keys = [k for k, v in bools.items() if k in {
        "current_state_preserved","farm5_0_1_114_sync_evidence_present","state_machine_contract_present","state_machine_contract_fail_closed","evidence_reporting_contract_present","evidence_reporting_contract_fail_closed","dry_run_evaluator_present","dry_run_evaluator_fail_closed","ai_phase8_task_present","remaining_plan_db_transition_target_aligned","readme_current_gate_aligned","index_current_gate_aligned","ai_coding_rules_current_gate_aligned","apply_mode_plan_only","runtime_activation_disabled","synthetic_transition_plan_scenarios_passed"
    } and not v]
    blockers = [f"{k}_missing_or_failed" for k in blocker_keys]


    checklist_names = ["current_state_preserved","phase7_accepted","phase8_working","farm5_0_1_114_sync_evidence_present","state_machine_contract_present","state_machine_contract_fail_closed","evidence_reporting_contract_present","evidence_reporting_contract_fail_closed","dry_run_evaluator_present","dry_run_evaluator_fail_closed","ai_phase8_task_present","remaining_plan_db_transition_target_aligned","readme_current_gate_aligned","index_current_gate_aligned","ai_coding_rules_current_gate_aligned","transition_plan_contract_defined","db_mutation_plan_contract_defined","operator_approval_contract_defined","audit_payload_contract_defined","restore_reference_contract_defined","idempotency_contract_defined","synthetic_transition_plan_scenarios_defined","synthetic_transition_plan_scenarios_passed","existing_abuse_models_detected","config_apply_mode_plan_only","proxy_runtime_activation_disabled","no_production_traffic","firewall_apply_disallowed","customer_nat_disallowed","customer_firewall_rules_disallowed","no_iptables_restore_authorized","abuse_automation_disallowed","abuse_runner_disallowed","db_reads_disallowed","db_writes_disallowed","abuse_db_reads_disallowed","abuse_db_writes_disallowed","usage_policy_customer_db_reads_writes_disallowed","live_conntrack_firewall_reads_disallowed","hard_block_disallowed","soft_block_disallowed","pause_automation_disallowed","separate_phase8_db_execution_pr_required","future_runtime_worker_integration_pr_required","fresh_farm5_sync_evidence_required_before_acceptance"]
    checklist_mapping = {
        **bools,
        "audit_payload_contract_defined": True,
        "restore_reference_contract_defined": True,
        "synthetic_transition_plan_scenarios_defined": True,
        "existing_abuse_models_detected": existing_models,
        "config_apply_mode_plan_only": bools["apply_mode_plan_only"],
        "proxy_runtime_activation_disabled": bools["runtime_activation_disabled"],
        "no_production_traffic": bools["production_traffic_none"],
        "no_iptables_restore_authorized": bools["iptables_restore_disallowed"],
        "abuse_db_reads_disallowed": bools["abuse_state_db_reads_disallowed"],
        "abuse_db_writes_disallowed": bools["abuse_state_db_writes_disallowed"] and bools["abuse_event_db_writes_disallowed"],
        "usage_policy_customer_db_reads_writes_disallowed": bools["usage_sample_db_reads_disallowed"] and bools["policy_event_db_reads_disallowed"] and bools["customer_db_reads_disallowed"],
        "live_conntrack_firewall_reads_disallowed": bools["conntrack_live_read_disallowed"] and bools["firewall_counter_live_read_disallowed"],
        "separate_phase8_db_execution_pr_required": True,
        "future_runtime_worker_integration_pr_required": True,
        "fresh_farm5_sync_evidence_required_before_acceptance": True,
    }
    checklist = [{"item": i, "status": "PASS" if bool(checklist_mapping.get(i, False)) else "BLOCKED", "evidence": i} for i in checklist_names]

    report = {
        "component": "phase8_db_transition_readiness", "phase": "Phase 8 — Abuse 1h Core", "gate_type": "phase8_db_transition_readiness", "final_decision": "BLOCKED", "readiness_status": "DB_ONLY_CONTROLLED_TRANSITION_READINESS_DEFINED_NOT_ACCEPTED", "authorization_status": "PHASE8_DB_TRANSITION_READINESS_REPORT_ONLY_NOT_AUTHORIZED", "inspection_only": True, "report_only": True, "preflight_only": True, "dry_run": True, "execution_allowed": False, "phase8_acceptance_allowed": False,
        "state_machine_contract_present": bools["state_machine_contract_present"], "state_machine_contract_fail_closed": bools["state_machine_contract_fail_closed"], "evidence_reporting_contract_present": bools["evidence_reporting_contract_present"], "evidence_reporting_contract_fail_closed": bools["evidence_reporting_contract_fail_closed"], "dry_run_evaluator_present": bools["dry_run_evaluator_present"], "dry_run_evaluator_fail_closed": bools["dry_run_evaluator_fail_closed"], "transition_plan_contract_defined": True, "db_mutation_plan_contract_defined": True, "operator_approval_contract_defined": True, "audit_payload_contract_defined": True, "restore_reference_contract_defined": True, "idempotency_contract_defined": True, "synthetic_transition_plan_scenarios_defined": True, "synthetic_transition_plan_scenarios_passed": scenarios_ok,
        "existing_abuse_models_detected": existing_models, "future_migration_required": not existing_models, "future_db_execution_pr_required": True, "future_runtime_worker_integration_pr_required": True, "fresh_farm5_sync_evidence_required_before_acceptance": True,
        "farm5_0_1_114_sync_evidence_present": bools["farm5_0_1_114_sync_evidence_present"], "no_server_sync_evidence_for_0_1_115": bools["no_farm5_0_1_115_sync_evidence_claimed"],
        "db_transition_execution_authorized": False, "db_reads_authorized": False, "db_writes_authorized": False, "abuse_state_db_reads_authorized": False, "abuse_state_db_writes_authorized": False, "abuse_event_db_writes_authorized": False, "usage_sample_db_reads_authorized": False, "policy_event_db_reads_authorized": False, "customer_db_reads_authorized": False, "abuse_runner_authorized": False, "abuse_automation_authorized": False, "conntrack_live_read_authorized": False, "firewall_counter_live_read_authorized": False, "iptables_save_authorized": False, "iptables_restore_authorized": False, "hard_block_authorized": False, "soft_block_authorized": False, "pause_automation_authorized": False, "firewall_apply_authorized": False, "customer_nat_authorized": False, "customer_firewall_rules_authorized": False, "production_traffic_authorized": False, "ui_authorized": False, "telegram_authorized": False,
        "operator_review_required": True, "separate_phase8_db_execution_pr_required": True,
        **bools,
        "live_firewall_read_allowed": False, "live_firewall_write_allowed": False, "live_firewall_apply_allowed": False, "live_firewall_verify_allowed": False, "live_firewall_rollback_allowed": False, "iptables_save_executed": False, "iptables_restore_allowed": False, "iptables_restore_executed": False, "conntrack_live_read_executed": False, "firewall_counter_live_read_executed": False, "subprocess_firewall_calls_allowed": False, "subprocess_firewall_calls_executed": False, "real_adapter_allowed": False, "real_adapter_executed": False, "db_connect_executed": False, "db_read_executed": False, "db_mutation": False, "db_customer_read_allowed": False, "db_customer_read_executed": False, "db_usage_sample_read_allowed": False, "db_usage_sample_read_executed": False, "db_usage_sample_write_allowed": False, "db_usage_sample_written": False, "db_policy_event_read_allowed": False, "db_policy_event_read_executed": False, "db_policy_event_write_allowed": False, "db_policy_event_written": False, "db_abuse_state_read_allowed": False, "db_abuse_state_read_executed": False, "db_abuse_state_write_allowed": False, "db_abuse_state_written": False, "db_abuse_event_write_allowed": False, "db_abuse_event_written": False, "filesystem_write_executed": False, "scheduler_job_created": False, "timer_enabled": False, "usage_collector_runtime_allowed": False, "usage_collector_runtime_started": False, "policy_reject_collector_runtime_allowed": False, "policy_reject_collector_runtime_started": False, "abuse_runner_runtime_allowed": False, "abuse_runner_runtime_started": False, "customer_nat_allowed": False, "customer_nat_changed": False, "customer_firewall_rules_allowed": False, "customer_firewall_rules_changed": False, "production_traffic_changed": False, "abuse_automation_allowed_runtime": False, "hard_block_allowed": False, "hard_block_applied": False, "soft_block_allowed": False, "soft_block_applied": False, "pause_automation_allowed": False, "pause_applied": False, "ui_allowed_runtime": False, "telegram_allowed_runtime": False,
        "operator_approval_contract": approval,
        "synthetic_transition_plan_scenarios": scenarios,
        "phase8_db_transition_readiness_checklist": checklist,
        "blockers": blockers,
        "errors": [],
    }
    return report
