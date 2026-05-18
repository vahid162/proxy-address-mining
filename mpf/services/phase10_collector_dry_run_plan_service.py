from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


def build_collector_dry_run_plan_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_collector_dry_run_plan",
        "final_decision": "ACCEPTED",
        "plan_only": True,
        "execution_allowed": False,
        "would_read_sources": [
            "synthetic_readiness_sample",
            "future_proxy_log",
            "future_pool_event",
            "future_stratum_observer",
        ],
        "would_validate_records": [
            "share_timeline_event_schema",
            "share_status_enum",
            "idempotency_key_uniqueness",
            "observed_at_timestamp_parse",
        ],
        "would_write_tables": [],
        "would_create_job_run": False,
        "would_start_daemon": False,
        "would_schedule_timer": False,
        "would_touch_firewall": False,
        "would_mutate_customers": False,
        "sample_synthetic_events": [
            {
                "share_event_id": "synthetic-share-001",
                "customer_id": 1001,
                "lane_id": "BTC",
                "customer_port": 30001,
                "share_status": "accepted",
                "observed_at": "2026-05-18T00:00:00Z",
                "source": "synthetic",
                "idempotency_key": "share-1001-btc-20260518t000000z-accepted",
            },
            {
                "share_event_id": "synthetic-share-002",
                "customer_id": 1001,
                "lane_id": "BTC",
                "customer_port": 30001,
                "share_status": "rejected",
                "reject_reason": "low_difficulty_share",
                "observed_at": "2026-05-18T00:00:30Z",
                "source": "synthetic",
                "idempotency_key": "share-1001-btc-20260518t000030z-rejected",
            },
        ],
        "validation_rules": [
            "customer_id required",
            "lane_id required",
            "observed_at required",
            "share_status enum accepted/rejected/stale/synthetic",
            "idempotency key required",
        ],
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
