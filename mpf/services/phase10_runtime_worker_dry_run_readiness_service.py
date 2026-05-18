from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig

RUNTIME_WORKER_DRY_RUN_CONTRACT = {
    "worker_name": "phase10_policy_share_timeline_worker",
    "mode": "dry_run_only",
    "reads": [
        "synthetic_session_sample",
        "synthetic_worker_identity_sample",
        "synthetic_worker_policy_sample",
        "synthetic_share_timeline_sample",
    ],
    "writes": ["none"],
    "future_writes": ["job_runs", "worker_cycle_events", "share_timeline_rollups", "abuse_observations"],
    "lock_required": True,
    "job_runs_required": True,
    "idempotency_required": True,
    "no_silent_skip_required": True,
    "failure_mode_reporting_required": True,
    "kill_switch_required": True,
    "operator_confirmation_required_for_future_runtime": True,
}


def build_runtime_worker_dry_run_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_runtime_worker_dry_run_readiness",
        "final_decision": "ACCEPTED",
        "report_only": True,
        "dry_run_only": True,
        "execution_allowed": False,
        "worker_daemon_authorized": False,
        "worker_runtime_authorized": False,
        "scheduler_authorized": False,
        "timer_authorized": False,
        "background_loop_authorized": False,
        "collector_daemon_authorized": False,
        "production_db_execution_authorized": False,
        "db_writes_authorized": False,
        "firewall_apply_authorized": False,
        "abuse_automation_authorized": False,
        "hard_block_authorized": False,
        "soft_block_authorized": False,
        "pause_automation_authorized": False,
        "customer_mutation_authorized": False,
        "no_silent_skip_contract_defined": True,
        "failure_mode_reporting_defined": True,
        "idempotency_contract_defined": True,
        "scheduler_lock_contract_defined": True,
        "kill_switch_contract_defined": True,
        "runtime_worker_dry_run_contract": RUNTIME_WORKER_DRY_RUN_CONTRACT,
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
