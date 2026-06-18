"""Read-only, fail-closed Phase 11 full CLI production operations gap inventory."""

from __future__ import annotations

import json
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
    NO_REAPPLY as READINESS_NO_REAPPLY,
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
    READY as ONBOARDING_READY,
    run_phase11_production_onboarding_flow_readiness_report,
)
from mpf.services.phase11_production_abuse_runner_readiness_service import (
    READY as ABUSE_RUNNER_READY,
)
from mpf.services.phase11_evidence_contract_readiness_service import (
    build_contract_readiness_report,
)
from mpf.services.phase11_production_controls_pause_block_expire_readiness_service import (
    run_phase11_production_controls_pause_block_expire_readiness_report,
)
from mpf.services.phase11_backup_restore_drill_readiness_service import (
    READY as BACKUP_RESTORE_READY,
    build_phase11_backup_restore_drill_readiness_report,
)
from mpf.services.phase11_generic_real_customer_activation_service import (
    READY as GENERIC_ACTIVATION_READY,
    readiness_from_evidence as generic_activation_readiness_from_evidence,
)

_MISSING_OR_PARTIAL = "missing_or_partial"

_FIREWALL_SAFE_FINAL_DECISIONS = {
    "PRODUCTION_FIREWALL_ALREADY_APPLIED_VERIFIED_NO_REAPPLY_REQUIRED",
    "PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE_READY",
}
_MUTATION_KEYS = (
    "mutation_performed",
    "db_mutation_performed",
    "firewall_apply_performed",
    "conntrack_flush_performed",
    "docker_restart_performed",
    "systemd_restart_performed",
)


def _resolve_restart_autostart_evidence_dir(evidence_dir: Path | str | None, explicit: Path | str | None = None) -> tuple[Path | None, str]:
    if explicit is not None:
        return Path(explicit), "direct_legacy"
    if evidence_dir is None:
        return None, "missing"
    base = Path(evidence_dir)
    nested = base / "restart-autostart-proof"
    if nested.is_dir():
        return nested, "nested_collector"
    if base.exists():
        return base, "direct_legacy"
    return None, "missing"


def _firewall_fail_closed(blocker: str, detail: str | None = None) -> dict[str, object]:
    blockers = [blocker] if detail is None else [blocker, detail]
    return {
        "component": "phase11_production_firewall_apply_verify_rollback_readiness",
        "repository_version": __version__,
        "production_firewall_apply_verify_rollback": _MISSING_OR_PARTIAL,
        "phase12_start_allowed": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "blockers": blockers,
        "final_decision": "BLOCKED_PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE",
        "next_required_step": "production_firewall_apply_verify_rollback",
    }


def _validated_firewall_readiness_json(report: dict[str, object]) -> dict[str, object]:
    if report.get("production_firewall_apply_verify_rollback") != FIREWALL_READY:
        return _firewall_fail_closed("firewall_completion_readiness_json_invalid")
    if report.get("final_decision") not in _FIREWALL_SAFE_FINAL_DECISIONS:
        return _firewall_fail_closed("firewall_completion_readiness_json_invalid")
    if report.get("blockers") not in ([], None):
        return _firewall_fail_closed("firewall_completion_readiness_json_invalid")
    if report.get("phase12_start_allowed") is not False:
        return _firewall_fail_closed("firewall_completion_readiness_json_unsafe")
    if any(report.get(key) is True for key in _MUTATION_KEYS):
        return _firewall_fail_closed("firewall_completion_readiness_json_unsafe")
    safe = dict(report)
    for key in _MUTATION_KEYS:
        safe.setdefault(key, False)
    safe.setdefault("phase12_start_allowed", False)
    safe.setdefault("blockers", [])
    return safe


def _load_firewall_completion_readiness(evidence_dir: Path | str | None) -> dict[str, object] | None:
    if evidence_dir is None:
        return None
    path = Path(evidence_dir) / "production-firewall-apply-verify-rollback-readiness.json"
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - fail closed for malformed collector evidence.
        return _firewall_fail_closed("firewall_completion_readiness_json_invalid", str(exc))
    if not isinstance(loaded, dict):
        return _firewall_fail_closed("firewall_completion_readiness_json_invalid")
    return _validated_firewall_readiness_json(loaded)


