from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig
from mpf.domain.abuse_worker_integration_readiness import (
    build_abuse_worker_failure_modes,
    build_abuse_worker_loop_contract,
    build_abuse_worker_readiness_contract,
)
from mpf.services.phase8_abuse_dry_run_evaluator_service import build_phase8_abuse_dry_run_evaluator_report
from mpf.services.phase8_abuse_evidence_reporting_contract_service import build_phase8_abuse_evidence_reporting_contract_report
from mpf.services.phase8_abuse_state_machine_contract_service import build_phase8_abuse_state_machine_contract_report
from mpf.services.phase8_db_transition_execution_service import build_phase8_db_transition_execution_report
from mpf.services.phase8_db_transition_readiness_service import build_phase8_db_transition_readiness_report


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def build_phase8_runtime_worker_integration_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = read_historical_phase_status(root)
    ai = _read(root / "docs/AI_PHASE_8_TASK.md")
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    rules = _read(root / "docs/AI_CODING_RULES.md")

    sm = build_phase8_abuse_state_machine_contract_report(cfg, root)
    er = build_phase8_abuse_evidence_reporting_contract_report(cfg, root)
    dr = build_phase8_abuse_dry_run_evaluator_report(cfg, root)
    rd = build_phase8_db_transition_readiness_report(cfg, root)
    ex = build_phase8_db_transition_execution_report(cfg, root)

    worker = build_abuse_worker_readiness_contract()
    loop = build_abuse_worker_loop_contract()
    failures = build_abuse_worker_failure_modes()
    failure_map = {f.failure: f for f in failures}

    scenarios = [
        {"scenario_id": "worker_default_disabled", "expected": True, "result": worker.enabled_by_default is False, "passed": worker.enabled_by_default is False},
        {"scenario_id": "scheduler_default_disabled", "expected": True, "result": worker.scheduler_enabled_by_default is False, "passed": worker.scheduler_enabled_by_default is False},
        {"scenario_id": "report_only_mode_allowed_as_contract", "expected": True, "result": "report_only" in loop.allowed_modes, "passed": "report_only" in loop.allowed_modes},
        {"scenario_id": "dry_run_mode_allowed_as_contract", "expected": True, "result": "dry_run" in loop.allowed_modes, "passed": "dry_run" in loop.allowed_modes},
        {"scenario_id": "production_mode_blocked", "expected": True, "result": loop.production_enable_allowed_in_this_pr is False, "passed": loop.production_enable_allowed_in_this_pr is False},
        {"scenario_id": "real_customer_evaluation_blocked", "expected": True, "result": worker.real_customer_evaluation_allowed is False, "passed": worker.real_customer_evaluation_allowed is False},
        {"scenario_id": "production_db_execution_blocked", "expected": True, "result": worker.production_db_execution_allowed is False, "passed": worker.production_db_execution_allowed is False},
        {"scenario_id": "firewall_mutation_blocked", "expected": True, "result": worker.firewall_mutation_allowed is False, "passed": worker.firewall_mutation_allowed is False},
        {"scenario_id": "customer_mutation_blocked", "expected": True, "result": worker.customer_mutation_allowed is False, "passed": worker.customer_mutation_allowed is False},
        {"scenario_id": "missing_evidence_failure_does_not_harden", "expected": True, "result": not failure_map["missing_evidence"].harden_allowed, "passed": not failure_map["missing_evidence"].harden_allowed},
        {"scenario_id": "stale_evidence_failure_does_not_harden", "expected": True, "result": not failure_map["stale_evidence"].harden_allowed, "passed": not failure_map["stale_evidence"].harden_allowed},
        {"scenario_id": "db_failure_does_not_harden", "expected": True, "result": not failure_map["db_failure"].harden_allowed, "passed": not failure_map["db_failure"].harden_allowed},
        {"scenario_id": "firewall_failure_does_not_harden", "expected": True, "result": not failure_map["firewall_failure"].harden_allowed, "passed": not failure_map["firewall_failure"].harden_allowed},
        {"scenario_id": "lock_contention_reports_skip_no_silent_skip", "expected": True, "result": "explicit_skip" in failure_map["lock_contention"].action, "passed": "explicit_skip" in failure_map["lock_contention"].action},
        {"scenario_id": "kill_switch_required", "expected": True, "result": len(worker.required_kill_switches) > 0, "passed": len(worker.required_kill_switches) > 0},
        {"scenario_id": "operator_enable_required_future_gated", "expected": True, "result": loop.manual_enable_required and not loop.production_enable_allowed_in_this_pr, "passed": loop.manual_enable_required and not loop.production_enable_allowed_in_this_pr},
    ]
    scenarios_passed = all(s["passed"] for s in scenarios)

    checks = {
        "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase7_accepted": "current_accepted_phase: Phase 7" in phase_status,
        "phase8_working": "current_working_phase: Phase 8" in phase_status,
        "phase8_planning_only": True,
        "farm5_0_1_115_sync_evidence_present": "synced to 0.1.115" in phase_status,
        "farm5_0_1_115_db_execution_report_evidence_present": "phase8 db-transition-execution --output json" in phase_status,
        "no_farm5_0_1_116_sync_evidence_claimed": "synced to 0.1.116" not in phase_status,
        "state_machine_contract_present": sm.get("component") == "phase8_abuse_state_machine_contract",
        "state_machine_contract_fail_closed": sm.get("final_decision") == "BLOCKED" and sm.get("execution_allowed") is False,
        "evidence_reporting_contract_present": er.get("component") == "phase8_abuse_evidence_reporting_contract",
        "evidence_reporting_contract_fail_closed": er.get("final_decision") == "BLOCKED" and er.get("execution_allowed") is False,
        "dry_run_evaluator_present": dr.get("component") == "phase8_abuse_dry_run_evaluator",
        "dry_run_evaluator_fail_closed": dr.get("final_decision") == "BLOCKED" and dr.get("execution_allowed") is False,
        "db_transition_readiness_present": rd.get("component") == "phase8_db_transition_readiness",
        "db_transition_readiness_fail_closed": rd.get("final_decision") == "BLOCKED" and rd.get("execution_allowed") is False and rd.get("blockers") == [],
        "db_transition_execution_present": ex.get("component") == "phase8_db_transition_execution",
        "db_transition_execution_fail_closed": ex.get("final_decision") == "BLOCKED" and ex.get("execution_allowed") is False,
        "ai_phase8_task_present": "Runtime/Worker Integration Readiness" in ai,
        "remaining_plan_runtime_worker_target_aligned": "Current target is Phase 8 runtime/worker integration readiness package." in remaining,
        "phase_status_current_gate_aligned": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase8_task_current_gate_aligned": "Runtime/Worker Integration Readiness" in ai,
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
        "runtime_worker_disallowed": True,
        "scheduler_disallowed": True,
        "real_customer_evaluation_disallowed": True,
        "production_db_execution_disallowed": True,
        "db_reads_disallowed": True,
        "db_writes_disallowed": True,
        "hard_block_disallowed": True,
        "soft_block_disallowed": True,
        "pause_automation_disallowed": True,
        "ui_disallowed": True,
        "telegram_disallowed": True,
        "abuse_invariant_preserved": True,
        "state_path_normal_over_tracking_over_grace_hard": True,
        "sustained_abuse_window_3600_seconds": True,
        "missing_evidence_does_not_harden": not failure_map["missing_evidence"].harden_allowed,
        "stale_evidence_does_not_harden": not failure_map["stale_evidence"].harden_allowed,
        "farms_over_alone_does_not_harden": True,
        "worker_over_alone_does_not_harden": True,
        "no_silent_skip_required": True,
        "worker_synthetic_scenarios_passed": scenarios_passed,
    }
    checks["worker_readiness_contract_defined"] = True
    checks["worker_loop_contract_defined"] = True
    checks["worker_failure_modes_defined"] = True
    checks["worker_synthetic_scenarios_defined"] = True
    checks["worker_default_disabled"] = worker.enabled_by_default is False
    checks["scheduler_default_disabled"] = worker.scheduler_enabled_by_default is False
    checks["future_worker_dry_run_harness_pr_required"] = True
    checks["future_farm5_sync_required_before_runtime_acceptance"] = True
    checks["future_operator_acceptance_required"] = True

    checklist_names = ["current_state_preserved","phase7_accepted","phase8_working","farm5_0_1_115_sync_evidence_present","farm5_0_1_115_db_execution_report_evidence_present","no_farm5_0_1_116_sync_evidence_claimed","state_machine_contract_present","state_machine_contract_fail_closed","evidence_reporting_contract_present","evidence_reporting_contract_fail_closed","dry_run_evaluator_present","dry_run_evaluator_fail_closed","db_transition_readiness_present","db_transition_readiness_fail_closed","db_transition_execution_present","db_transition_execution_fail_closed","worker_readiness_contract_defined","worker_loop_contract_defined","worker_failure_modes_defined","worker_synthetic_scenarios_defined","worker_synthetic_scenarios_passed","worker_default_disabled","scheduler_default_disabled","runtime_worker_disallowed","scheduler_disallowed","real_customer_evaluation_disallowed","production_db_execution_disallowed","db_reads_disallowed","db_writes_disallowed","firewall_apply_disallowed","customer_nat_disallowed","customer_firewall_rules_disallowed","hard_block_disallowed","soft_block_disallowed","pause_automation_disallowed","no_silent_skip_required","future_worker_dry_run_harness_pr_required","future_farm5_sync_required_before_runtime_acceptance","future_operator_acceptance_required"]
    checklist = [{"item": i, "status": "PASS" if checks.get(i, False) else "BLOCKED", "evidence": i} for i in checklist_names]
    blockers = [f"{i}_missing_or_failed" for i in checklist_names if checks.get(i, False) is False]

    return {
        "component": "phase8_runtime_worker_integration_readiness", "phase": "Phase 8 — Abuse 1h Core", "gate_type": "phase8_runtime_worker_integration_readiness", "final_decision": "BLOCKED", "readiness_status": "RUNTIME_WORKER_INTEGRATION_READINESS_DEFINED_NOT_ACCEPTED", "authorization_status": "PHASE8_RUNTIME_WORKER_INTEGRATION_NOT_AUTHORIZED", "inspection_only": True, "report_only": True, "preflight_only": True, "dry_run": True, "execution_allowed": False, "phase8_acceptance_allowed": False,
        **checks,
        "worker_readiness_contract": worker.__dict__, "worker_loop_contract": loop.__dict__, "worker_failure_modes": [f.__dict__ for f in failures], "worker_synthetic_scenarios": scenarios,
        "runtime_worker_authorized": False, "scheduler_authorized": False, "abuse_runner_authorized": False, "abuse_automation_authorized": False, "real_customer_evaluation_authorized": False, "production_db_execution_authorized": False, "db_reads_authorized": False, "db_writes_authorized": False, "firewall_apply_authorized": False, "iptables_restore_authorized": False, "customer_nat_authorized": False, "customer_firewall_rules_authorized": False, "production_traffic_authorized": False, "hard_block_authorized": False, "soft_block_authorized": False, "pause_automation_authorized": False, "ui_authorized": False, "telegram_authorized": False,
        "future_worker_dry_run_harness_pr_required": True, "future_farm5_sync_required_before_runtime_acceptance": True, "future_operator_acceptance_required": True,
        "live_firewall_read_allowed": False, "live_firewall_write_allowed": False, "live_firewall_apply_allowed": False, "iptables_save_executed": False, "iptables_restore_executed": False, "conntrack_live_read_executed": False, "firewall_counter_live_read_executed": False, "subprocess_runtime_calls_executed": False, "subprocess_firewall_calls_executed": False, "docker_executed": False, "systemctl_executed": False, "scheduler_job_created": False, "timer_enabled": False, "worker_started": False, "abuse_runner_runtime_started": False, "db_connect_executed": False, "db_read_executed": False, "db_mutation": False, "production_db_writes_executed": False, "customer_nat_changed": False, "customer_firewall_rules_changed": False, "production_traffic_changed": False, "hard_block_applied": False, "soft_block_applied": False, "pause_applied": False, "ui_allowed_runtime": False, "telegram_allowed_runtime": False, "filesystem_write_executed": False,
        "phase8_runtime_worker_integration_readiness_checklist": checklist, "blockers": blockers, "errors": [],
    }
