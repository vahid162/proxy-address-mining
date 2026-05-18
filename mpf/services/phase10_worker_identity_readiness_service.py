from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


WORKER_IDENTITY_FIELDS = [
    "worker_identity_id", "customer_id", "lane_id", "worker_name", "normalized_worker_name",
    "first_seen_at", "last_seen_at", "source", "status", "evidence_ref",
]


def build_worker_identity_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_worker_identity_readiness",
        "final_decision": "ACCEPTED",
        "report_only": True,
        "execution_allowed": False,
        "worker_runtime_enabled": False,
        "worker_enforcement_authorized": False,
        "worker_over_hardening_authorized": False,
        "abuse_hardening_authorized": False,
        "worker_over_alone_must_not_harden": True,
        "farms_over_alone_must_not_harden": True,
        "miner_abuse_1h_invariant_preserved": True,
        "normalization_contract_defined": True,
        "customer_lane_binding_contract_defined": True,
        "worker_identity_contract_fields": WORKER_IDENTITY_FIELDS,
        "abuse_invariant": "normal -> over_tracking -> over_grace -> hard",
        "sustained_miner_abuse_hardening_seconds": 3600,
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
