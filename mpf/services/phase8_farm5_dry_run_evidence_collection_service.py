from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_phase8_farm5_dry_run_evidence_collection_report(
    cfg: MPFConfig,
    repo_root: Path | None = None,
) -> dict[str, object]:
    _ = cfg
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")
    runbook = _read(root / "docs/PHASE_8_FARM5_CONTROLLED_WORKER_DRY_RUN_EVIDENCE_COLLECTION.md")

    checks = {
        "farm5_0_1_120_sync_evidence_present": "Phase 8 farm5 0.1.120 Operator Dry-Run Package Sync Evidence" in phase_status and "synced to 0.1.120" in phase_status,
        "repository_version_is_0_1_122": __version__ == "0.1.122",
        "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase8_not_accepted": "does not accept Phase 8" in phase_status,
        "dry_run_evidence_collection_runbook_present": "# Phase 8 farm5 Controlled Worker Dry-Run Evidence Collection" in runbook,
        "runbook_status_not_executed": "Not executed by this PR" in runbook,
        "farm5_0_1_121_sync_required_before_dry_run_evidence": "farm5 synced/tested to 0.1.121" in runbook,
        "operator_invocation_required": "operator explicitly invokes dry-run commands" in runbook,
        "default_command_requires_operator_confirmation": "without --operator-confirmed includes operator_confirmation_required blocker" in runbook,
        "operator_confirmed_command_remains_no_side_effect": "with --operator-confirmed" in runbook and "execution_allowed=false" in runbook,
        "synthetic_only_required": "synthetic_only: true" in runbook,
        "no_silent_skip_required": "no silent skip is allowed" in ai_phase8.lower(),
        "no_work_reporting_required": "no-work" in ai_phase8.lower(),
        "failure_mode_reporting_required": "failure" in ai_phase8.lower(),
        "idempotency_reporting_required": "idempotency" in ai_phase8.lower(),
    }

    blockers: list[str] = [f"{k}_missing_or_failed" for k, ok in checks.items() if not ok]

    checklist = [{"name": k, "passed": bool(v)} for k, v in checks.items()]

    return {
        "component": "phase8_farm5_dry_run_evidence_collection",
        "phase": "Phase 8 — Abuse 1h Core",
        "gate_type": "farm5_controlled_worker_dry_run_evidence_collection_preparation",
        "final_decision": "BLOCKED",
        "evidence_collection_status": "PREPARED_NOT_EXECUTED",
        "authorization_status": "NOT_AUTHORIZED_FOR_RUNTIME_EXECUTION",
        "inspection_only": True,
        "report_only": True,
        "execution_allowed": False,
        "phase8_acceptance_allowed": False,
        "dry_run_evidence_claimed": False,
        "repository_version": __version__,
        "latest_recorded_farm5_sync_evidence": "0.1.120",
        "farm5_0_1_120_sync_evidence_present": checks["farm5_0_1_120_sync_evidence_present"],
        "farm5_0_1_121_sync_required_before_dry_run_evidence": checks["farm5_0_1_121_sync_required_before_dry_run_evidence"],
        "current_state_preserved": checks["current_state_preserved"],
        "phase7_accepted": True,
        "phase8_working": True,
        "phase8_not_accepted": checks["phase8_not_accepted"],
        "dry_run_evidence_collection_runbook_present": checks["dry_run_evidence_collection_runbook_present"],
        "runbook_status_not_executed": checks["runbook_status_not_executed"],
        "operator_invocation_required": checks["operator_invocation_required"],
        "default_command_requires_operator_confirmation": checks["default_command_requires_operator_confirmation"],
        "operator_confirmed_command_remains_no_side_effect": checks["operator_confirmed_command_remains_no_side_effect"],
        "synthetic_only_required": checks["synthetic_only_required"],
        "no_silent_skip_required": checks["no_silent_skip_required"],
        "no_work_reporting_required": checks["no_work_reporting_required"],
        "failure_mode_reporting_required": checks["failure_mode_reporting_required"],
        "idempotency_reporting_required": checks["idempotency_reporting_required"],
        "runtime_worker_authorized": False,"worker_start_authorized": False,"background_worker_authorized": False,"scheduler_authorized": False,"timer_authorized": False,
        "abuse_runner_authorized": False,"real_customer_evaluation_authorized": False,"production_db_execution_authorized": False,"db_reads_authorized": False,"db_writes_authorized": False,
        "firewall_apply_authorized": False,"iptables_restore_authorized": False,"customer_nat_authorized": False,"customer_firewall_rules_authorized": False,"customer_policy_mutation_authorized": False,
        "hard_block_authorized": False,"soft_block_authorized": False,"pause_automation_authorized": False,"production_traffic_authorized": False,"ui_authorized": False,"telegram_authorized": False,
        "future_farm5_dry_run_evidence_pr_required": True,
        "future_phase8_final_acceptance_pr_required": True,
        "phase8_farm5_dry_run_evidence_collection_checklist": checklist,
        "blockers": blockers,
        "errors": [],
    }