def _load_evidence_json(evidence_dir: Path | str | None, filename: str) -> dict[str, object] | None:
    """Load an explicit collector evidence JSON file, or return None if absent.

    Remaining operational readiness must be evidence-driven. This helper keeps the
    service fail-closed for unit tests and ad-hoc calls that do not pass an
    evidence directory, while allowing the official collector bundle to advance
    from concrete JSON artifacts it already wrote.
    """

    if not evidence_dir:
        return None
    path = Path(evidence_dir) / filename
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - gap inventory must not traceback.
        return {
            "final_decision": f"BLOCKED_{filename.upper().replace('-', '_').replace('.', '_')}",
            "blockers": ["evidence_json_load_failed", str(exc)],
            "mutation_performed": False,
        }
    return data if isinstance(data, dict) else {"blockers": ["evidence_json_root_not_object"], "mutation_performed": False}


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
    if (
        readiness_report
        and readiness_report.get("final_decision") == READINESS_NO_REAPPLY
        and not readiness_report.get("blockers")
    ):
        return "production_firewall_apply_verify_rollback"
    if readiness_report and "controlled_artifact_reapply_readiness_snapshot_required" in readiness_report.get("blockers", []):
        return "controlled_artifact_reapply_readiness_snapshot_required"
    return str(active_progression()["next_required_step"])


