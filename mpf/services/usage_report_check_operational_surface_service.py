"""Read-only controlled Phase 11 usage/report/check operational surface check."""

from __future__ import annotations

from typing import Any

from mpf.config import MPFConfig
from mpf.repositories.abuse_operational_postgres_repo import PostgresAbuseOperationalRepo
from mpf.services import abuse_operational_service, customer_read_service, db_service, job_service, lane_service

_USAGE_COMMANDS = (
    "phase7 usage-accounting-contract",
    "phase7 usage-policy-readiness",
    "phase9 usage-visibility",
)
_REPORT_COMMANDS = (
    "db status",
    "jobs status",
    "customer list",
    "abuse status",
    "abuse events",
)
_CHECK_COMMANDS = (
    "customer lifecycle-doctor",
    "production phase11-operational-completion-gap-inventory",
    "production usage-report-check-operational-surface",
)
_DIAGNOSTICS_INPUTS = (
    {"input": "postgresql_schema_runtime_status", "visibility": "blocked"},
    {"input": "postgresql_lanes", "visibility": "blocked"},
    {"input": "postgresql_active_customers", "visibility": "blocked"},
    {"input": "postgresql_job_runs", "visibility": "blocked"},
    {"input": "postgresql_abuse_states", "visibility": "blocked"},
    {"input": "live_firewall_counters", "visibility": "not_available"},
    {"input": "live_conntrack", "visibility": "not_available"},
    {"input": "live_session_evidence", "visibility": "not_yet_collected"},
    {"input": "live_worker_evidence", "visibility": "not_yet_collected"},
    {"input": "live_reject_evidence", "visibility": "not_yet_collected"},
)
_NEXT_REQUIRED_STEP = "implement_controlled_firewall_apply_rollback_workflow"


