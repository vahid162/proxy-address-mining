"""Read-only controlled Phase 11 firewall apply/rollback operational surface."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from mpf.config import MPFConfig
from mpf.services import (
    customer_read_service,
    db_service,
    lane_service,
    phase11_current_controlled_artifact_gate_service,
)

_COMPONENT = "controlled_firewall_apply_rollback_operational_surface"
_NEXT_REQUIRED_STEP = "implement_restart_autostart_proof"
_PHASE_STATUS_PATH = Path("docs/PHASE_STATUS.md")
_CONTROLLED_APPLY_COMPONENTS = (
    "mpf.services.phase11_single_customer_firewall_plan_gate_service",
    "mpf.services.phase11_single_customer_firewall_apply_gate_service",
    "mpf.services.phase11_single_customer_firewall_apply_execution_service",
    "mpf.services.phase11_single_canary_restore_backup_adapter",
    "mpf.services.phase11_single_canary_host_apply_executor",
    "mpf.services.phase11_single_canary_host_apply_primitive",
    "mpf.services.phase11_single_canary_post_apply_verifier",
)
_CONTROLLED_ROLLBACK_COMPONENTS = (
    "mpf.services.phase11e_limited_activation_rollback_package_service",
    "mpf.services.phase11e_limited_activation_rollback_execute_service",
    "mpf.services.phase11_canary_rollback_restore_visibility_service",
)


def _base_report() -> dict[str, Any]:
    """Return the stable fail-closed shape and immutable no-mutation flags."""

    return {
        "component": _COMPONENT,
        "status": "BLOCKED",
        "blockers": [],
        "warnings": [],
        "db_connectivity_status": "BLOCKED",
        "db_connectivity_message": "database status has not been checked",
        "firewall_apply_mode": "unknown",
        "runtime_activation_allowed": "unknown",
        "lanes_visible_from_db": [],
        "active_customers_visible_from_db": [],
        "active_customer_count": 0,
        "controlled_artifact_gate_status": "not_checked",
        "known_controlled_artifacts_present": False,
        "known_controlled_artifacts_coverage": [],
        "unknown_mpf_artifacts": [],
        "unknown_mpf_artifacts_count": 0,
        "forbidden_public_runtime_exposure": False,
        "controlled_apply_workflow_components_checked": [],
        "controlled_rollback_workflow_components_checked": [],
        "restore_point_required": True,
        "firewall_snapshot_backup_required": True,
        "operator_lock_required": True,
        "verify_required": True,
        "rollback_artifact_required": True,
        "package_hash_validation_required": True,
        "operator_confirmation_required": True,
        "rollback_artifact_path_explicit": True,
        "rollback_from_current_db_state_allowed": False,
        "direct_cli_firewall_mutation": False,
        "direct_db_writes_from_cli_handlers": False,
        "apply_execution_allowed_by_default": False,
        "rollback_execution_allowed_by_default": False,
        "firewall_apply_rollback_surface_ready": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "firewall_rollback_performed": False,
        "iptables_restore_executed": False,
        "iptables_save_executed": False,
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
        "final_decision": "FIREWALL_APPLY_ROLLBACK_SURFACE_BLOCKED",
        "next_required_step": _NEXT_REQUIRED_STEP,
    }


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def _component_checks(module_names: tuple[str, ...]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - import visibility must fail closed.
            checks.append({"component": module_name, "status": "missing", "message": str(exc)})
        else:
            checks.append({"component": module_name, "status": "present", "message": "importable"})
    return checks


def _all_components_present(checks: list[dict[str, str]]) -> bool:
    return all(item["status"] == "present" for item in checks)


def _read_phase_status_text(path: Path = _PHASE_STATUS_PATH) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001 - artifact gate will fail closed on missing phase text.
        return ""


def _controlled_artifact_gate_report() -> dict[str, Any]:
    """Run the pure artifact-gate parser without executing iptables-save."""

    return phase11_current_controlled_artifact_gate_service.build_phase11_current_controlled_artifact_gate_report(
        iptables_save_text="",
        ip6tables_save_text="",
        phase_status_text=_read_phase_status_text(),
    )


def build_firewall_apply_rollback_operational_surface_report(
    config: MPFConfig,
    *,
    controlled_artifact_gate_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect the controlled firewall apply/rollback surface using read-only checks only.

    READY means the operator-facing surface can prove that controlled apply and
    rollback workflows are explicit, gated, rollback-aware, restore/lock/verify
    aware, and package/operator-confirmation bound. This command never executes
    iptables-save, iptables-restore, Docker, systemd, conntrack, or DB writes.
    """

    report = _base_report()
    blockers: list[str] = report["blockers"]

    report["firewall_apply_mode"] = config.firewall.apply_mode
    report["runtime_activation_allowed"] = config.proxy.runtime_activation_allowed
    if config.firewall.apply_mode != "plan_only":
        _append_unique(blockers, "firewall_apply_mode_not_plan_only")
    if config.proxy.runtime_activation_allowed:
        _append_unique(blockers, "proxy_runtime_activation_allowed_enabled")

    try:
        database = db_service.status(config)
    except Exception as exc:  # noqa: BLE001 - operator surface must fail closed.
        report["db_connectivity_message"] = str(exc)
        _append_unique(blockers, "database_read_failed")
        return report

    report["db_connectivity_status"] = "OK" if database.ok else "BLOCKED"
    report["db_connectivity_message"] = database.message
    if not database.ok:
        _append_unique(blockers, "database_read_failed")
        return report

    try:
        lanes = lane_service.list_lane_status(config)
    except Exception as exc:  # noqa: BLE001 - read surface must fail closed.
        report["lane_read_message"] = str(exc)
        _append_unique(blockers, "lane_read_failed")
    else:
        report["lane_read_message"] = lanes.message
        db_lanes = [lane for lane in lanes.lanes if lane.source == "db"] if lanes.ok else []
        report["lanes_visible_from_db"] = [lane.name for lane in db_lanes]
        if not lanes.ok:
            _append_unique(blockers, "lane_read_failed")
        elif not db_lanes or len(db_lanes) != len(lanes.lanes):
            _append_unique(blockers, "lanes_not_visible_from_db")

    try:
        customers = customer_read_service.list_customer_status(config, status="active", include_deleted=False, limit=1000)
    except Exception as exc:  # noqa: BLE001 - read surface must fail closed.
        report["active_customer_read_message"] = str(exc)
        _append_unique(blockers, "active_customer_read_failed")
    else:
        report["active_customer_read_message"] = customers.message
        visible_customers = customers.customers if customers.ok else []
        report["active_customers_visible_from_db"] = [customer.customer_key for customer in visible_customers]
        report["active_customer_count"] = len(visible_customers)
        if not customers.ok:
            _append_unique(blockers, "active_customer_read_failed")

    try:
        artifact_gate = controlled_artifact_gate_report if controlled_artifact_gate_report is not None else _controlled_artifact_gate_report()
    except Exception as exc:  # noqa: BLE001 - artifact visibility must fail closed.
        artifact_gate = {"final_decision": "BLOCKED", "unknown_mpf_artifacts": [], "forbidden_public_runtime_exposure": False, "error": str(exc)}
        _append_unique(blockers, "controlled_artifact_gate_read_failed")
    report["controlled_artifact_gate_status"] = str(artifact_gate.get("final_decision", "BLOCKED"))
    report["known_controlled_artifacts_present"] = bool(artifact_gate.get("known_controlled_artifacts_present", False))
    report["known_controlled_artifacts_coverage"] = list(artifact_gate.get("allowed_controlled_artifacts", []))
    report["unknown_mpf_artifacts"] = list(artifact_gate.get("unknown_mpf_artifacts", []))
    report["unknown_mpf_artifacts_count"] = len(report["unknown_mpf_artifacts"])
    report["forbidden_public_runtime_exposure"] = bool(artifact_gate.get("forbidden_public_runtime_exposure", False))
    if report["unknown_mpf_artifacts_count"]:
        _append_unique(blockers, "unknown_mpf_artifacts_detected")
    if report["forbidden_public_runtime_exposure"]:
        _append_unique(blockers, "forbidden_public_runtime_exposure_detected")
    if str(report["controlled_artifact_gate_status"]).startswith("BLOCKED"):
        _append_unique(blockers, "controlled_artifact_gate_blocked")

    apply_checks = _component_checks(_CONTROLLED_APPLY_COMPONENTS)
    rollback_checks = _component_checks(_CONTROLLED_ROLLBACK_COMPONENTS)
    report["controlled_apply_workflow_components_checked"] = apply_checks
    report["controlled_rollback_workflow_components_checked"] = rollback_checks
    if not _all_components_present(apply_checks):
        _append_unique(blockers, "controlled_apply_workflow_component_missing")
    if not _all_components_present(rollback_checks):
        _append_unique(blockers, "controlled_rollback_workflow_component_missing")

    if not blockers:
        report["status"] = "READY"
        report["firewall_apply_rollback_surface_ready"] = True
        report["final_decision"] = "FIREWALL_APPLY_ROLLBACK_SURFACE_READY"
    return report


def build_firewall_apply_rollback_operational_surface_blocked_report(*, blocker: str, message: str) -> dict[str, Any]:
    """Return the standard fail-closed shape when configuration cannot load."""

    report = _base_report()
    report["blockers"] = [blocker]
    report["db_connectivity_message"] = message
    return report
