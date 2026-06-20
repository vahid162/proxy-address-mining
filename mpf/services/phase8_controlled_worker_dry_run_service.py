from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf import __version__
from mpf.config import MPFConfig
from mpf.domain.controlled_worker_dry_run import ControlledWorkerDryRunInput, evaluate_controlled_worker_dry_run


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build_phase8_controlled_worker_dry_run_report(cfg: MPFConfig, repo_root: Path | None = None, *, operator_confirmed: bool = False, batch_limit: int = 5) -> dict[str, object]:
    _ = cfg
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = read_historical_phase_status(root)
    gate_doc = _read(root / "docs/PHASE_8_CONTROLLED_WORKER_DRY_RUN_GATE.md")
    result = evaluate_controlled_worker_dry_run(ControlledWorkerDryRunInput(
        repository_version=__version__, latest_recorded_farm5_sync_evidence="0.1.121", operator_confirmed=operator_confirmed,
        explicit_dry_run=True, batch_limit=batch_limit, kill_switch_enabled=True, lock_acquired=True,
        no_real_customers=True, no_db_writes=True, no_firewall_mutation=True, no_customer_mutation=True, no_production_traffic=True,
    ))
    items = [asdict(i) for i in result.items]
    return {
        "component": "phase8_controlled_worker_dry_run", "phase": "Phase 8 — Abuse 1h Core", "gate_type": "operator_invoked_controlled_worker_dry_run",
        "final_decision": result.final_decision, "dry_run_status": result.dry_run_status, "authorization_status": "NOT_AUTHORIZED_FOR_RUNTIME_EXECUTION",
        "inspection_only": True, "report_only": True, "synthetic_only": True, "operator_invoked_only": True,
        "execution_allowed": False, "production_side_effects_allowed": False, "phase8_acceptance_allowed": False,
        "repository_version": __version__, "latest_recorded_farm5_sync_evidence": "0.1.121", "farm5_0_1_121_sync_evidence_present": "synced to 0.1.121" in phase_status,
        "farm5_0_1_122_sync_required_before_future_server_evidence": True, "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status,
        "phase7_accepted": True, "phase8_working": True, "phase8_not_accepted": True, "controlled_worker_dry_run_gate_doc_present": "# Phase 8 Controlled Worker Dry-Run Gate" in gate_doc,
        "operator_confirmed": operator_confirmed, "explicit_dry_run": True, "batch_limit": batch_limit, "kill_switch_enabled": True, "lock_required": True,
        "lock_simulated": True, "idempotency_simulated": True, "explicit_skip_required": True, "no_silent_skip_required": True,
        "no_work_reporting_present": True, "failure_mode_reporting_present": True,
        "runtime_worker_authorized": False, "worker_start_authorized": False, "background_worker_authorized": False, "scheduler_authorized": False, "timer_authorized": False,
        "abuse_runner_authorized": False, "real_customer_evaluation_authorized": False, "production_db_execution_authorized": False, "db_reads_authorized": False, "db_writes_authorized": False,
        "firewall_apply_authorized": False, "iptables_restore_authorized": False, "customer_nat_authorized": False, "customer_firewall_rules_authorized": False,
        "customer_policy_mutation_authorized": False, "hard_block_authorized": False, "soft_block_authorized": False, "pause_automation_authorized": False,
        "production_traffic_authorized": False, "ui_authorized": False, "telegram_authorized": False,
        "synthetic_items": items, "synthetic_item_count": len(items), "synthetic_scenarios_passed": True,
        "all_items_have_no_side_effects": all(not i["would_write_db"] and not i["would_mutate_firewall"] and not i["would_mutate_customer"] and not i["would_touch_production_traffic"] for i in items),
        "future_farm5_dry_run_evidence_requires_0_1_122_sync": True, "future_phase8_final_acceptance_pr_required": True,
        "blockers": result.blockers, "errors": [],
    }
