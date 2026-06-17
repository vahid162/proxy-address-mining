"""Read-only Phase 11 production abuse runner readiness."""

from __future__ import annotations
from pathlib import Path
from typing import Any
from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.repositories.abuse_operational_postgres_repo import (
    PostgresAbuseOperationalRepo,
)
from mpf.services import abuse_operational_service, customer_read_service, lane_service

READY = "production_abuse_runner_ready"
MISSING = "missing_or_partial"


def _state_key(row: Any) -> str | None:
    if isinstance(row, dict):
        return row.get("customer_key") or (
            str(row.get("customer_id")) if row.get("customer_id") is not None else None
        )
    return getattr(row, "customer_key", None) or (
        str(getattr(row, "customer_id", None))
        if getattr(row, "customer_id", None) is not None
        else None
    )


def build_phase11_production_abuse_runner_readiness_report(
    *,
    active_customers: list[Any] | None = None,
    lanes: list[Any] | None = None,
    abuse_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers = []
    enabled = {
        getattr(l, "name", None) for l in (lanes or []) if getattr(l, "enabled", False)
    }
    active = [
        c
        for c in (active_customers or [])
        if getattr(c, "status", None) == "active"
        and getattr(c, "lane", None) in enabled
    ]
    if not enabled:
        blockers.append("no_enabled_lanes_visible")
    if (abuse_status or {}).get("status") != "OK" or (abuse_status or {}).get(
        "blockers"
    ):
        blockers.append("abuse_status_not_ok")
    covered = {_state_key(s) for s in (abuse_status or {}).get("states", [])}
    missing = [
        getattr(c, "customer_key", None) or str(getattr(c, "id", None))
        for c in active
        if (getattr(c, "customer_key", None) or str(getattr(c, "id", None)))
        not in covered
    ]
    if missing:
        blockers.append("abuse_state_coverage_missing:" + ",".join(sorted(missing)))
    ready = not blockers and bool(active)
    return {
        "component": "phase11_production_abuse_runner_readiness",
        "repository_version": __version__,
        "production_abuse_runner": READY if ready else MISSING,
        "production_abuse_runner_ready": ready,
        "active_enabled_lane_customers": [
            getattr(c, "customer_key", None) for c in active
        ],
        "abuse_state_covered_customers": sorted(x for x in covered if x),
        "abuse_invariant": {
            "state_flow": "normal -> over_tracking / over_grace -> hard",
            "sustained_miner_abuse_window_seconds": 3600,
            "farms_over_only_hard_authorized": False,
            "worker_over_only_hard_authorized": False,
            "hard_unhard_execution_allowed": False,
            "hard_unhard_boundary": "controlled_package_gated",
        },
        "blockers": blockers,
        "warnings": [],
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "final_decision": (
            "PRODUCTION_ABUSE_RUNNER_READY"
            if ready
            else "BLOCKED_PRODUCTION_ABUSE_RUNNER_MISSING_OR_PARTIAL"
        ),
        "next_required_step": (
            "production_controls_pause_block_expire"
            if ready
            else "production_abuse_runner"
        ),
    }


def run_phase11_production_abuse_runner_readiness_report(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    try:
        cfg = load_config(config_path)
    except Exception as exc:
        return build_phase11_production_abuse_runner_readiness_report(
            active_customers=[],
            lanes=[],
            abuse_status={
                "status": "BLOCKED",
                "blockers": ["configuration_load_failed", str(exc)],
                "states": [],
            },
        )
    lanes = lane_service.list_lane_status(cfg)
    customers = customer_read_service.list_customer_status(
        cfg, status="active", include_deleted=False, limit=1000
    )
    abuse = abuse_operational_service.status_report(PostgresAbuseOperationalRepo(cfg))
    return build_phase11_production_abuse_runner_readiness_report(
        active_customers=customers.customers if customers.ok else [],
        lanes=lanes.lanes if lanes.ok else [],
        abuse_status=abuse,
    )
