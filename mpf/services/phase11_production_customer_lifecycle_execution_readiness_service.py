"""Read-only Phase 11 production customer lifecycle execution readiness package."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.services import (
    abuse_operational_service,
    customer_lifecycle_operational_surface_service,
    firewall_apply_rollback_operational_surface_service,
    usage_report_check_operational_surface_service,
)
from mpf.repositories.abuse_operational_postgres_repo import PostgresAbuseOperationalRepo
from mpf.services.phase11_restart_autostart_proof_service import build_phase11_restart_autostart_proof_report
from mpf.services.phase11_production_customer_lifecycle_execution_service import READY as LIFECYCLE_EXEC_READY, verify as verify_lifecycle_execution

_REQUIRED_SURFACES = ("create", "activate", "renew", "expire", "pause", "block", "unblock")
_ENV_EXPECTED_BACKEND_TARGET = "MPF_EXPECTED_BACKEND_TARGET"


def _status(name: str, status: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "status": status, **extra}


def _env_expected_backend_target() -> str | None:
    value = os.environ.get(_ENV_EXPECTED_BACKEND_TARGET, "").strip()
    return value or None


def build_phase11_production_customer_lifecycle_execution_readiness_report(
    *,
    customer_lifecycle_report: dict[str, Any] | None = None,
    firewall_surface_report: dict[str, Any] | None = None,
    usage_surface_report: dict[str, Any] | None = None,
    restart_report: dict[str, Any] | None = None,
    abuse_report: dict[str, Any] | None = None,
    restart_autostart_proof_ready: bool = False,
    lifecycle_execution_evidence: dict[str, Any] | None = None,
) -> dict[str, object]:
    lifecycle_ready = (customer_lifecycle_report or {}).get("status") == "READY"
    firewall_ready = (firewall_surface_report or {}).get("status") == "READY"
    usage_ready = (usage_surface_report or {}).get("status") == "READY"
    restart_ready = restart_autostart_proof_ready or (restart_report or {}).get("restart_autostart_proof") == "ready" or (restart_report or {}).get("final_decision") == "RESTART_AUTOSTART_PROOF_READY"
    abuse_ok = (abuse_report or {}).get("status") == "OK"
    active_count = int((customer_lifecycle_report or {}).get("active_customer_count") or 0)
    abuse_states = (abuse_report or {}).get("states") or []
    abuse_covers_active = abuse_ok and active_count > 0 and len(abuse_states) >= active_count
    lifecycle_evidence_ready = (lifecycle_execution_evidence or {}).get("final_decision") == LIFECYCLE_EXEC_READY

    checks = [
        _status("active_customers", "present" if lifecycle_ready and active_count > 0 else "missing_or_partial", source_final_decision=(customer_lifecycle_report or {}).get("final_decision"), active_customer_count=active_count, active_customers=(customer_lifecycle_report or {}).get("active_customers_visible_from_db", [])),
        _status("lane_mapping", "present" if lifecycle_ready and (customer_lifecycle_report or {}).get("lanes_visible_from_db") else "missing_or_partial", lanes=(customer_lifecycle_report or {}).get("lanes_visible_from_db", [])),
        _status("customer_ports", "present" if lifecycle_ready and active_count > 0 else "missing_or_partial", requirement="customer public ports visible through DB-backed customer lifecycle surface"),
        _status("lifecycle_command_surfaces", "present" if lifecycle_ready else "missing_or_partial", required_commands=list(_REQUIRED_SURFACES)),
        _status("restart_autostart_proof", "ready" if restart_ready else "missing_or_partial", source_final_decision=(restart_report or {}).get("final_decision")),
        _status("usage_report_check_surface", "ready" if usage_ready else "missing_or_partial", source_final_decision=(usage_surface_report or {}).get("final_decision"), usage_evidence_acceptance="separate_not_accepted_by_this_check"),
        _status("firewall_plan_apply_verify_rollback_availability", "ready" if firewall_ready else ("present" if firewall_surface_report and not (firewall_surface_report.get("unknown_mpf_artifacts") or []) else "missing_or_partial"), source_final_decision=(firewall_surface_report or {}).get("final_decision"), blockers=(firewall_surface_report or {}).get("blockers", []), expected_backend_target=(firewall_surface_report or {}).get("expected_backend_target")),
        _status("audit_event_path_availability", "ready" if lifecycle_evidence_ready else "missing_or_partial", requirement="actual controlled lifecycle execution evidence must prove audit/event writes"),
        _status("backup_restore_point_requirement", "ready" if lifecycle_evidence_ready else "missing_or_partial", requirement="actual controlled lifecycle/firewall execution evidence must prove backup/restore drill"),
        _status("abuse_all_active_customer_coverage", "present" if abuse_covers_active else "missing_or_partial", abuse_status=(abuse_report or {}).get("status"), active_customer_count=active_count, visible_abuse_state_rows=len(abuse_states), diagnostic="mpf db status abuse_states counts persisted abuse_states rows; mpf abuse status reports active customer abuse visibility rows synthesized from active customers plus persisted state where present"),
    ]
    blockers = [item["name"] for item in checks if item["status"] == "missing_or_partial"]
    lifecycle_blockers = [b for b in blockers if b in {"audit_event_path_availability", "backup_restore_point_requirement"}]
    lifecycle_final_decision = (
        "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"
        if lifecycle_evidence_ready and not lifecycle_blockers
        else "BLOCKED_PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_NOT_READY"
    )
    return {
        "component": "phase11_production_customer_lifecycle_execution_readiness",
        "repository_version": __version__,
        "phase11_operational_completion_accepted": False,
        "production_customer_lifecycle_execution": "controlled_execution_evidence_ready" if lifecycle_evidence_ready else "missing_or_partial",
        "production_onboarding_flow": "missing_or_partial",
        "production_abuse_runner": "missing_or_partial",
        "backup_restore_drill": "missing_or_partial",
        "full_cli_production_operations": "missing_or_partial",
        "readiness_scope": "read_only_aggregated_operational_surfaces",
        "source_reports": {"customer_lifecycle": customer_lifecycle_report, "firewall_apply_rollback": firewall_surface_report, "usage_report_check": usage_surface_report, "restart_autostart_proof": restart_report, "abuse_status": abuse_report, "lifecycle_execution_evidence": lifecycle_execution_evidence},
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
        "final_decision": lifecycle_final_decision,
        "next_required_step": "production_firewall_apply_verify_rollback" if lifecycle_evidence_ready else "implement_production_customer_lifecycle_execution",
    }


def run_phase11_production_customer_lifecycle_execution_readiness_report(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    evidence_dir: Path | str | None = None,
    expected_backend_target: str | None = None,
    restart_autostart_proof_ready: bool = False,
    lifecycle_execution_evidence: dict[str, Any] | None = None,
    lifecycle_execution_evidence_json: Path | str | None = None,
) -> dict[str, object]:
    cfg = load_config(config_path)
    resolved_expected_backend_target = expected_backend_target or _env_expected_backend_target()
    lifecycle = customer_lifecycle_operational_surface_service.build_customer_lifecycle_operational_surface_report(cfg)
    firewall = firewall_apply_rollback_operational_surface_service.build_firewall_apply_rollback_operational_surface_report(
        cfg,
        expected_backend_target=resolved_expected_backend_target,
    )
    if resolved_expected_backend_target is not None:
        firewall["expected_backend_target"] = resolved_expected_backend_target
    usage = usage_report_check_operational_surface_service.build_usage_report_check_operational_surface_report(cfg)
    restart = build_phase11_restart_autostart_proof_report(evidence_dir) if evidence_dir else None
    abuse = abuse_operational_service.status_report(PostgresAbuseOperationalRepo(cfg))
    if lifecycle_execution_evidence_json is not None:
        lifecycle_execution_evidence = verify_lifecycle_execution(Path(lifecycle_execution_evidence_json), config_path)
    return build_phase11_production_customer_lifecycle_execution_readiness_report(customer_lifecycle_report=lifecycle, firewall_surface_report=firewall, usage_surface_report=usage, restart_report=restart, abuse_report=abuse, restart_autostart_proof_ready=restart_autostart_proof_ready, lifecycle_execution_evidence=lifecycle_execution_evidence)
