"""Read-only, fail-closed Phase 11 full CLI production operations gap inventory."""

from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH
from mpf.services.phase11_restart_autostart_persistence_fix_service import (
    run_phase11_restart_autostart_persistence_fix_plan,
)
from mpf.services.phase11_restart_autostart_proof_service import (
    build_phase11_restart_autostart_proof_report,
)


_MISSING_OR_PARTIAL = "missing_or_partial"


def _next_step(restart_status: str, persistence_plan: dict[str, object] | None) -> str:
    if restart_status == "ready":
        return "implement_production_customer_lifecycle_execution"
    if not persistence_plan:
        return "fix_restart_autostart_persistence_gap"
    if persistence_plan.get("safety_blockers"):
        return "fix_restart_autostart_persistence_gap"
    if persistence_plan.get("runtime_repair_required") is True:
        return "run_restart_autostart_persistence_fix_on_farm5"
    if persistence_plan.get("controlled_artifact_reapply_required") is True:
        if persistence_plan.get("controlled_artifact_reapply_capability_implemented") is not True:
            return "implement_controlled_artifact_reapply_execute_package"
        if persistence_plan.get("desired_artifact_semantics_complete") is not True or persistence_plan.get("production_execution_available") is not True:
            return "implement_source_backed_controlled_artifact_renderer_and_production_adapters"
        if persistence_plan.get("controlled_artifact_reapply_package_evidence_ready") is not True:
            return "sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5"
        if persistence_plan.get("controlled_artifact_reapply_execution_reviewed") is not True:
            return "review_and_run_controlled_artifact_reapply_on_farm5"
        if persistence_plan.get("controlled_artifact_reapply_execution_verified") is True:
            return "implement_reboot_safe_artifact_recovery_orchestration"
    return "run_controlled_restart_autostart_proof_on_farm5"


def build_phase11_operational_completion_gap_inventory_report(
    evidence_dir: Path | str | None = None,
    *,
    persistence_plan_report: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return the expanded post-acceptance Phase 11 gap inventory without mutation."""

    restart_report = build_phase11_restart_autostart_proof_report(evidence_dir) if evidence_dir else None
    restart_status = restart_report["restart_autostart_proof"] if restart_report else _MISSING_OR_PARTIAL
    next_required_step = _next_step(restart_status, persistence_plan_report)

    return {
        "component": "phase11_operational_completion_gap_inventory",
        "repository_version": __version__,
        "phase11_accepted": True,
        "phase11_operational_completion_required": True,
        "phase11_operational_completion_scope": "full_cli_production_operations",
        "phase12_start_allowed": False,
        "restart_autostart_proof": restart_status,
        "production_customer_lifecycle_execution": _MISSING_OR_PARTIAL,
        "production_firewall_apply_verify_rollback": _MISSING_OR_PARTIAL,
        "production_onboarding_flow": _MISSING_OR_PARTIAL,
        "production_usage_report_check_evidence": _MISSING_OR_PARTIAL,
        "production_abuse_runner": _MISSING_OR_PARTIAL,
        "production_controls_pause_block_expire": _MISSING_OR_PARTIAL,
        "backup_restore_drill": _MISSING_OR_PARTIAL,
        "full_cli_production_operations": _MISSING_OR_PARTIAL,
        "accepted_final_state_required": {
            "production_traffic": "cli_production",
            "customer_onboarding_allowed": "cli_production",
        },
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "restart_autostart_persistence_fix_plan_summary": {
            "final_decision": persistence_plan_report.get("final_decision") if persistence_plan_report else None,
            "safety_blockers": persistence_plan_report.get("safety_blockers", []) if persistence_plan_report else [],
            "runtime_repair_required": persistence_plan_report.get("runtime_repair_required") if persistence_plan_report else None,
            "runtime_repair_reasons": persistence_plan_report.get("runtime_repair_reasons", []) if persistence_plan_report else [],
            "controlled_artifact_reapply_required": persistence_plan_report.get("controlled_artifact_reapply_required") if persistence_plan_report else None,
            "read_only_reapply_foundation_implemented": persistence_plan_report.get("read_only_reapply_foundation_implemented") if persistence_plan_report else None,
            "desired_artifact_semantics_complete": persistence_plan_report.get("desired_artifact_semantics_complete") if persistence_plan_report else None,
            "production_execution_available": persistence_plan_report.get("production_execution_available") if persistence_plan_report else None,
            "live_ready_package_available": persistence_plan_report.get("live_ready_package_available") if persistence_plan_report else None,
            "controlled_artifact_reapply_capability_implemented": persistence_plan_report.get("controlled_artifact_reapply_capability_implemented") if persistence_plan_report else None,
            "controlled_artifact_reapply_execution_available": persistence_plan_report.get("controlled_artifact_reapply_execution_available") if persistence_plan_report else None,
        },
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "final_decision": "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED",
        "next_required_step": next_required_step,
        "restart_autostart_proof_final_decision": restart_report["final_decision"] if restart_report else "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL",
    }


def run_phase11_operational_completion_gap_inventory_report(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    evidence_dir: Path | str | None = None,
) -> dict[str, object]:
    """Read live persistence plan data and render the gap inventory without mutation."""

    try:
        persistence_plan = run_phase11_restart_autostart_persistence_fix_plan(config_path)
    except Exception as exc:  # noqa: BLE001 - inventory must fail closed without traceback.
        persistence_plan = {
            "final_decision": "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN",
            "safety_blockers": ["configuration_or_read_only_inspection_failed"],
            "runtime_repair_required": None,
            "runtime_repair_reasons": [],
            "controlled_artifact_reapply_required": None,
            "controlled_artifact_reapply_execution_available": None,
            "configuration_error": str(exc),
        }
    return build_phase11_operational_completion_gap_inventory_report(
        evidence_dir,
        persistence_plan_report=persistence_plan,
    )
