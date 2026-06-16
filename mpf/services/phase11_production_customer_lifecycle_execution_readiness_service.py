"""Read-only Phase 11 production customer lifecycle execution readiness package."""

from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH

_REQUIRED_SURFACES = ("create", "activate", "renew", "expire", "pause", "block", "unblock")


def build_phase11_production_customer_lifecycle_execution_readiness_report(*, restart_autostart_proof_ready: bool = False) -> dict[str, object]:
    checks = [
        {"name": "active_customers", "status": "missing_or_partial", "requirement": "DB-backed active customer inventory must be supplied by service/repository reads"},
        {"name": "lane_mapping", "status": "missing_or_partial", "requirement": "enabled lanes and BTC mapping must be visible"},
        {"name": "customer_ports", "status": "missing_or_partial", "requirement": "customer public ports must be collision-checked"},
        {"name": "lifecycle_command_surfaces", "status": "present", "required_commands": list(_REQUIRED_SURFACES)},
        {"name": "firewall_plan_apply_verify_rollback_availability", "status": "missing_or_partial", "requirement": "planner/service/adapter package must prove controlled plan/apply/verify/rollback availability"},
        {"name": "audit_event_path_availability", "status": "missing_or_partial", "requirement": "customer lifecycle mutations must record event/audit"},
        {"name": "backup_restore_point_requirement", "status": "missing_or_partial", "requirement": "dangerous lifecycle/firewall actions must require backup/restore point"},
        {"name": "abuse_all_active_customer_coverage", "status": "missing_or_partial", "requirement": "all active customers in all enabled lanes must be covered by the 1h abuse state machine"},
    ]
    blockers = [item["name"] for item in checks if item["status"] == "missing_or_partial"]
    if not restart_autostart_proof_ready:
        blockers.insert(0, "restart_autostart_proof_not_ready")
    return {
        "component": "phase11_production_customer_lifecycle_execution_readiness",
        "repository_version": __version__,
        "phase11_operational_completion_accepted": False,
        "production_customer_lifecycle_execution": "missing_or_partial",
        "readiness_scope": "read_only_plan_only_gate_package",
        "checks": checks,
        "blockers": sorted(set(blockers)),
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
        "final_decision": "BLOCKED_PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_NOT_READY",
        "next_required_step": "implement_production_customer_lifecycle_execution",
    }


def run_phase11_production_customer_lifecycle_execution_readiness_report(config_path: Path = DEFAULT_CONFIG_PATH, *, restart_autostart_proof_ready: bool = False) -> dict[str, object]:
    _ = config_path
    return build_phase11_production_customer_lifecycle_execution_readiness_report(restart_autostart_proof_ready=restart_autostart_proof_ready)
