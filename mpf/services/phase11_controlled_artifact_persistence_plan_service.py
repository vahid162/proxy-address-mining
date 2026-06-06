"""Read-only Phase 11 controlled firewall artifact persistence planning."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
import subprocess

from mpf import __version__
from mpf.adapters import socket_inspector
from mpf.config import DEFAULT_CONFIG_PATH, MPFConfig, load_config
from mpf.repositories import customer_repo
from mpf.services import (
    phase11_single_customer_firewall_apply_gate_service,
    phase11e_limited_activation_execution_package_service,
    phase11_controlled_artifact_reapply_package_service,
    phase11_controlled_artifact_reapply_executor_service,
    phase11_controlled_backend_target_service,
)
from mpf.services.phase11_current_controlled_artifact_gate_service import (
    build_phase11_current_controlled_artifact_gate_report,
)

_COMPONENT = "phase11_controlled_artifact_persistence_plan"
_REQUIRED_CUSTOMERS = {
    "canary-btc-001": {"lane": "btc", "port": 20001},
    "limited-btc-001": {"lane": "btc", "port": 20101},
}
_MUTATION_FLAGS: dict[str, bool] = {
    "mutation_performed": False,
    "db_mutation_performed": False,
    "firewall_apply_performed": False,
    "conntrack_flush_performed": False,
    "docker_restart_performed": False,
    "systemd_restart_performed": False,
}


def _read_command_stdout(command: list[str]) -> str:
    try:
        result = subprocess.run(command, text=True, capture_output=True)
    except FileNotFoundError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout


def _phase_status_text() -> str:
    try:
        return Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def _phase_gate_aligned(text: str) -> bool:
    required = (
        "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5",
        "current_working_phase: Phase 11 operational completion — Full CLI Production Operations",
        "production_traffic: controlled_cli_limited",
        "customer_onboarding_allowed: controlled_cli_limited",
        "phase12_start_allowed: no",
        "worker_enforcement_allowed: no",
        "ui_allowed: no",
        "telegram_allowed: no",
    )
    return all(item in text for item in required)


def _backend_listener_state(sockets: Iterable[socket_inspector.ListeningSocket]) -> dict[str, object]:
    matches = [item for item in sockets if item.port == 60010]
    public = any(socket_inspector.is_public_bind_address(item.local_address) for item in matches)
    local_only = bool(matches) and all(socket_inspector.is_local_bind_address(item.local_address) for item in matches)
    return {
        "port": 60010,
        "present": bool(matches),
        "local_only": local_only,
        "public_bind_detected": public,
        "listeners": [asdict(item) for item in matches],
    }


def _customer_visibility_from_records(records: Iterable[object]) -> dict[str, object]:
    visible: dict[str, object] = {}
    for key, expected in _REQUIRED_CUSTOMERS.items():
        match = None
        for record in records:
            if getattr(record, "customer_key", None) == key:
                match = record
                break
        visible[key] = {
            "visible": match is not None,
            "expected_lane": expected["lane"],
            "expected_port": expected["port"],
            "actual_lane": getattr(match, "lane", None) if match else None,
            "actual_port": getattr(match, "port", None) if match else None,
            "status": getattr(match, "status", None) if match else None,
            "matches_expected": bool(
                match
                and getattr(match, "lane", None) == expected["lane"]
                and getattr(match, "port", None) == expected["port"]
                and getattr(match, "status", None) != "deleted"
            ),
        }
    return visible


def _load_customer_records(config: MPFConfig) -> tuple[bool, list[object], str]:
    ok, records, message = customer_repo.list_customers(config, include_deleted=False, limit=1000)
    return ok, list(records), message


def _candidate_reapply_path_summary() -> dict[str, object]:
    single_customer_plan_callable = callable(
        getattr(phase11_single_customer_firewall_apply_gate_service, "build_phase11_single_customer_firewall_apply_gate_report", None)
    )
    limited_activation_package_callable = callable(
        getattr(phase11e_limited_activation_execution_package_service, "build_phase11e_limited_activation_execution_package_report", None)
    )
    package_callable = callable(getattr(phase11_controlled_artifact_reapply_package_service, "build_controlled_artifact_reapply_package_report", None))
    execute_callable = callable(getattr(phase11_controlled_artifact_reapply_executor_service, "execute_controlled_artifact_reapply_package", None))
    return {
        "candidate_reapply_services_declared": single_customer_plan_callable and limited_activation_package_callable and package_callable and execute_callable,
        "candidate_reapply_services": {
            "phase11_single_customer_firewall_apply_gate_service.build_phase11_single_customer_firewall_apply_gate_report": single_customer_plan_callable,
            "phase11e_limited_activation_execution_package_service.build_phase11e_limited_activation_execution_package_report": limited_activation_package_callable,
            "phase11_controlled_artifact_reapply_package_service.build_controlled_artifact_reapply_package_report": package_callable,
            "phase11_controlled_artifact_reapply_executor_service.execute_controlled_artifact_reapply_package": execute_callable,
        },
        "raw_iptables_reapply_implemented_here": False,
        "controlled_artifact_reapply_capability_implemented": package_callable and execute_callable,
        "safe_reuse_identified_for_execution_in_this_pr": False,
        "execution_package_available": False,
        "live_package_ready": False,
        "package_evidence_collected": False,
        "package_reviewed": False,
        "execution_verified": False,
        "execution_decision": "CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_BLOCKED_UNTIL_REAL_ADAPTERS_AND_FARM5_READY_PACKAGE",
        "reason": "Controlled read-only reapply surfaces are implemented, but production execute remains blocked until source-backed farm5 READY package evidence and real live-preflight/lock/backup/audit/rollback/verification adapters exist.",
    }


def build_phase11_controlled_artifact_persistence_plan_report(
    *,
    current_controlled_artifact_gate_result: dict[str, object] | None = None,
    listening_sockets: Iterable[socket_inspector.ListeningSocket] | None = None,
    customer_records: Iterable[object] | None = None,
    customer_read_ok: bool = True,
    customer_read_message: str = "OK",
    phase_status_text: str | None = None,
    candidate_reapply_restore_path_reuse: dict[str, object] | None = None,
    expected_version: str = __version__,
) -> dict[str, object]:
    """Build the fail-closed read-only artifact persistence plan."""

    phase_text = phase_status_text if phase_status_text is not None else _phase_status_text()
    gate = current_controlled_artifact_gate_result or build_phase11_current_controlled_artifact_gate_report(
        iptables_save_text="",
        ip6tables_save_text="",
        phase_status_text=phase_text,
        expected_version=expected_version,
    )
    backend = _backend_listener_state(listening_sockets or [])
    customers = _customer_visibility_from_records(customer_records or [])
    candidate_path = candidate_reapply_restore_path_reuse or _candidate_reapply_path_summary()

    unknown = gate.get("unknown_mpf_artifacts") if isinstance(gate.get("unknown_mpf_artifacts"), list) else []
    known_present = gate.get("known_controlled_artifacts_present") is True
    known_classified = gate.get("final_decision") in {
        "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS",
        "PASS_NO_CUSTOMER_ARTIFACTS",
    }
    controlled_absent_after_reboot = known_classified and not known_present

    blockers: list[str] = []
    if expected_version != __version__:
        blockers.append("wrong_expected_version")
    if not _phase_gate_aligned(phase_text):
        blockers.append("phase_gate_mismatch")
    if unknown != []:
        blockers.append("unknown_mpf_artifacts_detected")
    if backend["public_bind_detected"]:
        blockers.append("backend_public_exposure_detected")
    if not backend["local_only"]:
        blockers.append("backend_listener_not_local_only_or_absent")
    if not customer_read_ok:
        blockers.append("controlled_customer_records_unreadable")
    missing_or_mismatched = [key for key, value in customers.items() if not isinstance(value, dict) or not value.get("matches_expected")]
    blockers.extend(f"required_controlled_customer_missing_or_mismatched:{key}" for key in missing_or_mismatched)
    if not known_classified:
        blockers.append("known_controlled_artifact_state_unclassified")
    if not candidate_path.get("candidate_reapply_services_declared", False):
        blockers.append("candidate_reapply_or_restore_services_not_identified")

    ready = not blockers
    next_step = "implement_controlled_artifact_reapply_execute_package"
    if not ready:
        next_step = "fix_restart_autostart_persistence_gap"
    warnings = ["controlled_artifacts_absent_after_reboot"] if controlled_absent_after_reboot else []
    if candidate_path.get("execution_package_available") is not True:
        warnings.append("controlled_artifact_reapply_execution_package_not_available")
    else:
        warnings.append("farm5_controlled_artifact_reapply_package_evidence_required")

    return {
        "component": _COMPONENT,
        "repository_version": __version__,
        "expected_version": expected_version,
        "phase11_operational_completion_scope": "full_cli_production_operations",
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "current_controlled_artifact_gate_result": gate,
        "known_controlled_artifacts_present": known_present,
        "known_controlled_artifact_state_classified": known_classified,
        "unknown_mpf_artifacts": unknown,
        "controlled_artifacts_absent_after_reboot": controlled_absent_after_reboot,
        "backend_listener_127_0_0_1_60010_present": backend["present"] and backend["local_only"],
        "backend_public_exposure_detected": backend["public_bind_detected"],
        "backend_listener_state": backend,
        "controlled_customer_records_visible": customers,
        "customer_read_ok": customer_read_ok,
        "customer_read_message": customer_read_message,
        "candidate_reapply_restore_path_reuse": candidate_path,
        "safe_reuse_identified_for_execution_in_this_pr": candidate_path.get("safe_reuse_identified_for_execution_in_this_pr", False),
        "controlled_artifact_reapply_capability_implemented": candidate_path.get("controlled_artifact_reapply_capability_implemented", False),
        "execution_package_available": candidate_path.get("execution_package_available", False),
        "artifact_reapply_execution_decision": candidate_path.get("execution_decision", "CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_NOT_AVAILABLE"),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        **_MUTATION_FLAGS,
        "final_decision": "CONTROLLED_ARTIFACT_PERSISTENCE_PLAN_READY" if ready else "BLOCKED_CONTROLLED_ARTIFACT_PERSISTENCE_PLAN",
        "controlled_artifact_reapply_required": controlled_absent_after_reboot,
        "controlled_artifact_reapply_execution_available": False,
        "controlled_artifact_reapply_package_evidence_ready": False,
        "next_required_step": "sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5" if ready and candidate_path.get("controlled_artifact_reapply_capability_implemented", False) else next_step,
    }


def run_phase11_controlled_artifact_persistence_plan(config_path: Path = DEFAULT_CONFIG_PATH, *, expected_version: str = __version__) -> dict[str, object]:
    """Inspect read-only firewall/socket/customer state and return the plan."""

    cfg = load_config(config_path)
    ok, records, message = _load_customer_records(cfg)
    backend_target = phase11_controlled_backend_target_service.build_controlled_backend_target_report(expected_version=expected_version)
    expected_backend_target = None
    if backend_target.get("status") == "ok" and backend_target.get("resolved_ipv4") and backend_target.get("target_port"):
        expected_backend_target = f"{backend_target['resolved_ipv4']}:{backend_target['target_port']}"
    gate = build_phase11_current_controlled_artifact_gate_report(
        iptables_save_text=_read_command_stdout(["iptables-save"]),
        ip6tables_save_text=_read_command_stdout(["ip6tables-save"]),
        phase_status_text=_phase_status_text(),
        expected_version=expected_version,
        expected_backend_target=expected_backend_target,
    )
    gate["backend_target_resolution"] = backend_target
    return build_phase11_controlled_artifact_persistence_plan_report(
        current_controlled_artifact_gate_result=gate,
        listening_sockets=socket_inspector.list_listening_tcp_sockets(),
        customer_records=records,
        customer_read_ok=ok,
        customer_read_message=message,
        expected_version=expected_version,
    )
