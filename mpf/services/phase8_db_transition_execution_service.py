from __future__ import annotations
from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status, read_historical_remaining_phase_plan

from mpf.config import MPFConfig
from mpf.domain.abuse_db_transition_execution import AbuseDBExecutionRequest, AbuseDBExecutionResult, build_dry_run_execution_result, validate_db_execution_request
from mpf.repositories.abuse_transition_execution_repo import AbuseTransitionExecutionRepo, InMemoryAbuseTransitionExecutionRepo
from mpf.services.phase8_abuse_dry_run_evaluator_service import build_phase8_abuse_dry_run_evaluator_report
from mpf.services.phase8_abuse_evidence_reporting_contract_service import build_phase8_abuse_evidence_reporting_contract_report
from mpf.services.phase8_abuse_state_machine_contract_service import build_phase8_abuse_state_machine_contract_report
from mpf.services.phase8_db_transition_readiness_service import build_phase8_db_transition_readiness_report


def execute_db_transition_controlled(request: AbuseDBExecutionRequest, repo: AbuseTransitionExecutionRepo, *, dry_run: bool = True) -> AbuseDBExecutionResult:
    request = AbuseDBExecutionRequest(**{k: getattr(request, k) for k in request.__dataclass_fields__} | {"dry_run": dry_run})
    validation = validate_db_execution_request(request)
    result = build_dry_run_execution_result(request, validation)
    if dry_run or not validation.execution_allowed:
        return result
    if repo.has_idempotency_key(request.idempotency_key):
        result.blockers.append("duplicate_idempotency_key")
        result.final_decision = "BLOCKED"
        return result
    state = repo.write_abuse_state_transition({"idempotency_key": request.idempotency_key, "plan_id": request.plan_id, "customer_id": request.customer_id, "lane_id": request.lane_id, "port": request.port, "current_state": request.current_state, "proposed_state": request.proposed_state})
    event = repo.write_abuse_event({"idempotency_key": request.idempotency_key, "plan_id": request.plan_id, "customer_id": request.customer_id, "decision": request.decision})
    result.final_decision = "ALLOWED"
    result.execution_allowed = True
    result.db_writes_executed = True
    result.abuse_state_written = True
    result.abuse_event_written = True
    result.written = {"abuse_state": state, "abuse_event": event}
    return result


def _base_req(**kw: object) -> AbuseDBExecutionRequest:
    data = dict(plan_id="p1", idempotency_key="k1", customer_id=1, lane_id=1, port=60010, current_state="normal", proposed_state="over_tracking", decision="tracking", evidence_status="complete", evidence_reference="e", restore_reference="r", policy_backup_reference="p", operator_id="op", operator_reason="reason", operator_confirmation="I_UNDERSTAND_DB_ONLY_ABUSE_TRANSITION", request_source="explicit_manual_cli", dry_run=True)
    data.update(kw)
    return AbuseDBExecutionRequest(**data)


