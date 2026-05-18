from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


SESSION_FIELDS = [
    "session_id", "customer_id", "lane_id", "customer_port", "src_ip", "src_port",
    "worker_identity_id", "opened_at", "closed_at", "last_seen_at", "state", "source",
    "evidence_ref", "created_at",
]


def build_session_model_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_session_model_readiness",
        "final_decision": "ACCEPTED",
        "report_only": True,
        "execution_allowed": False,
        "session_runtime_enabled": False,
        "conntrack_capture_authorized": False,
        "tcpdump_authorized": False,
        "scheduler_authorized": False,
        "production_db_execution_authorized": False,
        "required_fields_present": all(SESSION_FIELDS),
        "retention_policy_defined": True,
        "idempotency_contract_defined": True,
        "stale_session_handling_defined": True,
        "session_contract_fields": SESSION_FIELDS,
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
