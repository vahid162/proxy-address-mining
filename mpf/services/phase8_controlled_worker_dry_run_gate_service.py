from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf import __version__


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build_phase8_controlled_worker_dry_run_gate_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")
    gate_doc = _read(root / "docs/PHASE_8_CONTROLLED_WORKER_DRY_RUN_GATE.md")

    checks = {
        "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase7_accepted": "current_accepted_phase: Phase 7" in phase_status,
        "phase8_working": "current_working_phase: Phase 8" in phase_status,
        "phase8_not_accepted": "This evidence does not accept Phase 8." in phase_status,
        "farm5_0_1_118_batch_sync_evidence_present": "Phase 8 farm5 0.1.118 Batched Sync Evidence" in phase_status and "synced to 0.1.118" in phase_status,
        "farm5_0_1_119_sync_required_before_controlled_worker_dry_run": "0.1.119 sync/test evidence is required" in ai_phase8,
        "controlled_worker_dry_run_gate_doc_present": "# Phase 8 Controlled Worker Dry-Run Gate" in gate_doc,
        "controlled_worker_dry_run_gate_prepared": "Status: Draft / Gate Preparation Only" in gate_doc,
    }
    bool_true = {
        "operator_approval_required": True, "kill_switch_required": True, "lock_required": True, "idempotency_required": True,
        "explicit_skip_required": True, "no_silent_skip_required": True, "no_work_reporting_required": True, "failure_mode_reporting_required": True,
        "future_controlled_worker_dry_run_requires_operator": True, "future_controlled_worker_dry_run_requires_0_1_119_sync": True,
        "future_controlled_worker_dry_run_pr_required": True, "future_phase8_final_acceptance_pr_required": True,
    }
    false_flags = {k: False for k in ["runtime_worker_authorized","worker_start_authorized","scheduler_authorized","timer_authorized","abuse_runner_authorized","real_customer_evaluation_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","customer_policy_mutation_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","production_traffic_authorized","ui_authorized","telegram_authorized"]}

    checklist_names = [
        "current_state_preserved","phase7_accepted","phase8_working","phase8_not_accepted","farm5_0_1_118_batch_sync_evidence_present",
        "farm5_0_1_119_sync_required_before_controlled_worker_dry_run","controlled_worker_dry_run_gate_doc_present","controlled_worker_dry_run_gate_prepared",
        "operator_approval_required","kill_switch_required","lock_required","idempotency_required","explicit_skip_required","no_silent_skip_required",
        "no_work_reporting_required","failure_mode_reporting_required"
    ]
    merged = {**checks, **bool_true}
    checklist = [{"item": i, "status": "PASS" if merged.get(i, False) else "BLOCKED"} for i in checklist_names]
    blockers = [f"{i} blocked" for i, ok in checks.items() if not ok]

    return {
        "component": "phase8_controlled_worker_dry_run_gate", "phase": "Phase 8 — Abuse 1h Core", "gate_type": "controlled_worker_dry_run_gate_preparation",
        "final_decision": "BLOCKED", "gate_status": "CONTROLLED_WORKER_DRY_RUN_GATE_PREPARED_NOT_EXECUTABLE",
        "authorization_status": "NOT_AUTHORIZED_FOR_RUNTIME_EXECUTION", "inspection_only": True, "report_only": True,
        "execution_allowed": False, "phase8_acceptance_allowed": False,
        "repository_version": __version__, "latest_recorded_farm5_sync_evidence": "0.1.118",
        **checks, **bool_true, **false_flags,
        "phase8_controlled_worker_dry_run_gate_checklist": checklist,
        "blockers": blockers, "errors": []
    }