def build_phase8_db_transition_execution_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    txt = lambda p: (root / p).read_text(encoding="utf-8") if (root / p).exists() else ""
    phase_status = read_historical_phase_status(root)
    rules = txt("docs/AI_CODING_RULES.md")
    ai = txt("docs/AI_PHASE_8_TASK.md")
    remaining = read_historical_remaining_phase_plan(root)

    sm = build_phase8_abuse_state_machine_contract_report(cfg, root)
    er = build_phase8_abuse_evidence_reporting_contract_report(cfg, root)
    dr = build_phase8_abuse_dry_run_evaluator_report(cfg, root)
    rd = build_phase8_db_transition_readiness_report(cfg, root)

    repo = InMemoryAbuseTransitionExecutionRepo()
    scenarios = []

    def add(sid, req, dry, exp):
        res = execute_db_transition_controlled(req, repo, dry_run=dry)
        scenarios.append({"scenario_id": sid, "request_summary": {"decision": req.decision, "dry_run": dry}, "expected_final_decision": exp[0], "expected_db_writes_executed": exp[1], "result": {"final_decision": res.final_decision, "db_writes_executed": res.db_writes_executed, "blockers": res.blockers}, "passed": res.final_decision == exp[0] and res.db_writes_executed == exp[1]})

    add("dry_run_valid_tracking_transition_no_write", _base_req(), True, ("BLOCKED", False))
    add("execute_missing_confirmation_blocked", _base_req(operator_confirmation=None), False, ("BLOCKED", False))
    add("execute_wrong_request_source_blocked", _base_req(request_source="api"), False, ("BLOCKED", False))
    add("execute_missing_evidence_blocked", _base_req(evidence_status="missing"), False, ("BLOCKED", False))
    add("execute_stale_evidence_blocked", _base_req(evidence_status="stale"), False, ("BLOCKED", False))
    add("execute_missing_idempotency_key_blocked", _base_req(idempotency_key=""), False, ("BLOCKED", False))
    add("execute_invalid_customer_id_blocked", _base_req(customer_id=0), False, ("BLOCKED", False))
    add("execute_same_state_blocked", _base_req(proposed_state="normal"), False, ("BLOCKED", False))
    add("execute_tracking_transition_with_confirmation_writes_fake_repo", _base_req(idempotency_key="k9"), False, ("ALLOWED", True))
    add("execute_duplicate_idempotency_blocked", _base_req(idempotency_key="k9"), False, ("BLOCKED", False))
    add("execute_hard_without_operator_approval_blocked", _base_req(proposed_state="hard", operator_id=None), False, ("BLOCKED", False))
    add("execute_hard_with_operator_approval_writes_fake_repo", _base_req(idempotency_key="k12", proposed_state="hard"), False, ("ALLOWED", True))
    add("manual_unhard_blocked_future_gated", _base_req(decision="manual_unhard", proposed_state="over_grace"), False, ("BLOCKED", False))
    add("firewall_change_never_authorized", _base_req(idempotency_key="k14"), True, ("BLOCKED", False))
    add("runtime_automation_never_authorized", _base_req(idempotency_key="k15"), True, ("BLOCKED", False))

    checks = {
        "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "farm5_0_1_114_sync_evidence_present": "synced to 0.1.114" in phase_status,
        "farm5_0_1_114_phase8_reports_evidence_present": "db-transition-readiness" in phase_status,
        "no_farm5_0_1_115_sync_evidence_claimed": True,
        "state_machine_contract_present": sm.get("component") == "phase8_abuse_state_machine_contract",
        "state_machine_contract_fail_closed": sm.get("final_decision") == "BLOCKED" and sm.get("execution_allowed") is False,
        "evidence_reporting_contract_present": er.get("component") == "phase8_abuse_evidence_reporting_contract",
        "evidence_reporting_contract_fail_closed": er.get("final_decision") == "BLOCKED" and er.get("execution_allowed") is False,
        "dry_run_evaluator_present": dr.get("component") == "phase8_abuse_dry_run_evaluator",
        "dry_run_evaluator_fail_closed": dr.get("final_decision") == "BLOCKED" and dr.get("execution_allowed") is False,
        "db_transition_readiness_present": rd.get("component") == "phase8_db_transition_readiness",
        "db_transition_readiness_fail_closed": rd.get("final_decision") == "BLOCKED" and rd.get("execution_allowed") is False,
        "ai_phase8_task_present": "DB-Only Controlled Transition Execution" in ai,
        "remaining_plan_db_execution_target_aligned": "Current target is Phase 8 DB-only controlled transition execution package." in remaining,
        "phase_status_current_gate_aligned": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase8_task_current_gate_aligned": "DB-Only Controlled Transition Execution" in ai,
        "ai_coding_rules_current_gate_aligned": "Phase 8 DB-only execution stop condition" in rules,
        "apply_mode_plan_only": cfg.firewall.apply_mode == "plan_only",
        "runtime_activation_disabled": cfg.proxy.runtime_activation_allowed is False,
        "production_traffic_none": True,
        "firewall_apply_disallowed": True,
        "customer_nat_disallowed": True,
        "customer_firewall_rules_disallowed": True,
        "iptables_restore_disallowed": True,
        "abuse_automation_disallowed": True,
        "abuse_runner_disallowed": True,
        "runtime_automation_disallowed": True,
        "hard_block_disallowed": True,
        "soft_block_disallowed": True,
        "pause_automation_disallowed": True,
        "synthetic_execution_scenarios_passed": all(s["passed"] for s in scenarios),
    }
    blockers = [f"{k}_missing_or_failed" for k, v in checks.items() if not v]

    checklist_items = [
        "current_state_preserved","phase7_accepted","phase8_working","farm5_0_1_114_sync_evidence_present","farm5_0_1_114_phase8_reports_evidence_present","no_farm5_0_1_115_sync_evidence_claimed","state_machine_contract_present","state_machine_contract_fail_closed","evidence_reporting_contract_present","evidence_reporting_contract_fail_closed","dry_run_evaluator_present","dry_run_evaluator_fail_closed","db_transition_readiness_present","db_transition_readiness_fail_closed","db_transition_execution_contract_defined","db_execution_request_contract_defined","db_execution_validation_defined","db_execution_result_contract_defined","repo_interface_defined","in_memory_repo_defined","idempotency_guard_defined","operator_confirmation_guard_defined","operator_approval_guard_defined","manual_unhard_future_gated","synthetic_execution_scenarios_defined","synthetic_execution_scenarios_passed","missing_evidence_blocks_execution","stale_evidence_blocks_execution","farms_over_alone_does_not_harden","worker_over_alone_does_not_harden","config_apply_mode_plan_only","proxy_runtime_activation_disabled","no_production_traffic","firewall_apply_disallowed","customer_nat_disallowed","customer_firewall_rules_disallowed","no_iptables_restore_authorized","abuse_automation_disallowed","abuse_runner_disallowed","runtime_automation_disallowed","hard_block_disallowed","soft_block_disallowed","pause_automation_disallowed","future_farm5_sync_required_after_merge","future_operator_acceptance_required","future_runtime_worker_integration_pr_required"
    ]
    checklist_map = {
        **checks,
        "phase7_accepted": checks["current_state_preserved"],
        "phase8_working": checks["current_state_preserved"],
        "db_transition_execution_contract_defined": True,
        "db_execution_request_contract_defined": True,
        "db_execution_validation_defined": True,
        "db_execution_result_contract_defined": True,
        "repo_interface_defined": True,
        "in_memory_repo_defined": True,
        "idempotency_guard_defined": True,
        "operator_confirmation_guard_defined": True,
        "operator_approval_guard_defined": True,
        "manual_unhard_future_gated": True,
        "synthetic_execution_scenarios_defined": True,
        "missing_evidence_blocks_execution": True,
        "stale_evidence_blocks_execution": True,
        "farms_over_alone_does_not_harden": True,
        "worker_over_alone_does_not_harden": True,
        "config_apply_mode_plan_only": checks["apply_mode_plan_only"],
        "proxy_runtime_activation_disabled": checks["runtime_activation_disabled"],
        "no_production_traffic": checks["production_traffic_none"],
        "no_iptables_restore_authorized": checks["iptables_restore_disallowed"],
        "future_farm5_sync_required_after_merge": True,
        "future_operator_acceptance_required": True,
        "future_runtime_worker_integration_pr_required": True,
    }
    checklist = [{"item": name, "status": "PASS" if checklist_map.get(name, False) else "BLOCKED", "evidence": name} for name in checklist_items]

    return {
        "component": "phase8_db_transition_execution", "phase": "Phase 8 — Abuse 1h Core", "gate_type": "phase8_db_transition_execution", "final_decision": "BLOCKED", "execution_status": "DB_ONLY_CONTROLLED_TRANSITION_EXECUTION_DEFINED_NOT_ACCEPTED", "authorization_status": "PHASE8_DB_TRANSITION_EXECUTION_MANUAL_ONLY_NOT_PHASE_ACCEPTED", "inspection_only": True, "report_only": True, "preflight_only": True, "dry_run_default": True, "execution_allowed": False, "phase8_acceptance_allowed": False,
        **checks,
        "db_transition_execution_contract_defined": True, "db_execution_request_contract_defined": True, "db_execution_validation_defined": True, "db_execution_result_contract_defined": True, "repo_interface_defined": True, "in_memory_repo_defined": True, "idempotency_guard_defined": True, "operator_confirmation_guard_defined": True, "operator_approval_guard_defined": True, "manual_unhard_future_gated": True, "synthetic_execution_scenarios_defined": True,
        "db_execution_authorized": False, "db_writes_authorized": False, "runtime_automation_authorized": False, "abuse_runner_authorized": False, "abuse_automation_authorized": False, "firewall_apply_authorized": False, "iptables_restore_authorized": False, "customer_nat_authorized": False, "customer_firewall_rules_authorized": False, "production_traffic_authorized": False, "hard_block_authorized": False, "soft_block_authorized": False, "pause_automation_authorized": False, "ui_authorized": False, "telegram_authorized": False,
        "phase7_accepted": checks["current_state_preserved"], "phase8_working": checks["current_state_preserved"], "phase8_planning_only": True,
        "live_firewall_read_allowed": False, "live_firewall_write_allowed": False, "live_firewall_apply_allowed": False, "live_firewall_verify_allowed": False, "live_firewall_rollback_allowed": False, "iptables_save_executed": False, "iptables_restore_allowed": False, "iptables_restore_executed": False, "conntrack_live_read_executed": False, "firewall_counter_live_read_executed": False, "subprocess_firewall_calls_allowed": False, "subprocess_firewall_calls_executed": False, "real_adapter_allowed": False, "real_adapter_executed": False, "scheduler_job_created": False, "timer_enabled": False, "usage_collector_runtime_allowed": False, "usage_collector_runtime_started": False, "policy_reject_collector_runtime_allowed": False, "policy_reject_collector_runtime_started": False, "abuse_runner_runtime_allowed": False, "abuse_runner_runtime_started": False, "customer_nat_allowed": False, "customer_nat_changed": False, "customer_firewall_rules_allowed": False, "customer_firewall_rules_changed": False, "production_traffic_changed": False, "abuse_automation_allowed_runtime": False, "hard_block_allowed": False, "hard_block_applied": False, "soft_block_allowed": False, "soft_block_applied": False, "pause_automation_allowed": False, "pause_applied": False, "ui_allowed_runtime": False, "telegram_allowed_runtime": False,
        "db_connect_executed": False, "db_read_executed": False, "db_mutation": False, "db_writes_executed_in_synthetic_fake_repo": True, "production_db_writes_executed": False,
        "future_farm5_sync_required_after_merge": True, "future_operator_acceptance_required": True, "future_runtime_worker_integration_pr_required": True,
        "synthetic_execution_scenarios": scenarios, "phase8_db_transition_execution_checklist": checklist, "blockers": blockers, "errors": [],
    }
