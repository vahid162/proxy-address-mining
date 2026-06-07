"""Read-only Phase 11 restart/autostart persistence fix planning.

This module intentionally does not execute Docker Compose, systemd, DB, firewall,
iptables-restore, or conntrack operations.  It only builds an operator-reviewed
plan/package for the accepted controlled Phase 11 runtime boundary.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
import subprocess
from typing import Any

import yaml

from mpf import __version__
from mpf.adapters import docker_compose, socket_inspector
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.services.phase11_restart_autostart_persistence_diagnosis_service import (
    build_phase11_restart_autostart_persistence_diagnosis_report,
)
from mpf.services.proxy_doctor_service import EXPECTED_RUNTIME_CONTAINERS

_COMPONENT = "phase11_restart_autostart_persistence_fix"
_SCOPE = "full_cli_production_operations"
_PROJECT_NAME = "mpf-proxy"
_COMPOSE_FILE = "compose/mpf-proxy.compose.yaml"
_PROFILE = "phase4-runtime"
_EXECUTE_COMMAND = (
    "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml "
    "--profile phase4-runtime up -d --no-build --pull never"
)
_PRE_CHECK_COMMANDS = [
    "mpf --version",
    "mpf phase-status",
    "mpf config validate",
    "mpf proxy status",
    "mpf proxy doctor",
    "mpf production restart-autostart-persistence-diagnosis --output json",
]
_POST_CHECK_COMMANDS = [
    "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime ps -a",
    "mpf proxy status",
    "mpf proxy doctor",
    "mpf production restart-autostart-persistence-diagnosis --output json",
    "mpf production restart-autostart-proof --output json",
    "mpf production phase11-operational-completion-gap-inventory --output json",
]
_FORBIDDEN_OPERATIONS = [
    "reboot",
    "shutdown",
    "systemctl enable",
    "systemctl start",
    "systemctl restart",
    "iptables-restore",
    "arbitrary iptables commands",
    "conntrack flush",
    "DB writes",
    "customer lifecycle execution",
    "unrestricted firewall apply",
    "Phase 12 commands",
    "worker enforcement",
    "UI",
    "Telegram",
    "public API exposure",
]
_MUTATION_FLAGS: dict[str, bool] = {
    "mutation_performed": False,
    "db_mutation_performed": False,
    "firewall_apply_performed": False,
    "conntrack_flush_performed": False,
    "docker_restart_performed": False,
    "systemd_restart_performed": False,
}


def _container_running(container: docker_compose.DockerContainerSummary) -> bool:
    return container.status.lower().startswith("up")


def _container_healthy(container: docker_compose.DockerContainerSummary) -> bool:
    status = container.status.lower()
    if not _container_running(container):
        return False
    if "unhealthy" in status or "health: starting" in status:
        return False
    return "healthy" in status or "health" not in status


def _container_report(containers: Iterable[docker_compose.DockerContainerSummary]) -> list[dict[str, object]]:
    return [
        {
            **asdict(container),
            "running": _container_running(container),
            "healthy": _container_healthy(container),
        }
        for container in sorted(containers, key=lambda item: item.name)
    ]


def _local_only_listener_state(sockets: Iterable[socket_inspector.ListeningSocket]) -> dict[str, object]:
    socket_list = list(sockets)
    expected_ports = {"v2raya_ui": 2015, "btc_backend": 60010}
    checks: dict[str, object] = {}
    blockers: list[str] = []
    for name, port in expected_ports.items():
        matches = [item for item in socket_list if item.port == port]
        public = any(socket_inspector.is_public_bind_address(item.local_address) for item in matches)
        local_only = bool(matches) and all(socket_inspector.is_local_bind_address(item.local_address) for item in matches)
        if not matches:
            blockers.append(f"missing_listener:{name}:{port}")
        elif public or not local_only:
            blockers.append(f"non_local_listener:{name}:{port}")
        checks[name] = {
            "port": port,
            "present": bool(matches),
            "local_only": local_only,
            "public_bind_detected": public,
            "listeners": [asdict(item) for item in matches],
        }
    return {"checks": checks, "blockers": blockers}


def _compose_service(compose_file: Path, service_name: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(compose_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    services = data.get("services", {}) if isinstance(data, dict) else {}
    service = services.get(service_name, {}) if isinstance(services, dict) else {}
    return service if isinstance(service, dict) else {}


def _docker_compose_dependency_summary(compose_file: Path) -> dict[str, object]:
    bridge = _compose_service(compose_file, "mpf-v2raya-socks-bridge")
    forwarder = _compose_service(compose_file, "mpf-forwarder-btc")
    return {
        "project_name": _PROJECT_NAME,
        "compose_file": _COMPOSE_FILE,
        "profile": _PROFILE,
        "socks_bridge_depends_on": bridge.get("depends_on", {}),
        "forwarder_depends_on": forwarder.get("depends_on", {}),
    }


def _socks_bridge_runtime_model(compose_file: Path) -> dict[str, object]:
    bridge = _compose_service(compose_file, "mpf-v2raya-socks-bridge")
    return {
        "container": "mpf-v2raya-socks-bridge",
        "network_mode": bridge.get("network_mode"),
        "command": bridge.get("command", []),
        "host_port_publish_allowed": False,
        "host_port_22070_published": bool(bridge.get("ports")),
        "expected_internal_listener": "127.0.0.1:22070 inside mpf-v2raya network namespace",
        "expected_upstream_target": "127.0.0.1:20170 inside mpf-v2raya network namespace",
    }


def _list_value(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _unknown_mpf_artifacts_detected(*, diagnosis: dict[str, object], artifact_gate_report: dict[str, object] | None = None) -> bool:
    direct_unknown = _list_value(diagnosis.get("unknown_mpf_artifacts"))
    if direct_unknown:
        return True

    gate_summary = diagnosis.get("current_controlled_artifact_gate_summary")
    if isinstance(gate_summary, dict) and _list_value(gate_summary.get("unknown_mpf_artifacts")):
        return True

    if diagnosis.get("unknown_mpf_artifacts_empty") is False:
        return True

    blockers = [str(item) for item in _list_value(diagnosis.get("blockers"))]
    if "unknown_mpf_artifacts_present" in blockers:
        return True

    if artifact_gate_report is not None and _list_value(artifact_gate_report.get("unknown_mpf_artifacts")):
        return True

    return False


def _likely_bridge_failure_reason(containers: list[docker_compose.DockerContainerSummary]) -> str | None:
    for container in containers:
        if container.name != "mpf-v2raya-socks-bridge":
            continue
        status = container.status.lower()
        if "exited" in status:
            return "socks_bridge_container_exited_after_reboot"
        if "unhealthy" in status:
            return "socks_bridge_healthcheck_unhealthy_after_reboot"
        if "health: starting" in status:
            return "socks_bridge_healthcheck_still_starting"
        if not status.startswith("up"):
            return "socks_bridge_not_running_after_reboot"
    if containers and "mpf-v2raya-socks-bridge" not in {item.name for item in containers}:
        return "socks_bridge_container_missing_after_reboot"
    return None


def _phase_gate_summary() -> dict[str, object]:
    return {
        "current_accepted_phase": "Phase 11 — Production / Customer Activation Gate accepted on farm5",
        "current_working_phase": "Phase 11 operational completion — Full CLI Production Operations",
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
    }



def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical_compose_path() -> Path:
    return _repository_root() / _COMPOSE_FILE


def validate_compose_scope(configured_path: Path | str) -> dict[str, object]:
    """Validate configured Compose path by canonical resolved file identity."""

    configured = Path(configured_path)
    canonical = _canonical_compose_path()
    result: dict[str, object] = {
        "configured_path": str(configured_path),
        "canonical_path": _COMPOSE_FILE,
        "configured_resolved_path": None,
        "canonical_resolved_path": None,
        "same_file": False,
        "valid": False,
        "blocker": None,
    }
    try:
        canonical_resolved = canonical.resolve(strict=True)
    except OSError:
        result["blocker"] = "compose_file_missing"
        return result
    result["canonical_resolved_path"] = str(canonical_resolved)

    try:
        candidate = configured if configured.is_absolute() else (_repository_root() / configured)
        configured_resolved = candidate.resolve(strict=True)
    except OSError:
        result["blocker"] = "compose_file_missing"
        return result

    result["configured_resolved_path"] = str(configured_resolved)
    same_file = configured_resolved == canonical_resolved
    result["same_file"] = same_file
    result["valid"] = same_file
    if not same_file:
        result["blocker"] = "compose_scope_mismatch"
    return result


def _diagnosis_has_controlled_artifact_absent(diagnosis: dict[str, object], artifact_gate_report: dict[str, object] | None) -> bool:
    blockers = [str(item) for item in _list_value(diagnosis.get("blockers"))]
    if "post_reboot_known_controlled_phase11_artifacts_absent" in blockers:
        return True
    if diagnosis.get("known_controlled_phase11_artifacts_present") is False:
        return True
    gate_summary = diagnosis.get("current_controlled_artifact_gate_summary")
    if isinstance(gate_summary, dict) and gate_summary.get("known_controlled_artifacts_present") is False:
        return True
    if artifact_gate_report is not None and artifact_gate_report.get("known_controlled_artifacts_present") is False:
        return True
    return False


def _artifact_capability_implemented() -> bool:
    try:
        from mpf.services import phase11_controlled_artifact_reapply_executor_service, phase11_controlled_artifact_reapply_package_service
    except Exception:
        return False
    return callable(getattr(phase11_controlled_artifact_reapply_package_service, "build_controlled_artifact_reapply_package_report", None)) and callable(getattr(phase11_controlled_artifact_reapply_executor_service, "execute_controlled_artifact_reapply_package", None))


def _artifact_execution_available(artifact_gate_report: dict[str, object] | None) -> bool:
    return bool(artifact_gate_report and artifact_gate_report.get("execution_package_available"))


def _snapshot_summary(plan: dict[str, object]) -> dict[str, object]:
    listener_checks = plan.get("local_only_listener_state", {}).get("checks", {}) if isinstance(plan.get("local_only_listener_state"), dict) else {}
    return {
        "expected_runtime_containers": plan.get("expected_runtime_containers", []),
        "actual_runtime_container_names": [item.get("name") for item in _list_value(plan.get("actual_runtime_containers")) if isinstance(item, dict)],
        "missing_containers": plan.get("missing_containers", []),
        "unhealthy_containers": plan.get("unhealthy_containers", []),
        "unexpected_project_containers": plan.get("unexpected_project_containers", []),
        "listener_checks": listener_checks,
        "compose_scope_validation": plan.get("compose_scope_validation", {}),
        "controlled_artifact_reapply_required": plan.get("controlled_artifact_reapply_required"),
        "controlled_artifact_reapply_execution_available": plan.get("controlled_artifact_reapply_execution_available"),
    }


def build_phase11_restart_autostart_persistence_fix_plan_report(
    *,
    expected_containers: Iterable[str] | None = None,
    actual_containers: Iterable[docker_compose.DockerContainerSummary] | None = None,
    listening_sockets: Iterable[socket_inspector.ListeningSocket] | None = None,
    diagnosis_report: dict[str, object] | None = None,
    artifact_gate_report: dict[str, object] | None = None,
    compose_file: Path = Path(_COMPOSE_FILE),
    expected_version: str = __version__,
) -> dict[str, object]:
    """Build the read-only controlled runtime persistence fix plan from explicit observations."""

    expected = sorted(set(expected_containers or EXPECTED_RUNTIME_CONTAINERS))
    safety_blockers: list[str] = []
    warnings: list[str] = []
    observations_supplied = actual_containers is not None and listening_sockets is not None
    if not observations_supplied:
        safety_blockers.append("runtime_observations_not_supplied")
        containers: list[docker_compose.DockerContainerSummary] = []
        socket_list: list[socket_inspector.ListeningSocket] = []
    else:
        containers = list(actual_containers)
        socket_list = list(listening_sockets)

    actual_names = sorted(item.name for item in containers)
    missing = sorted(set(expected) - set(actual_names)) if observations_supplied else []
    health = _container_report(containers)
    unhealthy = sorted(
        item["name"] for item in health if item["name"] in expected and (not item["running"] or not item["healthy"])
    ) if observations_supplied else []
    unexpected = sorted(set(actual_names) - set(expected)) if observations_supplied else []
    listeners = _local_only_listener_state(socket_list) if observations_supplied else {"checks": {}, "blockers": ["runtime_observations_not_supplied"]}
    diagnosis = diagnosis_report or build_phase11_restart_autostart_persistence_diagnosis_report(
        expected_containers=expected,
        actual_containers=containers,
        listening_sockets=socket_list,
        artifact_gate_report=artifact_gate_report,
        expected_version=expected_version,
    )

    runtime_repair_reasons: list[str] = []
    remaining_persistence_reasons: list[str] = []

    if expected_version != __version__:
        safety_blockers.append("wrong_expected_version")

    runtime_repair_reasons.extend(f"missing_container:{name}" for name in missing)
    runtime_repair_reasons.extend(f"unhealthy_container:{name}" for name in unhealthy)

    for listener_blocker in listeners["blockers"]:
        blocker = str(listener_blocker)
        if blocker.startswith("missing_listener:"):
            runtime_repair_reasons.append(blocker)
        elif blocker != "runtime_observations_not_supplied":
            safety_blockers.append(blocker)

    if unexpected:
        safety_blockers.extend(f"unexpected_project_container:{name}" for name in unexpected)

    compose_scope_validation = validate_compose_scope(compose_file)
    if compose_scope_validation.get("blocker"):
        safety_blockers.append(str(compose_scope_validation["blocker"]))

    try:
        phase_status_text = (_repository_root() / "docs/PHASE_STATUS.md").read_text(encoding="utf-8", errors="ignore")
    except OSError:
        phase_status_text = ""
    if "Phase 11 operational completion" not in phase_status_text:
        safety_blockers.append("phase_gate_mismatch")
    if _unknown_mpf_artifacts_detected(diagnosis=diagnosis, artifact_gate_report=artifact_gate_report):
        safety_blockers.append("unknown_mpf_artifacts_detected")
    if diagnosis.get("backend_public_exposure_detected") is True:
        safety_blockers.append("backend_public_exposure_detected")

    phase_summary = _phase_gate_summary()
    if phase_summary["phase12_start_allowed"] is not False:
        safety_blockers.append("phase12_opened")
    if phase_summary["worker_enforcement_allowed"] != "no":
        safety_blockers.append("worker_enforcement_opened")
    if phase_summary["ui_allowed"] != "no":
        safety_blockers.append("ui_opened")
    if phase_summary["telegram_allowed"] != "no":
        safety_blockers.append("telegram_opened")

    controlled_artifact_reapply_required = _diagnosis_has_controlled_artifact_absent(diagnosis, artifact_gate_report) and not _unknown_mpf_artifacts_detected(diagnosis=diagnosis, artifact_gate_report=artifact_gate_report)
    controlled_artifact_reapply_capability_implemented = _artifact_capability_implemented()
    controlled_artifact_reapply_execution_available = _artifact_execution_available(artifact_gate_report)
    if controlled_artifact_reapply_required:
        remaining_persistence_reasons.append("post_reboot_known_controlled_phase11_artifacts_absent")
        if not controlled_artifact_reapply_execution_available:
            remaining_persistence_reasons.append("controlled_artifact_reapply_execution_package_unavailable")

    unique_safety = sorted(set(safety_blockers))
    unique_runtime_repair = sorted(set(runtime_repair_reasons))
    runtime_repair_required = bool(unique_runtime_repair)
    runtime_execution_allowed = not unique_safety and runtime_repair_required

    if unique_safety:
        final_decision = "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN"
        next_required_step = "fix_restart_autostart_persistence_gap"
    elif runtime_repair_required:
        final_decision = "RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN_READY"
        next_required_step = "run_restart_autostart_persistence_fix_on_farm5"
    else:
        final_decision = "NO_RUNTIME_REPAIR_REQUIRED"
        if controlled_artifact_reapply_required and controlled_artifact_reapply_capability_implemented:
            next_required_step = "implement_source_backed_controlled_artifact_renderer_and_production_adapters"
        elif controlled_artifact_reapply_required:
            next_required_step = "implement_controlled_artifact_reapply_execute_package"
        else:
            next_required_step = "collect_restart_autostart_proof_after_persistence_fix"

    return {
        "component": _COMPONENT,
        "repository_version": __version__,
        "expected_version": expected_version,
        "phase11_operational_completion_scope": _SCOPE,
        **phase_summary,
        "expected_runtime_containers": expected,
        "actual_runtime_containers": health,
        "missing_containers": missing,
        "unhealthy_containers": unhealthy,
        "unexpected_project_containers": unexpected,
        "local_only_listener_state": listeners,
        "compose_scope_validation": compose_scope_validation,
        "docker_compose_dependency_summary": _docker_compose_dependency_summary(_canonical_compose_path()),
        "socks_bridge_runtime_model": _socks_bridge_runtime_model(_canonical_compose_path()),
        "likely_socks_bridge_failure_reason": _likely_bridge_failure_reason(containers),
        "recommended_controlled_recovery_commands": [_EXECUTE_COMMAND] if runtime_execution_allowed else [],
        "pre_restore_safety_checks": _PRE_CHECK_COMMANDS,
        "post_restore_safety_checks": _POST_CHECK_COMMANDS,
        "diagnosis_summary": {
            "final_decision": diagnosis.get("final_decision"),
            "blockers": diagnosis.get("blockers", []),
            "unknown_mpf_artifacts": diagnosis.get("unknown_mpf_artifacts", []),
            "current_controlled_artifact_gate_summary": diagnosis.get("current_controlled_artifact_gate_summary", {}),
            "unknown_mpf_artifacts_empty": diagnosis.get("unknown_mpf_artifacts_empty"),
            "known_controlled_phase11_artifacts_present": diagnosis.get("known_controlled_phase11_artifacts_present"),
        },
        "runtime_repair_required": runtime_repair_required,
        "runtime_repair_reasons": unique_runtime_repair,
        "runtime_reconciliation_execution_allowed": runtime_execution_allowed,
        "controlled_artifact_reapply_required": controlled_artifact_reapply_required,
        "read_only_reapply_foundation_implemented": controlled_artifact_reapply_capability_implemented,
        "desired_artifact_semantics_complete": False,
        "production_execution_available": False,
        "live_ready_package_available": False,
        "controlled_artifact_reapply_capability_implemented": controlled_artifact_reapply_capability_implemented,
        "controlled_artifact_reapply_execution_available": controlled_artifact_reapply_execution_available,
        "remaining_persistence_reasons": sorted(set(remaining_persistence_reasons)),
        "backend_public_exposure_detected": diagnosis.get("backend_public_exposure_detected") is True,
        "repair_reasons": unique_runtime_repair,
        "safety_blockers": unique_safety,
        "blockers": sorted(set([*unique_runtime_repair, *unique_safety, *remaining_persistence_reasons])),
        "warnings": sorted(set(warnings)),
        **_MUTATION_FLAGS,
        "observations_supplied": observations_supplied,
        "final_decision": final_decision,
        "next_required_step": next_required_step,
    }


def build_phase11_restart_autostart_persistence_fix_package_from_plan(
    plan_report: dict[str, object],
    *,
    expected_version: str = __version__,
) -> dict[str, object]:
    """Build an operator package from the exact supplied plan report."""

    safety_blockers = list(_list_value(plan_report.get("safety_blockers")))
    phase_summary = _phase_gate_summary()
    allowed_operation_set = ["controlled_docker_compose_runtime_reconciliation_up_no_build_pull_never"]
    command_scope = {
        "project_name": _PROJECT_NAME,
        "compose_file": _COMPOSE_FILE,
        "profile": _PROFILE,
        "execute_command": _EXECUTE_COMMAND,
    }
    if expected_version != __version__:
        safety_blockers.append("wrong_expected_version")
    if phase_summary["phase12_start_allowed"] is not False:
        safety_blockers.append("phase12_opened")
    if phase_summary["worker_enforcement_allowed"] != "no":
        safety_blockers.append("worker_enforcement_opened")
    if phase_summary["ui_allowed"] != "no":
        safety_blockers.append("ui_opened")
    if phase_summary["telegram_allowed"] != "no":
        safety_blockers.append("telegram_opened")

    compose_scope = plan_report.get("compose_scope_validation", {})
    if not isinstance(compose_scope, dict) or compose_scope.get("valid") is not True:
        safety_blockers.append(str(compose_scope.get("blocker") or "compose_scope_mismatch") if isinstance(compose_scope, dict) else "compose_scope_mismatch")
    if plan_report.get("observations_supplied") is not True:
        safety_blockers.append("runtime_observations_not_supplied")
    if plan_report.get("backend_public_exposure_detected") is True:
        safety_blockers.append("backend_public_exposure_detected")

    runtime_repair_reasons = sorted(set(str(item) for item in _list_value(plan_report.get("runtime_repair_reasons", plan_report.get("repair_reasons", [])))))
    runtime_repair_required = bool(plan_report.get("runtime_repair_required")) and bool(runtime_repair_reasons)
    runtime_allowed = bool(plan_report.get("runtime_reconciliation_execution_allowed"))
    unique_safety = sorted(set(safety_blockers))

    exact_scope_ok = command_scope == {
        "project_name": "mpf-proxy",
        "compose_file": "compose/mpf-proxy.compose.yaml",
        "profile": "phase4-runtime",
        "execute_command": "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never",
    }
    if not exact_scope_ok:
        unique_safety = sorted(set([*unique_safety, "compose_scope_mismatch"]))

    package_ready = not unique_safety and runtime_repair_required and bool(runtime_repair_reasons) and runtime_allowed and exact_scope_ok
    if unique_safety:
        final_decision = "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE"
        next_required_step = "fix_restart_autostart_persistence_gap"
    elif package_ready:
        final_decision = "RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE_READY"
        next_required_step = "run_restart_autostart_persistence_fix_on_farm5"
    else:
        final_decision = "NO_RUNTIME_REPAIR_REQUIRED"
        next_required_step = plan_report.get("next_required_step", "collect_restart_autostart_proof_after_persistence_fix")

    return {
        "package_type": "phase11_restart_autostart_persistence_fix",
        "repository_version": __version__,
        "expected_version": expected_version,
        "phase_gate_summary": phase_summary,
        "fix_plan_final_decision": plan_report.get("final_decision"),
        "source_plan_final_decision": plan_report.get("final_decision"),
        "source_plan_runtime_repair_required": plan_report.get("runtime_repair_required"),
        "source_plan_runtime_repair_reasons": runtime_repair_reasons,
        "source_plan_safety_blockers": plan_report.get("safety_blockers", []),
        "source_plan_snapshot_summary": _snapshot_summary(plan_report),
        "exact_allowed_operation_set": allowed_operation_set,
        "exact_docker_compose_command_plan": command_scope,
        "required_pre_check_commands": _PRE_CHECK_COMMANDS,
        "required_execute_command": _EXECUTE_COMMAND if package_ready else None,
        "required_post_check_commands": _POST_CHECK_COMMANDS if package_ready else [],
        "forbidden_operations": _FORBIDDEN_OPERATIONS,
        "rollback_note": "Code rollback is reverting this PR; runtime rollback must use reviewed operator evidence and existing controlled restore paths, not ad-hoc firewall or DB mutation.",
        "mutation_declaration": {
            **_MUTATION_FLAGS,
            "package_helper_execute_mode_may_perform_reviewed_docker_compose_up": package_ready,
            "normal_service_code_performs_mutation": False,
        },
        "operator_confirmation_requirements": [
            "operator reviewed the package JSON",
            "operator confirmed farm5 Phase 11 operational completion gate is current",
            "operator confirmed Phase 12, worker enforcement, UI, Telegram, and public API remain blocked",
            "operator confirmed backend public exposure is false before execution",
            "operator invokes helper with --execute --yes only when package final_decision is READY",
        ],
        "runtime_repair_required": runtime_repair_required,
        "runtime_repair_reasons": runtime_repair_reasons,
        "runtime_reconciliation_execution_allowed": package_ready,
        "controlled_artifact_reapply_required": plan_report.get("controlled_artifact_reapply_required"),
        "controlled_artifact_reapply_execution_available": plan_report.get("controlled_artifact_reapply_execution_available"),
        "remaining_persistence_reasons": plan_report.get("remaining_persistence_reasons", []),
        "repair_reasons": runtime_repair_reasons,
        "safety_blockers": unique_safety,
        "blockers": sorted(set([*runtime_repair_reasons, *unique_safety])),
        "warnings": plan_report.get("warnings", []),
        "observations_supplied": plan_report.get("observations_supplied") is True,
        "backend_public_exposure_detected": plan_report.get("backend_public_exposure_detected", False),
        "final_decision": final_decision,
        "next_required_step": next_required_step,
    }


def build_phase11_restart_autostart_persistence_fix_package(
    *,
    diagnosis_report: dict[str, object] | None = None,
    artifact_gate_report: dict[str, object] | None = None,
    expected_version: str = __version__,
) -> dict[str, object]:
    """Backward-compatible pure package builder that fails closed without observations."""

    plan = build_phase11_restart_autostart_persistence_fix_plan_report(
        diagnosis_report=diagnosis_report,
        artifact_gate_report=artifact_gate_report,
        expected_version=expected_version,
    )
    return build_phase11_restart_autostart_persistence_fix_package_from_plan(plan, expected_version=expected_version)



def _collect_project_containers_read_only(project_name: str) -> tuple[bool, list[docker_compose.DockerContainerSummary], str | None]:
    cmd = [
        "docker",
        "ps",
        "-a",
        "--filter",
        f"label=com.docker.compose.project={project_name}",
        "--format",
        "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}",
    ]
    try:
        result = subprocess.run(cmd, text=True, capture_output=True)
    except FileNotFoundError:
        return False, [], "docker_command_not_available"
    if result.returncode != 0:
        return False, [], (result.stderr or result.stdout or "docker_read_failed").strip()
    containers: list[docker_compose.DockerContainerSummary] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        while len(parts) < 4:
            parts.append("")
        containers.append(docker_compose.DockerContainerSummary(parts[0], parts[1], parts[2], parts[3]))
    return True, containers, None


def _split_socket_local(local: str) -> tuple[str, int | None]:
    if local.startswith("[") and "]:" in local:
        address, port_text = local.rsplit(":", 1)
    elif ":" in local:
        address, port_text = local.rsplit(":", 1)
    else:
        return local, None
    try:
        return address, int(port_text)
    except ValueError:
        return address, None


def _collect_listening_sockets_read_only() -> tuple[bool, list[socket_inspector.ListeningSocket], str | None]:
    try:
        result = subprocess.run(["ss", "-lntp"], text=True, capture_output=True)
    except FileNotFoundError:
        return False, [], "ss_command_not_available"
    if result.returncode != 0:
        return False, [], (result.stderr or result.stdout or "socket_read_failed").strip()
    sockets: list[socket_inspector.ListeningSocket] = []
    for line in result.stdout.splitlines():
        if not line.startswith("LISTEN"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        address, port = _split_socket_local(parts[3])
        if port is None:
            continue
        process = parts[-1] if len(parts) >= 7 else None
        sockets.append(socket_inspector.ListeningSocket(address, port, process))
    return True, sockets, None

def _build_artifact_gate_report(expected_version: str) -> dict[str, object]:
    from mpf.services.phase11_restart_autostart_persistence_diagnosis_service import _build_artifact_gate_report as build_gate

    return build_gate(expected_version)


def run_phase11_restart_autostart_persistence_fix_plan(config_path: Path = DEFAULT_CONFIG_PATH, *, expected_version: str = __version__) -> dict[str, object]:
    """Inspect read-only Docker/socket/config state once and return the fix plan."""

    cfg = load_config(config_path)
    containers_ok, containers, containers_error = _collect_project_containers_read_only(cfg.proxy.project_name)
    sockets_ok, sockets, sockets_error = _collect_listening_sockets_read_only()
    artifact_gate = _build_artifact_gate_report(expected_version)
    required_socket_ports = {2015, 60010}
    required_sockets_seen = {socket.port for socket in sockets if socket.port in required_socket_ports}
    empty_runtime_snapshot = containers_ok and sockets_ok and not containers and not required_sockets_seen
    observations_ok = containers_ok and sockets_ok and not empty_runtime_snapshot
    if empty_runtime_snapshot:
        containers_error = containers_error or "runtime_observations_unavailable_or_empty_dev_snapshot"
        sockets_error = sockets_error or "runtime_observations_unavailable_or_empty_dev_snapshot"
    diagnosis = (
        build_phase11_restart_autostart_persistence_diagnosis_report(
            actual_containers=containers,
            listening_sockets=sockets,
            artifact_gate_report=artifact_gate,
            expected_version=expected_version,
        )
        if observations_ok
        else {
            "final_decision": "BLOCKED_READ_ONLY_RUNTIME_OBSERVATIONS_UNAVAILABLE",
            "blockers": [item for item in (containers_error, sockets_error) if item],
            "unknown_mpf_artifacts": artifact_gate.get("unknown_mpf_artifacts", []),
            "unknown_mpf_artifacts_empty": artifact_gate.get("unknown_mpf_artifacts") == [],
        }
    )
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=containers if observations_ok else None,
        listening_sockets=sockets if observations_ok else None,
        diagnosis_report=diagnosis,
        artifact_gate_report=artifact_gate,
        compose_file=cfg.proxy.compose_file,
        expected_version=expected_version,
    )
    report["runtime_observation_errors"] = [item for item in (containers_error, sockets_error) if item]
    return report


def run_phase11_restart_autostart_persistence_fix_package(config_path: Path = DEFAULT_CONFIG_PATH, *, expected_version: str = __version__) -> dict[str, object]:
    """Build the package from the exact live read-only plan snapshot."""

    plan = run_phase11_restart_autostart_persistence_fix_plan(config_path, expected_version=expected_version)
    return build_phase11_restart_autostart_persistence_fix_package_from_plan(plan, expected_version=expected_version)
