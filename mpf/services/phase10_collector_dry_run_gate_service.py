from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


COLLECTOR_DRY_RUN_CONTRACT = {
    "collector_name": "phase10_share_timeline_collector",
    "mode": "dry_run_only",
    "input_sources": [
        "synthetic_readiness_sample",
        "future_proxy_log",
        "future_pool_event",
        "future_stratum_observer",
    ],
    "output_targets": ["report_only", "future_share_timeline_table"],
    "lock_required": True,
    "job_runs_required": True,
    "idempotency_required": True,
    "retention_required": True,
    "kill_switch_required": True,
    "operator_confirmation_required_for_future_runtime": True,
}


def build_collector_dry_run_gate_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_collector_dry_run_gate",
        "final_decision": "ACCEPTED",
        "report_only": True,
        "dry_run_only": True,
        "execution_allowed": False,
        "collector_daemon_authorized": False,
        "scheduler_authorized": False,
        "timer_authorized": False,
        "background_loop_authorized": False,
        "live_capture_authorized": False,
        "live_share_ingestion_authorized": False,
        "production_db_execution_authorized": False,
        "db_writes_authorized": False,
        "firewall_apply_authorized": False,
        "abuse_automation_authorized": False,
        "customer_mutation_authorized": False,
        "job_runs_logging_contract_defined": True,
        "scheduler_lock_contract_defined": True,
        "no_silent_skip_contract_defined": True,
        "failure_mode_reporting_defined": True,
        "stale_input_behavior_defined": True,
        "collector_dry_run_contract": COLLECTOR_DRY_RUN_CONTRACT,
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
