from __future__ import annotations

from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH
from mpf.services.phase11_operational_completion_progression import active_progression
from mpf.services import phase11_current_controlled_artifact_gate_service as gate_service
from mpf.services import phase11_restart_autostart_persistence_fix_service as fix_service
from mpf.services import phase11_controlled_artifact_reapply_package_service as package_service
from mpf.services import phase11_controlled_artifact_reapply_verification_service as verification_service

READY = "READY_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"
BLOCKED = "BLOCKED_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"
NO_REAPPLY = "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT"


def _as_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else ([] if value in (None, "") else [value])


def _blocked_report(expected_version: str, blockers: list[str], warnings: list[str] | None = None) -> dict[str, object]:
    progression = active_progression()
    return {
        "component": "phase11_controlled_artifact_reapply_readiness",
        "repository_version": __version__,
        "expected_version": expected_version,
        "current_phase_gate_ok": False,
        "known_controlled_artifacts_present": False,
        "unknown_mpf_artifacts": [],
        "forbidden_public_runtime_exposure": False,
        "production_gates_remain_closed": True,
        "controlled_artifact_reapply_required": None,
        "read_only_reapply_foundation_implemented": progression["read_only_reapply_foundation_implemented"],
        "controlled_filter_packet_path_evidence_ready": progression["controlled_filter_packet_path_evidence_ready"],
        "controlled_filter_packet_path_verified": progression["controlled_filter_packet_path_verified"],
        "artifact_graph_binding_ready": progression["artifact_graph_binding_ready"],
        "desired_artifact_semantics_complete": progression["desired_artifact_semantics_complete"],
        "controlled_artifact_reapply_package_evidence_ready": progression["controlled_artifact_reapply_package_evidence_ready"],
        "live_plan_collected": False,
        "package_generated": False,
        "package_verified_against_live_plan": False,
        "package_id": None,
        "package_sha256": None,
        "execution_precondition_fingerprint": None,
        "db_customer_policy_snapshot_hash": None,
        "desired_state_hash": None,
        "artifact_classification_hash": None,
        "payload_sha256": None,
        "backup_requirements_ready": False,
        "rollback_plan_ready": False,
        "lock_requirements_ready": False,
        "operator_confirmations_required": [],
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
        "blockers": sorted(set(blockers)),
        "warnings": warnings or [],
        "final_decision": BLOCKED,
        "next_required_step": "prepare_live_ready_controlled_artifact_reapply_package",
    }


