from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


def build_worker_cycle_dry_run_plan_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_worker_cycle_dry_run_plan",
        "final_decision": "ACCEPTED",
        "plan_only": True,
        "dry_run_only": True,
        "execution_allowed": False,
        "would_read_sources": [
            "synthetic_session_sample",
            "synthetic_worker_identity_sample",
            "synthetic_worker_policy_sample",
            "synthetic_share_timeline_sample",
        ],
        "would_validate": [
            "current phase gate",
            "config safety gate",
            "scheduler lock availability",
            "idempotency key",
            "no silent skip contract",
            "failure mode reporting",
            "abuse invariant preservation",
        ],
        "would_write_tables": [],
        "would_create_job_run": False,
        "would_acquire_scheduler_lock": False,
        "would_start_daemon": False,
        "would_schedule_timer": False,
        "would_touch_firewall": False,
        "would_mutate_customers": False,
        "would_harden_abuse_state": False,
        "synthetic_cycle_steps": [
            "load synthetic sessions",
            "load synthetic worker identities",
            "evaluate synthetic worker policy in report_only mode",
            "read synthetic share timeline events",
            "build non-mutating worker-cycle summary",
            "emit report only",
        ],
        "sample_cycle_result": {
            "evaluated_sessions": 2,
            "evaluated_workers": 2,
            "accepted_shares": 1,
            "rejected_shares": 1,
            "policy_violations": 0,
            "hardening_actions": 0,
            "firewall_actions": 0,
            "customer_mutations": 0,
        },
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
