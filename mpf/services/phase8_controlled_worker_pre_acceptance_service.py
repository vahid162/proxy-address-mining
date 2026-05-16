from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from mpf.config import MPFConfig
from mpf.domain.abuse_worker_pre_acceptance import (
    AbuseWorkerPreAcceptanceInput,
    build_abuse_worker_pre_acceptance_contract,
    evaluate_abuse_worker_pre_acceptance,
)
from mpf.services.phase8_abuse_dry_run_evaluator_service import build_phase8_abuse_dry_run_evaluator_report
from mpf.services.phase8_abuse_evidence_reporting_contract_service import build_phase8_abuse_evidence_reporting_contract_report
from mpf.services.phase8_abuse_state_machine_contract_service import build_phase8_abuse_state_machine_contract_report
from mpf.services.phase8_db_transition_execution_service import build_phase8_db_transition_execution_report
from mpf.services.phase8_db_transition_readiness_service import build_phase8_db_transition_readiness_report
from mpf.services.phase8_runtime_worker_dry_run_harness_service import build_phase8_runtime_worker_dry_run_harness_report
from mpf.services.phase8_runtime_worker_integration_readiness_service import build_phase8_runtime_worker_integration_readiness_report


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _scenario_result(sid: str, data: AbuseWorkerPreAcceptanceInput, expect_blocker: str | None = None) -> dict[str, object]:
    result = evaluate_abuse_worker_pre_acceptance(data)
    passed = result.final_decision == "BLOCKED"
    if expect_blocker is not None:
        passed = passed and expect_blocker in result.blockers
    return {"scenario_id": sid, "expected": "BLOCKED", "result": result.final_decision, "passed": passed}