def run_phase11_controlled_artifact_reapply_readiness(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    expected_version: str = __version__,
) -> dict[str, object]:
    progression = active_progression()
    blockers: list[str] = []
    warnings: list[str] = []
    try:
        fix_plan = fix_service.run_phase11_restart_autostart_persistence_fix_plan(config_path)
    except Exception as exc:  # noqa: BLE001
        fix_plan = {"final_decision": "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN", "safety_blockers": ["restart_autostart_persistence_fix_plan_failed", str(exc)]}
    try:
        live_plan = package_service.run_controlled_artifact_reapply_plan(config_path, expected_version=expected_version)
    except Exception as exc:  # noqa: BLE001
        live_plan = {"final_decision": "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE", "blockers": ["live_plan_collection_failed", str(exc)], "mutation_performed": False}
    try:
        backend_for_gate = live_plan.get("backend_target") if isinstance(live_plan.get("backend_target"), dict) else {}
        expected_backend_target = None
        if backend_for_gate.get("resolved_ipv4") and backend_for_gate.get("backend_port"):
            expected_backend_target = f"{backend_for_gate.get('resolved_ipv4')}:{backend_for_gate.get('backend_port')}"
        gate = gate_service.build_phase11_current_controlled_artifact_gate_report(
            iptables_save_text=str(live_plan.get("iptables_save_text", "")),
            ip6tables_save_text=str(live_plan.get("ip6tables_save_text", "")),
            phase_status_text=Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8") if Path("docs/PHASE_STATUS.md").exists() else "",
            expected_version=expected_version,
            expected_backend_target=expected_backend_target,
        )
    except Exception as exc:  # noqa: BLE001
        gate = {"blockers": ["current_controlled_artifact_gate_failed", str(exc)], "unknown_mpf_artifacts": [], "current_phase_gate_ok": False}
    package = package_service.build_controlled_artifact_reapply_package_report(plan=live_plan)
    verify = verification_service.build_controlled_artifact_reapply_verify_report(package=package, live_plan=live_plan, config_path=config_path, expected_version=expected_version)

    classification = live_plan.get("artifact_classification") if isinstance(live_plan.get("artifact_classification"), dict) else {}
    backend = live_plan.get("backend_target") if isinstance(live_plan.get("backend_target"), dict) else {}
    unknown = _as_list(classification.get("unknown_mpf") or gate.get("unknown_mpf_artifacts"))
    forbidden_public = bool(backend.get("backend_public_exposure") or gate.get("forbidden_public_runtime_exposure"))
    plan_decision = live_plan.get("final_decision")
    verification_ready = verify.get("final_decision") == "CONTROLLED_ARTIFACT_REAPPLY_VERIFY_READY"
    package_ready = package.get("final_decision") == "CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY"
    no_reapply = plan_decision == "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT" or classification.get("status") == "exact_present"

    blockers.extend(str(b) for b in _as_list(live_plan.get("blockers")))
    blockers.extend(str(b) for b in _as_list(package.get("blockers")))
    blockers.extend(str(b) for b in _as_list(verify.get("blockers")))
    blockers.extend(str(b) for b in _as_list(fix_plan.get("safety_blockers")))
    blockers.extend(str(b) for b in _as_list(gate.get("blockers")))
    if unknown:
        blockers.append("unknown_mpf_artifacts_present")
    if forbidden_public:
        blockers.append("forbidden_public_runtime_exposure")
    if not progression["production_execution_available"] is False:
        blockers.append("production_execution_gate_open_unexpectedly")
    production_gates_closed = progression["production_traffic"] == "controlled_cli_limited" and progression["customer_onboarding_allowed"] == "controlled_cli_limited" and progression["phase12_start_allowed"] == "no"
    if not production_gates_closed:
        blockers.append("production_or_later_phase_gate_open")
    if plan_decision not in {"CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY", "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT"}:
        blockers.append("live_plan_final_decision_blocked")

    final_decision = BLOCKED
    live_ready = False
    next_step = "prepare_live_ready_controlled_artifact_reapply_package"
    if no_reapply and not unknown and not forbidden_public and production_gates_closed and plan_decision == "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT":
        blockers = [b for b in blockers if b not in {"plan_not_ready", "package_not_ready", "package_payload_empty", "live_plan_not_safe", "live_plan_final_decision_blocked"}]
        if not blockers:
            final_decision = NO_REAPPLY
    elif package_ready and verification_ready and not blockers:
        final_decision = READY
        live_ready = True
        next_step = "sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5"

    return {
        "component": "phase11_controlled_artifact_reapply_readiness",
        "repository_version": __version__,
        "expected_version": expected_version,
        "current_phase_gate_ok": not _as_list(gate.get("blockers")),
        "known_controlled_artifacts_present": classification.get("status") == "exact_present",
        "unknown_mpf_artifacts": unknown,
        "forbidden_public_runtime_exposure": forbidden_public,
        "production_gates_remain_closed": production_gates_closed,
        "controlled_artifact_reapply_required": plan_decision == "CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY",
        "read_only_reapply_foundation_implemented": progression["read_only_reapply_foundation_implemented"],
        "controlled_filter_packet_path_evidence_ready": progression["controlled_filter_packet_path_evidence_ready"],
        "controlled_filter_packet_path_verified": progression["controlled_filter_packet_path_verified"],
        "artifact_graph_binding_ready": progression["artifact_graph_binding_ready"],
        "desired_artifact_semantics_complete": progression["desired_artifact_semantics_complete"],
        "controlled_artifact_reapply_package_evidence_ready": progression["controlled_artifact_reapply_package_evidence_ready"],
        "live_plan_collected": isinstance(live_plan, dict) and live_plan.get("component") == "phase11_controlled_artifact_reapply_plan",
        "package_generated": isinstance(package, dict) and package.get("component") == "phase11_controlled_artifact_reapply_package",
        "package_verified_against_live_plan": verification_ready,
        "package_id": package.get("package_id"),
        "package_sha256": package.get("package_sha256"),
        "execution_precondition_fingerprint": package.get("execution_precondition_fingerprint"),
        "db_customer_policy_snapshot_hash": package.get("db_customer_policy_snapshot_hash"),
        "desired_state_hash": package.get("desired_state_hash"),
        "artifact_classification_hash": package.get("artifact_classification_hash"),
        "payload_sha256": package.get("payload_sha256"),
        "backup_requirements_ready": bool((package.get("backup_requirements") or {}).get("required")) if isinstance(package.get("backup_requirements"), dict) else False,
        "rollback_plan_ready": isinstance(package.get("rollback_plan"), dict) and bool((package.get("rollback_plan") or {}).get("manual_review_required")),
        "lock_requirements_ready": bool((package.get("lock_requirements") or {}).get("exclusive_lock_required")) if isinstance(package.get("lock_requirements"), dict) else False,
        "operator_confirmations_required": package.get("operator_confirmations", []),
        "live_ready_package_available": live_ready,
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
        "blockers": sorted(set(blockers)) if final_decision == BLOCKED else [],
        "warnings": warnings,
        "final_decision": final_decision,
        "next_required_step": next_step,
    }
