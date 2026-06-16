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
from mpf.services.phase11_operational_completion_progression import active_progression
from mpf.services.phase11_controlled_artifact_reapply_readiness_service import READY as READINESS_READY, run_phase11_controlled_artifact_reapply_readiness
from mpf.services.phase11_production_customer_lifecycle_execution_readiness_service import run_phase11_production_customer_lifecycle_execution_readiness_report


_MISSING_OR_PARTIAL = "missing_or_partial"


def _next_step(restart_status: str, persistence_plan: dict[str, object] | None, readiness_report: dict[str, object] | None = None) -> str:
    if restart_status == "ready":
        return "implement_production_customer_lifecycle_execution"
    if readiness_report and readiness_report.get("final_decision") == READINESS_READY:
        return "sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5"
    return str(active_progression()["next_required_step"])


def build_phase11_operational_completion_gap_inventory_report(
    evidence_dir: Path | str | None = None,
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    persistence_plan_report: dict[str, object] | None = None,
    readiness_report: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return the expanded post-acceptance Phase 11 gap inventory without mutation."""

    restart_report = build_phase11_restart_autostart_proof_report(evidence_dir) if evidence_dir else None
    restart_status = restart_report["restart_autostart_proof"] if restart_report else _MISSING_OR_PARTIAL
    next_required_step = _next_step(restart_status, persistence_plan_report, readiness_report)
    try:
        lifecycle_readiness = run_phase11_production_customer_lifecycle_execution_readiness_report(
            config_path, evidence_dir=evidence_dir, restart_autostart_proof_ready=restart_status == "ready"
        )
    except Exception:
        from mpf.services.phase11_production_customer_lifecycle_execution_readiness_service import build_phase11_production_customer_lifecycle_execution_readiness_report
        lifecycle_readiness = build_phase11_production_customer_lifecycle_execution_readiness_report(restart_autostart_proof_ready=restart_status == "ready")

    return {
        "component": "phase11_operational_completion_gap_inventory",
        "repository_version": __version__,
        "phase11_accepted": True,
        "phase11_operational_completion_required": True,
        "phase11_operational_completion_scope": "full_cli_production_operations",
        "phase12_start_allowed": False,
        "restart_autostart_proof": restart_status,
        "production_customer_lifecycle_execution": _MISSING_OR_PARTIAL,
        "production_customer_lifecycle_execution_readiness": lifecycle_readiness,
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
            "controlled_filter_packet_path_evidence_capability_implemented": active_progression()["controlled_filter_packet_path_evidence_capability_implemented"],
            "controlled_filter_packet_path_evidence_ready": active_progression()["controlled_filter_packet_path_evidence_ready"],
            "controlled_filter_packet_path_verified": active_progression()["controlled_filter_packet_path_verified"],
            "artifact_graph_binding_ready": active_progression()["artifact_graph_binding_ready"],
            "controlled_artifact_reapply_package_evidence_ready": active_progression()["controlled_artifact_reapply_package_evidence_ready"],
            "live_ready_controlled_artifact_reapply_readiness_final_decision": readiness_report.get("final_decision") if readiness_report else None,
            "live_ready_package_available": readiness_report.get("live_ready_package_available") if readiness_report else (persistence_plan_report.get("live_ready_package_available") if persistence_plan_report else None),
            "readiness_package_id": readiness_report.get("package_id") if readiness_report else None,
            "readiness_package_sha256": readiness_report.get("package_sha256") if readiness_report else None,
            "readiness_blockers": readiness_report.get("blockers", []) if readiness_report else [],
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
    packet_path_evidence_dir: Path | str | None = None,
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
    try:
        readiness_report = run_phase11_controlled_artifact_reapply_readiness(config_path, packet_path_evidence_dir=packet_path_evidence_dir)
    except Exception as exc:  # noqa: BLE001 - readiness summary must fail closed.
        readiness_report = {"final_decision": "BLOCKED_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE", "live_ready_package_available": False, "blockers": ["readiness_summary_failed", str(exc)]}
    return build_phase11_operational_completion_gap_inventory_report(
        evidence_dir,
        config_path=config_path,
        persistence_plan_report=persistence_plan,
        readiness_report=readiness_report,
    )