def build_phase11_operational_completion_gap_inventory_report(
    evidence_dir: Path | str | None = None,
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    persistence_plan_report: dict[str, object] | None = None,
    readiness_report: dict[str, object] | None = None,
    lifecycle_execution_evidence_json: Path | str | None = None,
    firewall_completion_evidence_dir: Path | str | None = None,
    restart_autostart_evidence_dir: Path | str | None = None,
    firewall_completion_readiness: dict[str, object] | None = None,
    expected_version: str = __version__,
    expected_backend_target: str | None = None,
    iptables_save_file: Path | str | None = None,
    ip6tables_save_file: Path | str | None = None,
    onboarding_readiness: dict[str, object] | None = None,
    usage_report_check_surface: dict[str, object] | None = None,
    abuse_runner_readiness: dict[str, object] | None = None,
    controls_readiness: dict[str, object] | None = None,
    backup_restore_readiness: dict[str, object] | None = None,
    generic_activation_readiness: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return the expanded post-acceptance Phase 11 gap inventory without mutation."""

    if readiness_report is None:
        readiness_report = _load_evidence_json(
            evidence_dir, "controlled-artifact-reapply-readiness-target-aware.json"
        ) or _load_evidence_json(evidence_dir, "controlled-artifact-reapply-readiness.json")
    if readiness_report is None:
        readiness_report = {
            "component": "phase11_controlled_artifact_reapply_readiness",
            "repository_version": __version__,
            "final_decision": "BLOCKED_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE",
            "live_ready_package_available": False,
            "production_execution_available": False,
            "controlled_artifact_execute_available": False,
            "iptables_restore_invocation_allowed": False,
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
            "blockers": ["controlled_artifact_reapply_readiness_snapshot_required"],
            "next_required_step": "controlled_artifact_reapply_readiness_snapshot_required",
        }

    resolved_restart_dir, restart_layout = _resolve_restart_autostart_evidence_dir(evidence_dir, restart_autostart_evidence_dir)
    restart_report = (
        build_phase11_restart_autostart_proof_report(resolved_restart_dir)
        if resolved_restart_dir is not None
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
                evidence_dir=resolved_restart_dir,
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
    if firewall_completion_readiness is not None:
        firewall_completion = _validated_firewall_readiness_json(firewall_completion_readiness)
    else:
        firewall_completion = _load_firewall_completion_readiness(evidence_dir)
    if firewall_completion is None and firewall_completion_evidence_dir:
        firewall_completion = build_production_firewall_apply_verify_rollback_readiness_report(
            firewall_completion_evidence_dir
        )
    firewall_item = (
        FIREWALL_READY
        if firewall_completion
        and firewall_completion.get("production_firewall_apply_verify_rollback")
        == FIREWALL_READY
        else _MISSING_OR_PARTIAL
    )
    if onboarding_readiness is None:
        loaded_onboarding = _load_evidence_json(
            evidence_dir, "production-onboarding-flow-readiness.json"
        )
        if loaded_onboarding and loaded_onboarding.get("production_onboarding_flow") == ONBOARDING_READY:
            onboarding_readiness = loaded_onboarding
        else:
            try:
                onboarding_readiness = run_phase11_production_onboarding_flow_readiness_report(
                    config_path,
                    lifecycle_readiness=lifecycle_readiness,
                    firewall_readiness=firewall_completion,
                )
            except Exception as exc:  # noqa: BLE001 - gap inventory must fail closed.
                onboarding_readiness = loaded_onboarding or {
                    "production_onboarding_flow": _MISSING_OR_PARTIAL,
                    "blockers": ["onboarding_readiness_context_evaluation_failed", str(exc)],
                    "mutation_performed": False,
                    "phase12_start_allowed": False,
                }
    onboarding_item = (
        ONBOARDING_READY
        if (onboarding_readiness or {}).get("production_onboarding_flow")
        == ONBOARDING_READY
        else _MISSING_OR_PARTIAL
    )
    if usage_report_check_surface is None:
        usage_report_check_surface = _load_evidence_json(
            evidence_dir, "usage-report-check-operational-surface.json"
        )
    usage_item = (
        "production_usage_report_check_evidence_ready"
        if (usage_report_check_surface or {}).get("usage_report_check_surface_ready") is True
        and (usage_report_check_surface or {}).get("final_decision")
        == "USAGE_REPORT_CHECK_SURFACE_READY"
        and not (usage_report_check_surface or {}).get("blockers")
        else _MISSING_OR_PARTIAL
    )
    if abuse_runner_readiness is None:
        abuse_runner_readiness = _load_evidence_json(
            evidence_dir, "production-abuse-runner-readiness.json"
        )
    abuse_item = (
        ABUSE_RUNNER_READY
        if (abuse_runner_readiness or {}).get("production_abuse_runner")
        == ABUSE_RUNNER_READY
        else _MISSING_OR_PARTIAL
    )
    if controls_readiness is None:
        explicit_controls = _load_evidence_json(
            evidence_dir, "production-controls-pause-block-expire-readiness.json"
        )
        controls_readiness = explicit_controls
        if controls_readiness is None:
            controls_readiness = build_contract_readiness_report(
                "production_controls_pause_block_expire", evidence_dir
            )
            controls_readiness.setdefault("production_controls_pause_block_expire", _MISSING_OR_PARTIAL)
            controls_readiness.setdefault("production_controls_pause_block_expire_ready", False)
            controls_readiness.setdefault("readiness_scope", "explicit_evidence_required")
            controls_readiness.setdefault("blockers", [])
            if "production_controls_pause_block_expire_evidence_missing" not in controls_readiness["blockers"]:
                controls_readiness["blockers"].append("production_controls_pause_block_expire_evidence_missing")
        else:
            if (
                controls_readiness.get("production_controls_pause_block_expire")
                == "production_controls_pause_block_expire_ready"
                and controls_readiness.get("production_controls_pause_block_expire_ready") is True
                and not controls_readiness.get("blockers")
            ):
                controls_readiness["contract_readiness"] = {
                    "component": "phase11_production_controls_pause_block_expire_readiness_contract",
                    "repository_version": __version__,
                    "production_controls_pause_block_expire": "production_controls_pause_block_expire_ready",
                    "production_controls_pause_block_expire_ready": True,
                    "expected_evidence_file": "production-controls-pause-block-expire-readiness.json",
                    "blockers": [],
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
                    "final_decision": "PRODUCTION_CONTROLS_PAUSE_BLOCK_EXPIRE_READY",
                }
            else:
                contract = build_contract_readiness_report("production_controls_pause_block_expire", evidence_dir)
                controls_readiness["contract_readiness"] = contract
    if backup_restore_readiness is None:
        explicit_backup_restore = _load_evidence_json(
            evidence_dir, "backup-restore-drill-readiness.json"
        )
        if explicit_backup_restore is not None:
            backup_restore_readiness = explicit_backup_restore
        else:
            backup_restore_readiness = build_phase11_backup_restore_drill_readiness_report(evidence_dir)
    if generic_activation_readiness is None:
        generic_activation_readiness = generic_activation_readiness_from_evidence(
            _load_evidence_json(evidence_dir, "production-generic-real-customer-activation-readiness.json")
            or _load_evidence_json(evidence_dir, "generic-real-customer-activation-runtime-evidence.json")
        )
    controls_item = controls_readiness.get(
        "production_controls_pause_block_expire", _MISSING_OR_PARTIAL
    )
    backup_item = backup_restore_readiness.get(
        "backup_restore_drill", _MISSING_OR_PARTIAL
    )
    generic_activation_item = (
        GENERIC_ACTIVATION_READY
        if (generic_activation_readiness or {}).get("production_generic_real_customer_activation") == GENERIC_ACTIVATION_READY
        else _MISSING_OR_PARTIAL
    )
    order = [
        ("production_onboarding_flow", onboarding_item),
        ("production_usage_report_check_evidence", usage_item),
        ("production_abuse_runner", abuse_item),
        ("production_controls_pause_block_expire", controls_item),
        ("backup_restore_drill", backup_item),
        ("production_generic_real_customer_activation", generic_activation_item),
    ]
    next_required_step = _next_step(
        restart_status, persistence_plan_report, readiness_report, lifecycle_readiness
    )
    progression_prerequisites_ready = (
        restart_status == "ready"
        and lifecycle_item == "controlled_execution_evidence_ready"
        and firewall_item == FIREWALL_READY
    )
    full_acceptance_prerequisites_ready = (
        restart_status == "ready"
        and lifecycle_item == "controlled_execution_evidence_ready"
        and firewall_item == FIREWALL_READY
    )
    if progression_prerequisites_ready:
        next_required_step = "final_phase11_operational_completion_acceptance"
        for name, status in order:
            if status == _MISSING_OR_PARTIAL:
                next_required_step = name
                break
    all_surfaces_ready = full_acceptance_prerequisites_ready and all(
        status != _MISSING_OR_PARTIAL for _, status in order
    )
    # This readiness package may advance backup_restore_drill only. Final Full CLI
    # Production Operations acceptance is a later explicit acceptance PR.
    full_ready = False

    return {
        "component": "phase11_operational_completion_gap_inventory",
        "repository_version": __version__,
        "phase11_accepted": True,
        "phase11_operational_completion_required": True,
        "phase11_operational_completion_scope": "full_cli_production_operations",
        "phase12_start_allowed": False,
        "restart_autostart_proof": restart_status,
        "restart_autostart_evidence_dir": str(resolved_restart_dir) if resolved_restart_dir else None,
        "restart_autostart_evidence_layout": restart_layout if restart_report else "missing",
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
        "production_generic_real_customer_activation": generic_activation_item,
        "production_generic_real_customer_activation_readiness": generic_activation_readiness,
        "full_cli_production_operations": (
            "full_cli_production_operations_ready"
            if full_ready
            else _MISSING_OR_PARTIAL
        ),
        "full_cli_production_operations_acceptance_pr_required": all_surfaces_ready,
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
    restart_autostart_evidence_dir: Path | str | None = None,
    firewall_completion_readiness: dict[str, object] | None = None,
    expected_version: str = __version__,
    expected_backend_target: str | None = None,
    iptables_save_file: Path | str | None = None,
    ip6tables_save_file: Path | str | None = None,
    onboarding_readiness: dict[str, object] | None = None,
    usage_report_check_surface: dict[str, object] | None = None,
    abuse_runner_readiness: dict[str, object] | None = None,
    controls_readiness: dict[str, object] | None = None,
    backup_restore_readiness: dict[str, object] | None = None,
    generic_activation_readiness: dict[str, object] | None = None,
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
    readiness_report = None
    if packet_path_evidence_dir is not None or (iptables_save_file is not None and ip6tables_save_file is not None):
        try:
            readiness_report = run_phase11_controlled_artifact_reapply_readiness(
                config_path,
                expected_version=expected_version,
                packet_path_evidence_dir=packet_path_evidence_dir,
                expected_backend_target=expected_backend_target,
                iptables_save_file=iptables_save_file,
                ip6tables_save_file=ip6tables_save_file,
            )
        except Exception as exc:  # noqa: BLE001 - readiness summary must fail closed.
            readiness_report = {
                "final_decision": "BLOCKED_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE",
                "live_ready_package_available": False,
                "production_execution_available": False,
                "controlled_artifact_execute_available": False,
                "iptables_restore_invocation_allowed": False,
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
                "blockers": ["readiness_summary_failed", str(exc)],
            }
    return build_phase11_operational_completion_gap_inventory_report(
        evidence_dir,
        config_path=config_path,
        persistence_plan_report=persistence_plan,
        readiness_report=readiness_report,
        lifecycle_execution_evidence_json=lifecycle_execution_evidence_json,
        firewall_completion_evidence_dir=firewall_completion_evidence_dir,
        restart_autostart_evidence_dir=restart_autostart_evidence_dir,
        firewall_completion_readiness=firewall_completion_readiness,
        onboarding_readiness=onboarding_readiness,
        usage_report_check_surface=usage_report_check_surface,
        abuse_runner_readiness=abuse_runner_readiness,
        controls_readiness=controls_readiness,
        backup_restore_readiness=backup_restore_readiness,
        generic_activation_readiness=generic_activation_readiness,
    )