def _base_report() -> dict[str, Any]:
    """Return the stable fail-closed shape and immutable safety flags."""

    return {
        "component": "controlled_usage_report_check_operational_surface",
        "status": "BLOCKED",
        "blockers": [],
        "warnings": [],
        "db_connectivity_status": "BLOCKED",
        "db_connectivity_message": "database status has not been checked",
        "db_schema_runtime_status": "blocked",
        "db_schema_runtime": {},
        "lanes_visible_from_db": [],
        "active_customers_visible_from_db": [],
        "active_customer_count": 0,
        "active_customer_key_lane_port_visibility": [],
        "job_runs_visibility": "blocked",
        "recent_job_runs_visible": [],
        "recent_job_run_count": 0,
        "usage_commands_checked": list(_USAGE_COMMANDS),
        "report_commands_checked": list(_REPORT_COMMANDS),
        "check_commands_checked": list(_CHECK_COMMANDS),
        "diagnostics_inputs_checked": [dict(item) for item in _DIAGNOSTICS_INPUTS],
        "usage_report_check_surface_ready": False,
        "usage_evidence_source": "not_yet_collected",
        "reject_counter_visibility": "not_yet_collected",
        "session_evidence_visibility": "not_yet_collected",
        "worker_evidence_visibility": "not_yet_collected",
        "abuse_state_visibility": "blocked",
        "customer_lifecycle_visibility": "blocked",
        "recommended_next_action": _NEXT_REQUIRED_STEP,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "firewall_change": "no",
        "nat_change": "no",
        "runtime_change": "no",
        "docker_action_performed": False,
        "systemd_action_performed": False,
        "conntrack_action_performed": False,
        "worker_enforcement_enabled": False,
        "ui_enabled": False,
        "telegram_enabled": False,
        "phase12_start_allowed": False,
        "final_decision": "USAGE_REPORT_CHECK_SURFACE_BLOCKED",
        "next_required_step": _NEXT_REQUIRED_STEP,
    }


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def build_usage_report_check_operational_surface_report(config: MPFConfig) -> dict[str, Any]:
    """Inspect the current controlled surface using PostgreSQL reads only.

    READY means the operator-facing read-only surface exists and honestly shows
    evidence gaps. It does not activate collectors or inspect live firewall,
    conntrack, session, worker, or reject evidence.
    """

    report = _base_report()
    blockers: list[str] = report["blockers"]
    warnings: list[str] = report["warnings"]

    try:
        database = db_service.status(config)
    except Exception as exc:  # noqa: BLE001 - operator surface must fail closed.
        report["db_connectivity_message"] = str(exc)
        blockers.append("database_read_failed")
        return report

    report["db_connectivity_status"] = "OK" if database.ok else "BLOCKED"
    report["db_connectivity_message"] = database.message
    if not database.ok:
        blockers.append("database_read_failed")
        return report

    report["db_schema_runtime_status"] = "available"
    for diagnostic in report["diagnostics_inputs_checked"]:
        if diagnostic["input"].startswith("postgresql_"):
            diagnostic["visibility"] = "available"
    report["db_schema_runtime"] = {
        "alembic_version": database.alembic_version,
        "public_table_count": database.public_table_count,
        "lanes": database.lanes,
        "customers": database.customers,
        "job_runs": database.job_runs,
        "firewall_applies": database.firewall_applies,
        "abuse_states": database.abuse_states,
    }

    try:
        lanes = lane_service.list_lane_status(config)
    except Exception as exc:  # noqa: BLE001 - operator surface must fail closed.
        lanes = None
        report["lane_read_message"] = str(exc)
        blockers.append("lane_read_failed")
    if lanes is not None:
        report["lane_read_message"] = lanes.message
        db_lanes = [lane for lane in lanes.lanes if lane.source == "db"] if lanes.ok else []
        report["lanes_visible_from_db"] = [lane.name for lane in db_lanes]
        if not lanes.ok:
            blockers.append("lane_read_failed")
        elif not db_lanes or len(db_lanes) != len(lanes.lanes):
            blockers.append("lanes_not_visible_from_db")

    try:
        customers = customer_read_service.list_customer_status(config, status="active", include_deleted=False, limit=1000)
    except Exception as exc:  # noqa: BLE001 - operator surface must fail closed.
        customers = None
        report["active_customer_read_message"] = str(exc)
        blockers.append("active_customer_read_failed")
    if customers is not None:
        report["active_customer_read_message"] = customers.message
        visible_customers = customers.customers if customers.ok else []
        report["active_customers_visible_from_db"] = [customer.customer_key for customer in visible_customers]
        report["active_customer_count"] = len(visible_customers)
        report["active_customer_key_lane_port_visibility"] = [
            {"customer_key": customer.customer_key, "lane": customer.lane, "port": customer.port}
            for customer in visible_customers
        ]
        if customers.ok:
            report["customer_lifecycle_visibility"] = "available"
            if not visible_customers:
                warnings.append("no_active_customers_visible_from_db")
        else:
            blockers.append("active_customer_read_failed")

    try:
        jobs = job_service.list_job_status(config, limit=20)
    except Exception as exc:  # noqa: BLE001 - operator surface must fail closed.
        jobs = None
        report["job_runs_message"] = str(exc)
        blockers.append("job_runs_read_failed")
    if jobs is not None:
        report["job_runs_message"] = jobs.message
        if jobs.ok:
            report["job_runs_visibility"] = "available"
            report["recent_job_runs_visible"] = [
                {"id": job.id, "job_name": job.job_name, "status": job.status, "started_at": job.started_at}
                for job in jobs.jobs
            ]
            report["recent_job_run_count"] = len(jobs.jobs)
        else:
            blockers.append("job_runs_read_failed")

    try:
        abuse = abuse_operational_service.status_report(PostgresAbuseOperationalRepo(config))
    except Exception as exc:  # noqa: BLE001 - operator surface must fail closed.
        abuse = {"status": "BLOCKED", "blockers": ["database_read_failed"], "error": str(exc), "states": []}
    report["abuse_state_rows_visible"] = len(abuse.get("states", []))
    if abuse.get("status") == "OK":
        report["abuse_state_visibility"] = "available"
    else:
        report["abuse_state_message"] = abuse.get("error") or abuse.get("note") or "abuse state DB read failed"
        blockers.append("abuse_state_read_failed")

    for warning in (
        "usage_runtime_evidence_not_yet_collected",
        "reject_counter_evidence_not_yet_collected",
        "session_evidence_not_yet_collected",
        "worker_evidence_not_yet_collected",
    ):
        _append_unique(warnings, warning)

    if not blockers:
        report["status"] = "READY"
        report["usage_report_check_surface_ready"] = True
        report["final_decision"] = "USAGE_REPORT_CHECK_SURFACE_READY"
    return report


def build_usage_report_check_operational_surface_blocked_report(*, blocker: str, message: str) -> dict[str, Any]:
    """Return the standard fail-closed shape when configuration cannot load."""

    report = _base_report()
    report["blockers"] = [blocker]
    report["db_connectivity_message"] = message
    return report
