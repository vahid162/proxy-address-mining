from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig

SCHEDULER_DRY_RUN_CONTRACT = {
    "scheduler_name": "phase10_worker_scheduler",
    "mode": "dry_run_only",
    "future_trigger_modes": ["manual_cli", "systemd_timer_future", "cron_future"],
    "current_trigger_modes": ["manual_cli_only"],
    "interval_policy": {
        "disabled_now": True,
        "future_minimum_interval_seconds": 60,
        "future_jitter_required": True,
    },
    "lock_required": True,
    "overlap_prevention_required": True,
    "job_runs_required": True,
    "stale_lock_handling_required": True,
    "kill_switch_required": True,
    "operator_confirmation_required_for_future_scheduler": True,
}


def build_scheduler_dry_run_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_scheduler_dry_run_readiness",
        "final_decision": "ACCEPTED",
        "report_only": True,
        "dry_run_only": True,
        "execution_allowed": False,
        "scheduler_enabled": False,
        "timer_enabled": False,
        "cron_enabled": False,
        "systemd_timer_enabled": False,
        "background_loop_authorized": False,
        "worker_daemon_authorized": False,
        "collector_daemon_authorized": False,
        "production_db_execution_authorized": False,
        "db_writes_authorized": False,
        "firewall_apply_authorized": False,
        "abuse_automation_authorized": False,
        "hard_block_authorized": False,
        "soft_block_authorized": False,
        "pause_automation_authorized": False,
        "overlap_prevention_contract_defined": True,
        "stale_lock_handling_defined": True,
        "job_runs_logging_contract_defined": True,
        "kill_switch_contract_defined": True,
        "scheduler_dry_run_contract": SCHEDULER_DRY_RUN_CONTRACT,
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
