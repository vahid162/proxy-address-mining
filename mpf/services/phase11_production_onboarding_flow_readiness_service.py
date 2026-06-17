"""Read-only Phase 11 production onboarding flow readiness."""

from __future__ import annotations
from typing import Any
from pathlib import Path
from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.services import customer_read_service, lane_service

READY = "production_onboarding_flow_ready"
MISSING = "missing_or_partial"
_REQUIRED = {"canary-btc-001": ("btc", 20001), "limited-btc-001": ("btc", 20101)}


def build_phase11_production_onboarding_flow_readiness_report(
    *,
    lifecycle_readiness: dict[str, Any] | None = None,
    firewall_readiness: dict[str, Any] | None = None,
    lanes: list[Any] | None = None,
    active_customers: list[Any] | None = None,
    gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gates = gates or {
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
    }
    blockers = []
    if (lifecycle_readiness or {}).get(
        "production_customer_lifecycle_execution"
    ) != "controlled_execution_evidence_ready":
        blockers.append("lifecycle_execution_evidence_not_ready")
    if (firewall_readiness or {}).get(
        "production_firewall_apply_verify_rollback"
    ) != "production_firewall_apply_verify_rollback_ready":
        blockers.append("firewall_apply_verify_rollback_not_ready")
    enabled_lanes = {
        getattr(l, "name", None) for l in (lanes or []) if getattr(l, "enabled", False)
    }
    if "btc" not in enabled_lanes:
        blockers.append("btc_lane_not_enabled")
    seen = {
        getattr(c, "customer_key", None): (
            getattr(c, "lane", None),
            getattr(c, "port", None),
            getattr(c, "status", None),
        )
        for c in (active_customers or [])
    }
    for key, (lane, port) in _REQUIRED.items():
        if seen.get(key) != (lane, port, "active"):
            blockers.append(
                f"required_active_customer_missing_or_mismatched:{key}:{lane}:{port}"
            )
    expected = {
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
    }
    for k, v in expected.items():
        if gates.get(k) != v:
            blockers.append(f"unsafe_gate_flag:{k}")
    ready = not blockers
    return {
        "component": "phase11_production_onboarding_flow_readiness",
        "repository_version": __version__,
        "production_onboarding_flow": READY if ready else MISSING,
        "production_onboarding_flow_ready": ready,
        "required_customers": [
            {"customer_key": k, "lane": v[0], "port": v[1], "status": "active"}
            for k, v in _REQUIRED.items()
        ],
        "active_customers_visible_from_db": [
            {
                "customer_key": getattr(c, "customer_key", None),
                "lane": getattr(c, "lane", None),
                "port": getattr(c, "port", None),
                "status": getattr(c, "status", None),
            }
            for c in (active_customers or [])
        ],
        "enabled_lanes": sorted(enabled_lanes),
        "blockers": blockers,
        "warnings": [],
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        **expected,
        "final_decision": (
            "PRODUCTION_ONBOARDING_FLOW_READY"
            if ready
            else "BLOCKED_PRODUCTION_ONBOARDING_FLOW_MISSING_OR_PARTIAL"
        ),
        "next_required_step": (
            "production_usage_report_check_evidence"
            if ready
            else "production_onboarding_flow"
        ),
    }


def run_phase11_production_onboarding_flow_readiness_report(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    lifecycle_readiness: dict[str, Any] | None = None,
    firewall_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        cfg = load_config(config_path)
    except Exception as exc:
        return build_phase11_production_onboarding_flow_readiness_report(
            lifecycle_readiness=lifecycle_readiness,
            firewall_readiness=firewall_readiness,
            lanes=[],
            active_customers=[],
            gates={
                "production_traffic": "controlled_cli_limited",
                "customer_onboarding_allowed": "controlled_cli_limited",
                "phase12_start_allowed": False,
                "worker_enforcement_allowed": "no",
                "ui_allowed": "no",
                "telegram_allowed": "no",
            },
        ) | {
            "blockers": ["configuration_load_failed", str(exc)],
            "final_decision": "BLOCKED_PRODUCTION_ONBOARDING_FLOW_MISSING_OR_PARTIAL",
        }
    lanes = lane_service.list_lane_status(cfg)
    customers = customer_read_service.list_customer_status(
        cfg, status="active", include_deleted=False, limit=1000
    )
    return build_phase11_production_onboarding_flow_readiness_report(
        lifecycle_readiness=lifecycle_readiness,
        firewall_readiness=firewall_readiness,
        lanes=lanes.lanes if lanes.ok else [],
        active_customers=customers.customers if customers.ok else [],
    )
