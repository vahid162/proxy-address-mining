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
from mpf.services.phase11_controlled_artifact_reapply_readiness_service import (
    READY as READINESS_READY,
    run_phase11_controlled_artifact_reapply_readiness,
)
from mpf.services.phase11_production_customer_lifecycle_execution_readiness_service import (
    run_phase11_production_customer_lifecycle_execution_readiness_report,
)
from mpf.services.phase11_production_firewall_apply_verify_rollback_readiness_service import (
    build_production_firewall_apply_verify_rollback_readiness_report,
    READY as FIREWALL_READY,
)
from mpf.services.phase11_production_onboarding_flow_readiness_service import (
    run_phase11_production_onboarding_flow_readiness_report,
    READY as ONBOARDING_READY,
)
from mpf.services.usage_report_check_operational_surface_service import (
    build_usage_report_check_operational_surface_report,
)
from mpf.services.phase11_production_abuse_runner_readiness_service import (
    run_phase11_production_abuse_runner_readiness_report,
    READY as ABUSE_RUNNER_READY,
)
from mpf.services.phase11_evidence_contract_readiness_service import (
    build_contract_readiness_report,
)
from mpf.config import load_config

_MISSING_OR_PARTIAL = "missing_or_partial"


def _next_step(
    restart_status: str,
    persistence_plan: dict[str, object] | None,
    readiness_report: dict[str, object] | None = None,
    lifecycle_readiness: dict[str, object] | None = None,
) -> str:
    if (
        lifecycle_readiness
        and lifecycle_readiness.get("production_customer_lifecycle_execution")
        == "controlled_execution_evidence_ready"
    ):
        return "production_firewall_apply_verify_rollback"
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
    lifecycle_execution_evidence_json: Path | str | None = None,
    firewall_completion_evidence_dir: Path | str | None = None,
    onboarding_readiness: dict[str, object] | None = None,
    usage_report_check_surface: dict[str, object] | None = None,
    abuse_runner_readiness: dict[str, object] | None = None,
    controls_readiness: dict[str, object] | None = None,
    backup_restore_readiness: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return the expanded post-acceptance Phase 11 gap inventory without mutation."""

    restart_report = (
        build_phase11_restart_autostart_proof_report(evidence_dir)
        if evidence_dir
        else None
    )
    restart_status = (
        restart_report["restart_autostart_proof"]
        if restart_report
        else _MISSING_OR_PARTIAL
    )
    try:
        lifecycle_readiness = (
            run_phase11_production_customer_lifecycle_execution_readiness_report(
                config_path,
                evidence_dir=evidence_dir,
                restart_autostart_proof_ready=restart_status == "ready",
                lifecycle_execution_evidence_json=lifecycle_execution_evidence_json,
            )
        )
    except Exception:
        from mpf.services.phase11_production_customer_lifecycle_execution_readiness_service import (
            build_phase11_production_customer_lifecycle_execution_readiness_report,
        )

        lifecycle_readiness = (
            build_phase11_production_customer_lifecycle_execution_readiness_report(
                restart_autostart_proof_ready=restart_status == "ready"
            )
        )
    lifecycle_item = (
        "controlled_execution_evidence_ready"
        if lifecycle_readiness.get("production_customer_lifecycle_execution")
        == "controlled_execution_evidence_ready"
        else _MISSING_OR_PARTIAL
    )
    firewall_completion = (
        build_production_firewall_apply_verify_rollback_readiness_report(
            firewall_completion_evidence_dir
        )
        if firewall_completion_evidence_dir
        else None
    )
    firewall_item = (
        FIREWALL_READY
        if firewall_completion
        and firewall_completion.get("production_firewall_apply_verify_rollback")
        == FIREWALL_READY
        else _MISSING_OR_PARTIAL
    )
    if (
        onboarding_readiness is None
        and lifecycle_item == "controlled_execution_evidence_ready"
        and firewall_item == FIREWALL_READY
    ):
        try:
            onboarding_readiness = (
                run_phase11_production_onboarding_flow_readiness_report(
                    config_path,
                    lifecycle_readiness=lifecycle_readiness,
                    firewall_readiness=firewall_completion,
                )
            )
        except Exception as exc:
            onboarding_readiness = {
                "production_onboarding_flow": _MISSING_OR_PARTIAL,
                "blockers": ["onboarding_readiness_failed", str(exc)],
                "mutation_performed": False,
            }
    onboarding_item = (
        ONBOARDING_READY
        if (onboarding_readiness or {}).get("production_onboarding_flow")
        == ONBOARDING_READY
        else _MISSING_OR_PARTIAL
    )
    if usage_report_check_surface is None:
        try:
            usage_report_check_surface = (
                build_usage_report_check_operational_surface_report(
                    load_config(config_path)
                )
            )
        except Exception as exc:
            usage_report_check_surface = {
                "usage_report_check_surface_ready": False,
                "final_decision": "BLOCKED_USAGE_REPORT_CHECK_SURFACE",
                "blockers": ["usage_surface_failed", str(exc)],
                "warnings": [],
            }
    usage_item = (
        "production_usage_report_check_evidence_ready"
        if usage_report_check_surface.get("usage_report_check_surface_ready") is True
        and usage_report_check_surface.get("final_decision")
        == "USAGE_REPORT_CHECK_SURFACE_READY"
        and not usage_report_check_surface.get("blockers")
        else _MISSING_OR_PARTIAL
    )
    if (
        abuse_runner_readiness is None
        and onboarding_item == ONBOARDING_READY
        and usage_item != _MISSING_OR_PARTIAL
    ):
        try:
            abuse_runner_readiness = (
                run_phase11_production_abuse_runner_readiness_report(config_path)
            )
        except Exception as exc:
            abuse_runner_readiness = {
                "production_abuse_runner": _MISSING_OR_PARTIAL,
                "blockers": ["abuse_runner_readiness_failed", str(exc)],
                "mutation_performed": False,
            }
    abuse_item = (
        ABUSE_RUNNER_READY
        if (abuse_runner_readiness or {}).get("production_abuse_runner")
        == ABUSE_RUNNER_READY
        else _MISSING_OR_PARTIAL
    )
    controls_readiness = controls_readiness or build_contract_readiness_report(
        "production_controls_pause_block_expire", evidence_dir
    )
    backup_restore_readiness = (
        backup_restore_readiness
        or build_contract_readiness_report("backup_restore_drill", evidence_dir)
    )
    controls_item = controls_readiness.get(
        "production_controls_pause_block_expire", _MISSING_OR_PARTIAL
    )
    backup_item = backup_restore_readiness.get(
        "backup_restore_drill", _MISSING_OR_PARTIAL
    )
    order = [
        ("production_onboarding_flow", onboarding_item),
        ("production_usage_report_check_evidence", usage_item),
        ("production_abuse_runner", abuse_item),
        ("production_controls_pause_block_expire", controls_item),
        ("backup_restore_drill", backup_item),
    ]
    next_required_step = _next_step(
        restart_status, persistence_plan_report, readiness_report, lifecycle_readiness
    )
    prerequisites_ready = (
        restart_status == "ready"
        and lifecycle_item == "controlled_execution_evidence_ready"
        and firewall_item == FIREWALL_READY
    )
    if prerequisites_ready:
        next_required_step = "final_phase11_operational_completion_acceptance"
        for name, status in order:
            if status == _MISSING_OR_PARTIAL:
                next_required_step = name
                break
    full_ready = prerequisites_ready and all(
        status != _MISSING_OR_PARTIAL for _, status in order
    )

    return {
        "component": "phase11_operational_completion_gap_inventory",
        "repository_version": __version__,
        "phase11_accepted": True,
        "phase11_operational_completion_required": True,
        "phase11_operational_completion_scope": "full_cli_production_operations",
        "phase12_start_allowed": False,
        "restart_autostart_proof": restart_status,
        "production_customer_lifecycle_execution": lifecycle_item,
        "production_customer_lifecycle_execution_readiness": lifecycle_readiness,
        "production_firewall_apply_verify_rollback": firewall_item,
        "production_firewall_apply_verify_rollback_readiness": firewall_completion,
        "production_onboarding_flow": onboarding_item,
        "production_onboarding_flow_readiness": onboarding_readiness,
        "production_usage_report_check_evidence": usage_item,
        "usage_report_check_operational_surface": usage_report_check_surface,
        "production_usage_report_check_warnings": (
            usage_report_check_surface.get("warnings", [])
            if usage_report_check_surface
            else []
        ),
        "production_abuse_runner": abuse_item,
        "production_abuse_runner_readiness": abuse_runner_readiness,
        "production_controls_pause_block_expire": controls_item,
        "production_controls_pause_block_expire_readiness": controls_readiness,
        "backup_restore_drill": backup_item,
        "backup_restore_drill_readiness": backup_restore_readiness,
        "full_cli_production_operations": (
            "full_cli_production_operations_ready"
            if full_ready
            else _MISSING_OR_PARTIAL
        ),
        "accepted_final_state_required": {
            "production_traffic": "cli_production",
            "customer_onboarding_allowed": "cli_production",
        },
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "restart_autostart_persistence_fix_plan_summary": {
            "final_decision": (
                persistence_plan_report.get("final_decision")
                if persistence_plan_report
                else None
            ),
            "safety_blockers": (
                persistence_plan_report.get("safety_blockers", [])
                if persistence_plan_report
                else []
            ),
            "runtime_repair_required": (
                persistence_plan_report.get("runtime_repair_required")
                if persistence_plan_report
                else None
            ),
            "runtime_repair_reasons": (
                persistence_plan_report.get("runtime_repair_reasons", [])
                if persistence_plan_report
                else []
            ),
            "controlled_artifact_reapply_required": (
                persistence_plan_report.get("controlled_artifact_reapply_required")
                if persistence_plan_report
                else None
            ),
            "read_only_reapply_foundation_implemented": (
                persistence_plan_report.get("read_only_reapply_foundation_implemented")
                if persistence_plan_report
                else None
            ),
            "desired_artifact_semantics_complete": (
                persistence_plan_report.get("desired_artifact_semantics_complete")
                if persistence_plan_report
                else None
            ),
            "production_execution_available": (
                persistence_plan_report.get("production_execution_available")
                if persistence_plan_report
                else None
            ),
            "live_ready_package_available": (
                persistence_plan_report.get("live_ready_package_available")
                if persistence_plan_report
                else None
            ),
            "controlled_artifact_reapply_capability_implemented": (
                persistence_plan_report.get(
                    "controlled_artifact_reapply_capability_implemented"
                )
                if persistence_plan_report
                else None
            ),
            "controlled_artifact_reapply_execution_available": (
                persistence_plan_report.get(
                    "controlled_artifact_reapply_execution_available"
                )
                if persistence_plan_report
                else None
            ),
            "controlled_filter_packet_path_evidence_capability_implemented": active_progression()[
                "controlled_filter_packet_path_evidence_capability_implemented"
            ],
            "controlled_filter_packet_path_evidence_ready": active_progression()[
                "controlled_filter_packet_path_evidence_ready"
            ],
            "controlled_filter_packet_path_verified": active_progression()[
                "controlled_filter_packet_path_verified"
            ],
            "artifact_graph_binding_ready": active_progression()[
                "artifact_graph_binding_ready"
            ],
            "controlled_artifact_reapply_package_evidence_ready": active_progression()[
                "controlled_artifact_reapply_package_evidence_ready"
            ],
            "live_ready_controlled_artifact_reapply_readiness_final_decision": (
                readiness_report.get("final_decision") if readiness_report else None
            ),
            "live_ready_package_available": (
                readiness_report.get("live_ready_package_available")
                if readiness_report
                else (
                    persistence_plan_report.get("live_ready_package_available")
                    if persistence_plan_report
                    else None
                )
            ),
            "readiness_package_id": (
                readiness_report.get("package_id") if readiness_report else None
            ),
            "readiness_package_sha256": (
                readiness_report.get("package_sha256") if readiness_report else None
            ),
            "readiness_blockers": (
                readiness_report.get("blockers", []) if readiness_report else []
            ),
        },
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "final_decision": "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED",
        "next_required_step": next_required_step,
        "restart_autostart_proof_final_decision": (
            restart_report["final_decision"]
            if restart_report
            else "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"
        ),
    }


def run_phase11_operational_completion_gap_inventory_report(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    evidence_dir: Path | str | None = None,
    packet_path_evidence_dir: Path | str | None = None,
    lifecycle_execution_evidence_json: Path | str | None = None,
    firewall_completion_evidence_dir: Path | str | None = None,
    onboarding_readiness: dict[str, object] | None = None,
    usage_report_check_surface: dict[str, object] | None = None,
    abuse_runner_readiness: dict[str, object] | None = None,
    controls_readiness: dict[str, object] | None = None,
    backup_restore_readiness: dict[str, object] | None = None,
) -> dict[str, object]:
    """Read live persistence plan data and render the gap inventory without mutation."""

    try:
        persistence_plan = run_phase11_restart_autostart_persistence_fix_plan(
            config_path
        )
    except (
        Exception
    ) as exc:  # noqa: BLE001 - inventory must fail closed without traceback.
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
        readiness_report = run_phase11_controlled_artifact_reapply_readiness(
            config_path, packet_path_evidence_dir=packet_path_evidence_dir
        )
    except Exception as exc:  # noqa: BLE001 - readiness summary must fail closed.
        readiness_report = {
            "final_decision": "BLOCKED_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE",
            "live_ready_package_available": False,
            "blockers": ["readiness_summary_failed", str(exc)],
        }
    return build_phase11_operational_completion_gap_inventory_report(
        evidence_dir,
        config_path=config_path,
        persistence_plan_report=persistence_plan,
        readiness_report=readiness_report,
        lifecycle_execution_evidence_json=lifecycle_execution_evidence_json,
        firewall_completion_evidence_dir=firewall_completion_evidence_dir,
        onboarding_readiness=onboarding_readiness,
        usage_report_check_surface=usage_report_check_surface,
        abuse_runner_readiness=abuse_runner_readiness,
        controls_readiness=controls_readiness,
        backup_restore_readiness=backup_restore_readiness,
    )