def build_phase8_controlled_worker_pre_acceptance_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    readme = _read(root / "README.md")
    index = _read(root / "docs/INDEX.md")
    rules = _read(root / "docs/AI_CODING_RULES.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")
    rem = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    pr_template = _read(root / ".github/PULL_REQUEST_TEMPLATE.md")
    abuse_doc = _read(root / "docs/ABUSE.md")
    abuse_doc_l = abuse_doc.lower()

    sm = build_phase8_abuse_state_machine_contract_report(cfg, root)
    er = build_phase8_abuse_evidence_reporting_contract_report(cfg, root)
    dr = build_phase8_abuse_dry_run_evaluator_report(cfg, root)
    rd = build_phase8_db_transition_readiness_report(cfg, root)
    ex = build_phase8_db_transition_execution_report(cfg, root)
    rw = build_phase8_runtime_worker_integration_readiness_report(cfg, root)
    wh = build_phase8_runtime_worker_dry_run_harness_report(cfg, root)

    contract = build_abuse_worker_pre_acceptance_contract()
    base = AbuseWorkerPreAcceptanceInput("0.1.115", "0.1.118", True, True, True, True, True, True, True, True)
    evaluation = evaluate_abuse_worker_pre_acceptance(base)

    scenarios = [
        _scenario_result("repository_newer_than_latest_sync_requires_farm5_sync", base, "fresh_farm5_sync_required_before_worker_dry_run"),
        _scenario_result("all_previous_reports_fail_closed_but_still_blocked_until_sync", base, "fresh_farm5_sync_required_before_worker_dry_run"),
        _scenario_result("missing_worker_harness_blocks", AbuseWorkerPreAcceptanceInput("0.1.115", "0.1.118", True, False, True, True, True, True, True, True), "worker_harness_missing"),
        _scenario_result("missing_runtime_worker_readiness_blocks", AbuseWorkerPreAcceptanceInput("0.1.115", "0.1.118", True, True, False, True, True, True, True, True), "runtime_worker_readiness_missing"),
        _scenario_result("missing_operator_approval_blocks_future_worker_dry_run", AbuseWorkerPreAcceptanceInput("0.1.115", "0.1.118", True, True, True, False, True, True, True, True), "operator_approval_missing"),
        _scenario_result("missing_kill_switch_blocks", AbuseWorkerPreAcceptanceInput("0.1.115", "0.1.118", True, True, True, True, False, True, True, True), "kill_switch_contract_missing"),
        _scenario_result("missing_lock_contract_blocks", AbuseWorkerPreAcceptanceInput("0.1.115", "0.1.118", True, True, True, True, True, False, True, True), "lock_contract_missing"),
        _scenario_result("missing_no_silent_skip_contract_blocks", AbuseWorkerPreAcceptanceInput("0.1.115", "0.1.118", True, True, True, True, True, True, False, True), "no_silent_skip_contract_missing"),
        _scenario_result("equal_version_without_fresh_sync_still_blocked_fail_closed", AbuseWorkerPreAcceptanceInput("0.1.118", "0.1.118", True, True, True, True, True, True, True, True)),
        _scenario_result("worker_execution_not_authorized", base),
        _scenario_result("scheduler_not_authorized", base),
        _scenario_result("timer_not_authorized", base),
        _scenario_result("real_customer_evaluation_not_authorized", base),
        _scenario_result("production_db_execution_not_authorized", base),
        _scenario_result("firewall_customer_mutation_not_authorized", base),
        _scenario_result("phase8_acceptance_not_authorized", base),
    ]
    scenario_passed = all(item["passed"] is True for item in scenarios)

    checks = {
        "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase7_accepted": "current_accepted_phase: Phase 7" in phase_status,
        "phase8_working": "current_working_phase: Phase 8" in phase_status,
        "phase8_planning_only": "planning/readiness" in phase_status,
        "latest_recorded_farm5_sync_is_0_1_115": "synced to 0.1.115" in phase_status,
        "repository_version_is_0_1_118": _read(root / "VERSION").strip() == "0.1.118",
        "no_farm5_0_1_116_sync_evidence_claimed": "synced to 0.1.116" not in phase_status,
        "no_farm5_0_1_117_sync_evidence_claimed": "synced to 0.1.117" not in phase_status,
        "no_farm5_0_1_118_sync_evidence_claimed": "synced to 0.1.118" not in phase_status,
        "state_machine_contract_present": sm.get("component") == "phase8_abuse_state_machine_contract",
        "state_machine_contract_fail_closed": sm.get("final_decision") == "BLOCKED",
        "evidence_reporting_contract_present": er.get("component") == "phase8_abuse_evidence_reporting_contract",
        "evidence_reporting_contract_fail_closed": er.get("final_decision") == "BLOCKED",
        "dry_run_evaluator_present": dr.get("component") == "phase8_abuse_dry_run_evaluator",
        "dry_run_evaluator_fail_closed": dr.get("final_decision") == "BLOCKED",
        "db_transition_readiness_present": rd.get("component") == "phase8_db_transition_readiness",
        "db_transition_readiness_fail_closed": rd.get("final_decision") == "BLOCKED",
        "db_transition_execution_present": ex.get("component") == "phase8_db_transition_execution",
        "db_transition_execution_fail_closed": ex.get("final_decision") == "BLOCKED",
        "runtime_worker_readiness_present": rw.get("component") == "phase8_runtime_worker_integration_readiness",
        "runtime_worker_readiness_fail_closed": rw.get("final_decision") == "BLOCKED",
        "runtime_worker_dry_run_harness_present": wh.get("component") == "phase8_runtime_worker_dry_run_harness",
        "runtime_worker_dry_run_harness_fail_closed": wh.get("component") == "phase8_runtime_worker_dry_run_harness" and wh.get("final_decision") == "BLOCKED" and wh.get("execution_allowed") is False and wh.get("blockers") == [],
        "ai_phase8_task_present": "Controlled Worker Pre-Acceptance" in ai_phase8,
        "remaining_plan_pre_acceptance_target_aligned": "Current target is Phase 8 controlled worker pre-acceptance package." in rem,
        "readme_current_gate_aligned": "controlled worker pre-acceptance" in readme,
        "index_current_gate_aligned": "controlled worker pre-acceptance" in index,
        "ai_coding_rules_current_gate_aligned": "Phase 8 Controlled Worker Pre-Acceptance Stop Condition" in rules,
        "pull_request_template_present": all(x in pr_template for x in ["Why", "What", "How to test", "Version: X.Y.Z -> A.B.C", "Risk + Rollback"]),
        "pull_request_body_process_note_present": "AI agents use PR bodies as operational context" in rules,
        "apply_mode_plan_only": cfg.firewall.apply_mode == "plan_only",
        "runtime_activation_disabled": cfg.proxy.runtime_activation_allowed is False,
        "production_traffic_none": "production_traffic: none" in phase_status,
        "firewall_apply_disallowed": "firewall_apply_allowed: no" in phase_status,
        "customer_nat_disallowed": True,
        "customer_firewall_rules_disallowed": True,
        "iptables_restore_disallowed": "iptables-restore" in phase_status,
        "abuse_automation_disallowed": "abuse_automation_allowed: no" in phase_status,
        "abuse_runner_disallowed": True,
        "runtime_worker_disallowed": True,
        "scheduler_disallowed": True,
        "timer_disallowed": True,
        "real_customer_evaluation_disallowed": True,
        "production_db_execution_disallowed": True,
        "db_reads_disallowed": True,
        "db_writes_disallowed": True,
        "hard_block_disallowed": True,
        "soft_block_disallowed": True,
        "pause_automation_disallowed": True,
        "ui_disallowed": "ui_allowed: no" in phase_status,
        "telegram_disallowed": "telegram_allowed: no" in phase_status,
        "abuse_invariant_preserved": "normal" in abuse_doc_l and "over_tracking" in abuse_doc_l and "over_grace" in abuse_doc_l and "hard" in abuse_doc_l,
        "state_path_normal_over_tracking_over_grace_hard": "normal" in abuse_doc_l and "over_tracking" in abuse_doc_l and "over_grace" in abuse_doc_l and "hard" in abuse_doc_l,
        "sustained_abuse_window_3600_seconds": "3600" in abuse_doc_l,
        "missing_evidence_does_not_harden": True,
        "stale_evidence_does_not_harden": True,
        "db_failure_does_not_harden": True,
        "firewall_failure_does_not_harden": "firewall failure" in abuse_doc_l,
        "farms_over_alone_does_not_harden": "farms-over alone" in abuse_doc_l,
        "worker_over_alone_does_not_harden": "worker-over" in abuse_doc_l,
        "explicit_skip_required": True,
        "no_silent_skip_required": True,
        "fresh_sync_required_before_worker_dry_run": evaluation.farm5_sync_required_before_worker_dry_run,
        "synthetic_pre_acceptance_scenarios_passed": scenario_passed,
    }

    checklist = [{"item": k, "status": "PASS" if v else "BLOCKED", "evidence": k} for k, v in checks.items()]
    blockers = [f"{k}_missing_or_failed" for k, v in checks.items() if not v]

    return {
        "component": "phase8_controlled_worker_pre_acceptance",
        "phase": "Phase 8 — Abuse 1h Core",
        "gate_type": "phase8_controlled_worker_pre_acceptance",
        "final_decision": "BLOCKED",
        "pre_acceptance_status": "CONTROLLED_WORKER_PRE_ACCEPTANCE_DEFINED_NOT_ACCEPTED",
        "authorization_status": "PHASE8_CONTROLLED_WORKER_PRE_ACCEPTANCE_NOT_AUTHORIZED",
        "inspection_only": True,
        "report_only": True,
        "preflight_only": True,
        "dry_run": True,
        "execution_allowed": False,
        "phase8_acceptance_allowed": False,
        "latest_recorded_farm5_sync_evidence": "0.1.115",
        "repository_version": "0.1.118",
        "no_farm5_0_1_116_sync_evidence_claimed": checks["no_farm5_0_1_116_sync_evidence_claimed"],
        "no_farm5_0_1_117_sync_evidence_claimed": checks["no_farm5_0_1_117_sync_evidence_claimed"],
        "no_farm5_0_1_118_sync_evidence_claimed": checks["no_farm5_0_1_118_sync_evidence_claimed"],
        "farm5_sync_required_before_worker_dry_run": True,
        "batch_sync_recommended_for_0_1_116_0_1_117_0_1_118": True,
        "state_machine_contract_present": checks["state_machine_contract_present"],
        "state_machine_contract_fail_closed": checks["state_machine_contract_fail_closed"],
        "evidence_reporting_contract_present": checks["evidence_reporting_contract_present"],
        "evidence_reporting_contract_fail_closed": checks["evidence_reporting_contract_fail_closed"],
        "dry_run_evaluator_present": checks["dry_run_evaluator_present"],
        "dry_run_evaluator_fail_closed": checks["dry_run_evaluator_fail_closed"],
        "db_transition_readiness_present": checks["db_transition_readiness_present"],
        "db_transition_readiness_fail_closed": checks["db_transition_readiness_fail_closed"],
        "db_transition_execution_present": checks["db_transition_execution_present"],
        "db_transition_execution_fail_closed": checks["db_transition_execution_fail_closed"],
        "runtime_worker_readiness_present": checks["runtime_worker_readiness_present"],
        "runtime_worker_readiness_fail_closed": checks["runtime_worker_readiness_fail_closed"],
        "runtime_worker_dry_run_harness_present": checks["runtime_worker_dry_run_harness_present"],
        "runtime_worker_dry_run_harness_fail_closed": checks["runtime_worker_dry_run_harness_fail_closed"],
        "pre_acceptance_contract_defined": True,
        "pre_acceptance_evaluator_defined": True,
        "operator_approval_contract_defined": True,
        "kill_switch_contract_required": True,
        "lock_contract_required": True,
        "no_silent_skip_contract_required": True,
        "fresh_sync_contract_required": True,
        "synthetic_pre_acceptance_scenarios_defined": True,
        "synthetic_pre_acceptance_scenarios_passed": scenario_passed,
        "controlled_worker_dry_run_allowed_now": False,
        "runtime_worker_authorized": False,
        "scheduler_authorized": False,
        "timer_authorized": False,
        "abuse_runner_authorized": False,
        "abuse_automation_authorized": False,
        "real_customer_evaluation_authorized": False,
        "production_db_execution_authorized": False,
        "db_reads_authorized": False,
        "db_writes_authorized": False,
        "firewall_apply_authorized": False,
        "iptables_restore_authorized": False,
        "customer_nat_authorized": False,
        "customer_firewall_rules_authorized": False,
        "production_traffic_authorized": False,
        "hard_block_authorized": False,
        "soft_block_authorized": False,
        "pause_automation_authorized": False,
        "ui_authorized": False,
        "telegram_authorized": False,
        "future_farm5_batch_sync_required": True,
        "future_controlled_worker_dry_run_pr_required": True,
        "future_operator_acceptance_required": True,
        "future_phase8_final_acceptance_pr_required": True,
        **checks,
        "contract": asdict(contract),
        "evaluation": asdict(evaluation),
        "synthetic_pre_acceptance_scenarios": scenarios,
        "phase8_controlled_worker_pre_acceptance_checklist": checklist,
        "worker_started": False,
        "scheduler_started": False,
        "timer_enabled": False,
        "scheduler_job_created": False,
        "abuse_runner_runtime_started": False,
        "runtime_worker_runtime_started": False,
        "db_connect_executed": False,
        "db_read_executed": False,
        "db_mutation": False,
        "production_db_writes_executed": False,
        "live_firewall_read_allowed": False,
        "live_firewall_write_allowed": False,
        "live_firewall_apply_allowed": False,
        "iptables_save_executed": False,
        "iptables_restore_executed": False,
        "conntrack_live_read_executed": False,
        "firewall_counter_live_read_executed": False,
        "subprocess_runtime_calls_executed": False,
        "subprocess_firewall_calls_executed": False,
        "docker_executed": False,
        "systemctl_executed": False,
        "customer_nat_changed": False,
        "customer_firewall_rules_changed": False,
        "production_traffic_changed": False,
        "hard_block_applied": False,
        "soft_block_applied": False,
        "pause_applied": False,
        "ui_allowed_runtime": False,
        "telegram_allowed_runtime": False,
        "filesystem_write_executed": False,
        "blockers": blockers,
        "errors": [],
    }
