"""Read-only Phase 11 post-cleanup restart/persistence evidence composer."""

from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH
from mpf.services import (
    phase11_controlled_artifact_persistence_plan_service as persistence,
    phase11_controlled_backend_target_service as backend_service,
    phase11_current_controlled_artifact_gate_service as artifact_gate,
    phase11_operational_completion_gap_inventory_service as gap_inventory,
    phase11_restart_autostart_persistence_diagnosis_service as diagnosis,
    phase11_restart_autostart_proof_service as proof,
)

_MUTATION_FLAGS = {
    "mutation_performed": False,
    "db_mutation_performed": False,
    "firewall_apply_performed": False,
    "conntrack_flush_performed": False,
    "docker_restart_performed": False,
    "systemd_restart_performed": False,
}


def build_fail_closed_report(*, expected_version: str = __version__, blockers: list[str] | None = None) -> dict[str, object]:
    b = sorted(set(blockers or ["post_cleanup_restart_persistence_evidence_failed_closed"]))
    return {
        "component": "phase11_post_cleanup_restart_persistence_evidence",
        "repository_version": __version__,
        "expected_version": expected_version,
        "backend_target": None,
        "current_controlled_artifact_gate": None,
        "duplicate_cleanup_state": {"final_decision": "UNKNOWN"},
        "controlled_artifact_persistence_state": {"final_decision": "BLOCKED"},
        "restart_autostart_readiness_state": {"restart_autostart_proof": "missing_or_partial"},
        "gap_inventory_summary": {"full_cli_production_operations": "missing_or_partial"},
        "phase11_operational_completion_accepted": False,
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "blockers": b,
        "warnings": [],
        **_MUTATION_FLAGS,
        "final_decision": "BLOCKED_POST_CLEANUP_RESTART_PERSISTENCE_EVIDENCE",
        "next_required_step": "resolve_post_cleanup_restart_persistence_evidence_blockers",
    }


def build_phase11_post_cleanup_restart_persistence_evidence_report(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    expected_version: str = __version__,
    evidence_dir: Path | str | None = None,
) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    backend = backend_service.build_controlled_backend_target_report(expected_version=expected_version)
    expected_backend_target = backend_service.expected_backend_target_from_report(backend)
    if expected_backend_target is None:
        blockers.append("expected_backend_target_required")

    try:
        current_gate = artifact_gate.build_phase11_current_controlled_artifact_gate_report(
            iptables_save_text=persistence._read_command_stdout(["iptables-save"]),
            ip6tables_save_text=persistence._read_command_stdout(["ip6tables-save"]),
            phase_status_text=persistence._phase_status_text(),
            expected_version=expected_version,
            expected_backend_target=expected_backend_target,
        )
    except Exception as exc:  # noqa: BLE001
        current_gate = {"final_decision": "BLOCKED_CURRENT_CONTROLLED_ARTIFACT_GATE", "blockers": [str(exc)], "unknown_mpf_artifacts": []}
        blockers.append("current_controlled_artifact_gate_failed_closed")

    try:
        persistence_state = persistence.run_phase11_controlled_artifact_persistence_plan(config_path, expected_version=expected_version)
    except Exception as exc:  # noqa: BLE001
        persistence_state = {"final_decision": "BLOCKED_CONTROLLED_ARTIFACT_PERSISTENCE_PLAN", "blockers": [str(exc)]}
        blockers.append("controlled_artifact_persistence_plan_failed_closed")
    try:
        restart_state = diagnosis.run_phase11_restart_autostart_persistence_diagnosis(config_path, expected_version=expected_version)
    except Exception as exc:  # noqa: BLE001
        restart_state = {"final_decision": "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_GAP", "blockers": [str(exc)]}
        blockers.append("restart_autostart_readiness_failed_closed")
    proof_state = proof.build_phase11_restart_autostart_proof_report(evidence_dir)
    try:
        gap = gap_inventory.run_phase11_operational_completion_gap_inventory_report(config_path, evidence_dir=evidence_dir)
    except Exception as exc:  # noqa: BLE001
        gap = {"final_decision": "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED", "blockers": [str(exc)], "full_cli_production_operations": "missing_or_partial"}
        blockers.append("gap_inventory_failed_closed")

    for component in (current_gate, persistence_state, restart_state):
        for blocker in component.get("blockers", []) if isinstance(component, dict) else []:
            if blocker in {"expected_backend_target_required", "dnat_target_unresolved", "unknown_mpf_artifacts_detected"}:
                blockers.append(str(blocker))
    if current_gate.get("unknown_mpf_artifacts") not in ([], None):
        blockers.append("unknown_mpf_artifacts_detected")

    summary = {
        "component": "phase11_post_cleanup_restart_persistence_evidence",
        "repository_version": __version__,
        "expected_version": expected_version,
        "backend_target": {"expected_backend_target": expected_backend_target, "resolution": backend},
        "current_controlled_artifact_gate": current_gate,
        "duplicate_cleanup_state": {
            "duplicate_nat_redirect_count": current_gate.get("duplicate_nat_redirect_count"),
            "duplicate_controlled_artifact_count": current_gate.get("duplicate_controlled_artifact_count"),
            "unknown_mpf_artifacts": current_gate.get("unknown_mpf_artifacts", []),
            "forbidden_public_runtime_exposure": current_gate.get("forbidden_public_runtime_exposure"),
            "production_gates_remain_closed": current_gate.get("production_gates_remain_closed"),
        },
        "controlled_artifact_persistence_state": persistence_state,
        "restart_autostart_readiness_state": {"diagnosis": restart_state, "proof": proof_state, "restart_autostart_proof": proof_state.get("restart_autostart_proof", "missing_or_partial")},
        "gap_inventory_summary": gap,
        "phase11_operational_completion_accepted": False,
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        **_MUTATION_FLAGS,
        "final_decision": "POST_CLEANUP_RESTART_PERSISTENCE_EVIDENCE_READY" if not blockers else "BLOCKED_POST_CLEANUP_RESTART_PERSISTENCE_EVIDENCE",
        "next_required_step": "collect_real_restart_autostart_evidence_after_operator_restart_or_reboot" if not blockers else "resolve_post_cleanup_restart_persistence_evidence_blockers",
    }
    return summary
