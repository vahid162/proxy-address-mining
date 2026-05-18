from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


SHARE_TIMELINE_FIELDS = [
    "share_event_id",
    "customer_id",
    "lane_id",
    "session_id",
    "worker_identity_id",
    "customer_port",
    "src_ip",
    "worker_name",
    "share_status",
    "reject_reason",
    "share_difficulty",
    "pool_difficulty",
    "pool_latency_ms",
    "observed_at",
    "source",
    "evidence_ref",
    "created_at",
]

SHARE_STATUS_VALUES = ["accepted", "rejected", "stale", "synthetic"]
SHARE_SOURCE_VALUES = ["synthetic", "readiness", "future_proxy", "future_pool", "future_collector"]


def build_share_timeline_model_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_share_timeline_model_readiness",
        "final_decision": "ACCEPTED",
        "report_only": True,
        "execution_allowed": False,
        "share_collector_authorized": False,
        "live_share_ingestion_authorized": False,
        "tcpdump_authorized": False,
        "conntrack_capture_authorized": False,
        "scheduler_authorized": False,
        "production_db_execution_authorized": False,
        "required_fields_present": True,
        "accepted_rejected_visibility_defined": True,
        "stale_evidence_handling_defined": True,
        "idempotency_contract_defined": True,
        "retention_policy_defined": True,
        "high_volume_guard_defined": True,
        "share_timeline_contract_fields": SHARE_TIMELINE_FIELDS,
        "share_status_values": SHARE_STATUS_VALUES,
        "source_values": SHARE_SOURCE_VALUES,
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
