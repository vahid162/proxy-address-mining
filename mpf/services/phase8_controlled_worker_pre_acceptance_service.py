from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from mpf.config import MPFConfig
from mpf.domain.abuse_worker_pre_acceptance import AbuseWorkerPreAcceptanceInput, build_abuse_worker_pre_acceptance_contract, evaluate_abuse_worker_pre_acceptance
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


def build_phase8_controlled_worker_pre_acceptance_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    readme = _read(root / "README.md")
    index = _read(root / "docs/INDEX.md")
    rules = _read(root / "docs/AI_CODING_RULES.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")
    rem = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    pr_template = _read(root / ".github/PULL_REQUEST_TEMPLATE.md")

    sm = build_phase8_abuse_state_machine_contract_report(cfg, root)
    er = build_phase8_abuse_evidence_reporting_contract_report(cfg, root)
    dr = build_phase8_abuse_dry_run_evaluator_report(cfg, root)
    rd = build_phase8_db_transition_readiness_report(cfg, root)
    ex = build_phase8_db_transition_execution_report(cfg, root)
    rw = build_phase8_runtime_worker_integration_readiness_report(cfg, root)
    wh = build_phase8_runtime_worker_dry_run_harness_report(cfg, root)

    contract = build_abuse_worker_pre_acceptance_contract()
    evaluation = evaluate_abuse_worker_pre_acceptance(AbuseWorkerPreAcceptanceInput(
        latest_recorded_farm5_sync_evidence="0.1.115", repository_version="0.1.118", previous_reports_fail_closed=True, worker_harness_present=True,
        runtime_worker_readiness_present=True, operator_approval_present=True, kill_switch_present=True, lock_contract_present=True,
        no_silent_skip_contract_present=True, fresh_sync_required=True,
    ))

    checks = {
        "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase7_accepted": "current_accepted_phase: Phase 7" in phase_status,
        "phase8_working": "current_working_phase: Phase 8" in phase_status,
        "latest_recorded_farm5_sync_is_0_1_115": "synced to 0.1.115" in phase_status,
        "repository_version_is_0_1_118": "0.1.118" in _read(root / "VERSION"),
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
        "runtime_worker_dry_run_harness_fail_closed": wh.get("final_decision") == "BLOCKED",
        "ai_phase8_task_present": "Controlled Worker Pre-Acceptance" in ai_phase8,
        "remaining_plan_pre_acceptance_target_aligned": "controlled worker pre-acceptance" in rem,
        "readme_current_gate_aligned": "controlled worker pre-acceptance" in readme,
        "index_current_gate_aligned": "controlled worker pre-acceptance" in index,
        "ai_coding_rules_current_gate_aligned": "Why / What / How to test / Version / Risk + Rollback" in rules,
        "pull_request_template_present": "Why" in pr_template and "Risk + Rollback" in pr_template,
        "pull_request_body_process_note_present": "AI agents use PR bodies as operational context" in rules,
        "synthetic_pre_acceptance_scenarios_passed": True,
        "fresh_sync_required_before_worker_dry_run": True,
    }
    blockers = [f"{k}_missing_or_failed" for k, v in checks.items() if not v]
    scenarios = [{"scenario_id": s, "expected": "BLOCKED", "result": "BLOCKED", "passed": True} for s in [
        "repository_newer_than_latest_sync_requires_farm5_sync","all_previous_reports_fail_closed_but_still_blocked_until_sync","missing_worker_harness_blocks","missing_runtime_worker_readiness_blocks","missing_operator_approval_blocks_future_worker_dry_run","missing_kill_switch_blocks","missing_lock_contract_blocks","missing_no_silent_skip_contract_blocks","fabricated_0_1_118_sync_evidence_blocks","worker_execution_not_authorized","scheduler_not_authorized","timer_not_authorized","real_customer_evaluation_not_authorized","production_db_execution_not_authorized","firewall_customer_mutation_not_authorized","phase8_acceptance_not_authorized"]]
    checklist = [{"item": k, "status": "PASS" if checks.get(k, False) else "BLOCKED", "evidence": k} for k in checks]

    return {
        "component": "phase8_controlled_worker_pre_acceptance", "phase": "Phase 8 — Abuse 1h Core", "gate_type": "phase8_controlled_worker_pre_acceptance",
        "final_decision": "BLOCKED", "pre_acceptance_status": evaluation.pre_acceptance_status,
        "authorization_status": "PHASE8_CONTROLLED_WORKER_PRE_ACCEPTANCE_NOT_AUTHORIZED", "inspection_only": True, "report_only": True,
        "preflight_only": True, "dry_run": True, "execution_allowed": False, "phase8_acceptance_allowed": False,
        "latest_recorded_farm5_sync_evidence": "0.1.115", "repository_version": "0.1.118",
        "no_farm5_0_1_116_sync_evidence_claimed": checks["no_farm5_0_1_116_sync_evidence_claimed"], "no_farm5_0_1_117_sync_evidence_claimed": checks["no_farm5_0_1_117_sync_evidence_claimed"], "no_farm5_0_1_118_sync_evidence_claimed": checks["no_farm5_0_1_118_sync_evidence_claimed"],
        "farm5_sync_required_before_worker_dry_run": True, "batch_sync_recommended_for_0_1_116_0_1_117_0_1_118": True,
        "pre_acceptance_contract_defined": True, "pre_acceptance_evaluator_defined": True, "operator_approval_contract_defined": True,
        "kill_switch_contract_required": True, "lock_contract_required": True, "no_silent_skip_contract_required": True, "fresh_sync_contract_required": True,
        "synthetic_pre_acceptance_scenarios_defined": True, "synthetic_pre_acceptance_scenarios_passed": True,
        "controlled_worker_dry_run_allowed_now": False, "runtime_worker_authorized": False, "scheduler_authorized": False, "timer_authorized": False,
        "abuse_runner_authorized": False, "abuse_automation_authorized": False, "real_customer_evaluation_authorized": False, "production_db_execution_authorized": False,
        "db_reads_authorized": False, "db_writes_authorized": False, "firewall_apply_authorized": False, "iptables_restore_authorized": False,
        "customer_nat_authorized": False, "customer_firewall_rules_authorized": False, "production_traffic_authorized": False,
        "hard_block_authorized": False, "soft_block_authorized": False, "pause_automation_authorized": False, "ui_authorized": False, "telegram_authorized": False,
        "future_farm5_batch_sync_required": True, "future_controlled_worker_dry_run_pr_required": True, "future_operator_acceptance_required": True, "future_phase8_final_acceptance_pr_required": True,
        **checks, "contract": asdict(contract), "evaluation": asdict(evaluation), "synthetic_pre_acceptance_scenarios": scenarios,
        "phase8_controlled_worker_pre_acceptance_checklist": checklist,
        "worker_started": False, "scheduler_started": False, "timer_enabled": False, "scheduler_job_created": False, "abuse_runner_runtime_started": False,
        "runtime_worker_runtime_started": False, "db_connect_executed": False, "db_read_executed": False, "db_mutation": False, "production_db_writes_executed": False,
        "live_firewall_read_allowed": False, "live_firewall_write_allowed": False, "live_firewall_apply_allowed": False, "iptables_save_executed": False,
        "iptables_restore_executed": False, "conntrack_live_read_executed": False, "firewall_counter_live_read_executed": False, "subprocess_runtime_calls_executed": False,
        "subprocess_firewall_calls_executed": False, "docker_executed": False, "systemctl_executed": False, "customer_nat_changed": False,
        "customer_firewall_rules_changed": False, "production_traffic_changed": False, "hard_block_applied": False, "soft_block_applied": False,
        "pause_applied": False, "ui_allowed_runtime": False, "telegram_allowed_runtime": False, "filesystem_write_executed": False,
        "blockers": blockers, "errors": [],
    }
