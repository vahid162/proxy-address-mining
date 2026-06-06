"""Read-only Phase 11 restart/autostart persistence fix planning.

This module intentionally does not execute Docker Compose, systemd, DB, firewall,
iptables-restore, or conntrack operations.  It only builds an operator-reviewed
plan/package for the accepted controlled Phase 11 runtime boundary.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
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
    """Build the read-only controlled runtime persistence fix plan."""

    expected = sorted(set(expected_containers or EXPECTED_RUNTIME_CONTAINERS))
    containers = list(actual_containers or [])
    actual_names = sorted(item.name for item in containers)
    missing = sorted(set(expected) - set(actual_names))
    health = _container_report(containers)
    unhealthy = sorted(
        item["name"] for item in health if item["name"] in expected and (not item["running"] or not item["healthy"])
    )
    unexpected = sorted(set(actual_names) - set(expected))
    listeners = _local_only_listener_state(listening_sockets or [])
    diagnosis = diagnosis_report or build_phase11_restart_autostart_persistence_diagnosis_report(
        expected_containers=expected,
        actual_containers=containers,
        listening_sockets=listening_sockets or [],
        artifact_gate_report=artifact_gate_report,
        expected_version=expected_version,
    )

    repair_reasons: list[str] = []
    safety_blockers: list[str] = []
    warnings: list[str] = []

    if expected_version != __version__:
        safety_blockers.append("wrong_expected_version")

    repair_reasons.extend(f"missing_container:{name}" for name in missing)
    repair_reasons.extend(f"unhealthy_container:{name}" for name in unhealthy)

    for listener_blocker in listeners["blockers"]:
        blocker = str(listener_blocker)
        if blocker.startswith("missing_listener:"):
            repair_reasons.append(blocker)
        else:
            safety_blockers.append(blocker)

    if unexpected:
        safety_blockers.extend(f"unexpected_project_container:{name}" for name in unexpected)
    if not compose_file.exists():
        safety_blockers.append("compose_file_missing")
    if str(compose_file) not in {_COMPOSE_FILE, f"./{_COMPOSE_FILE}"}:
        safety_blockers.append("compose_scope_mismatch")
    if "Phase 11 operational completion" not in Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8", errors="ignore"):
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

    ready = not safety_blockers
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
        "docker_compose_dependency_summary": _docker_compose_dependency_summary(compose_file),
        "socks_bridge_runtime_model": _socks_bridge_runtime_model(compose_file),
        "likely_socks_bridge_failure_reason": _likely_bridge_failure_reason(containers),
        "recommended_controlled_recovery_commands": [_EXECUTE_COMMAND],
        "pre_restore_safety_checks": _PRE_CHECK_COMMANDS,
        "post_restore_safety_checks": _POST_CHECK_COMMANDS,
        "diagnosis_summary": {
            "final_decision": diagnosis.get("final_decision"),
            "blockers": diagnosis.get("blockers", []),
            "unknown_mpf_artifacts": diagnosis.get("unknown_mpf_artifacts", []),
            "current_controlled_artifact_gate_summary": diagnosis.get("current_controlled_artifact_gate_summary", {}),
            "unknown_mpf_artifacts_empty": diagnosis.get("unknown_mpf_artifacts_empty"),
        },
        "repair_reasons": sorted(set(repair_reasons)),
        "safety_blockers": sorted(set(safety_blockers)),
        "blockers": sorted(set([*repair_reasons, *safety_blockers])),
        "warnings": sorted(set(warnings)),
        **_MUTATION_FLAGS,
        "final_decision": "RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN_READY" if ready else "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN",
        "next_required_step": "run_restart_autostart_persistence_fix_on_farm5" if ready else "fix_restart_autostart_persistence_gap",
    }


def build_phase11_restart_autostart_persistence_fix_package(
    *,
    diagnosis_report: dict[str, object] | None = None,
    artifact_gate_report: dict[str, object] | None = None,
    expected_version: str = __version__,
) -> dict[str, object]:
    """Build an operator-reviewed controlled Docker Compose recovery package."""

    plan = build_phase11_restart_autostart_persistence_fix_plan_report(
        diagnosis_report=diagnosis_report,
        artifact_gate_report=artifact_gate_report,
        expected_version=expected_version,
    )
    safety_blockers = list(plan.get("safety_blockers", []))
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
    diagnosis_summary = plan.get("diagnosis_summary", {})
    if isinstance(diagnosis_summary, dict) and _unknown_mpf_artifacts_detected(diagnosis=diagnosis_summary, artifact_gate_report=artifact_gate_report):
        safety_blockers.append("unknown_mpf_artifacts_detected")
    if command_scope != {
        "project_name": "mpf-proxy",
        "compose_file": "compose/mpf-proxy.compose.yaml",
        "profile": "phase4-runtime",
        "execute_command": "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never",
    }:
        safety_blockers.append("compose_scope_mismatch")
    package_ready = not sorted(set(safety_blockers))
    return {
        "package_type": "phase11_restart_autostart_persistence_fix",
        "repository_version": __version__,
        "expected_version": expected_version,
        "phase_gate_summary": phase_summary,
        "fix_plan_final_decision": plan["final_decision"],
        "exact_allowed_operation_set": allowed_operation_set,
        "exact_docker_compose_command_plan": command_scope,
        "required_pre_check_commands": _PRE_CHECK_COMMANDS,
        "required_execute_command": _EXECUTE_COMMAND,
        "required_post_check_commands": _POST_CHECK_COMMANDS,
        "forbidden_operations": _FORBIDDEN_OPERATIONS,
        "rollback_note": "Code rollback is reverting this PR; runtime rollback must use reviewed operator evidence and existing controlled restore paths, not ad-hoc firewall or DB mutation.",
        "mutation_declaration": {
            **_MUTATION_FLAGS,
            "package_helper_execute_mode_may_perform_reviewed_docker_compose_up": True,
            "normal_service_code_performs_mutation": False,
        },
        "operator_confirmation_requirements": [
            "operator reviewed the package JSON",
            "operator confirmed farm5 Phase 11 operational completion gate is current",
            "operator confirmed Phase 12, worker enforcement, UI, Telegram, and public API remain blocked",
            "operator confirmed backend public exposure is false before execution",
            "operator invokes helper with --execute --yes only after review",
        ],
        "repair_reasons": plan.get("repair_reasons", []),
        "safety_blockers": sorted(set(safety_blockers)),
        "blockers": sorted(set([*plan.get("repair_reasons", []), *safety_blockers])),
        "warnings": plan["warnings"],
        "final_decision": "RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE_READY" if package_ready else "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE",
        "next_required_step": "run_restart_autostart_persistence_fix_on_farm5" if package_ready else "fix_restart_autostart_persistence_gap",
    }


def run_phase11_restart_autostart_persistence_fix_plan(config_path: Path = DEFAULT_CONFIG_PATH, *, expected_version: str = __version__) -> dict[str, object]:
    """Inspect read-only Docker/socket state and return the fix plan."""

    cfg = load_config(config_path)
    return build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=docker_compose.list_project_containers(cfg.proxy.project_name),
        listening_sockets=socket_inspector.list_listening_tcp_sockets(),
        compose_file=cfg.proxy.compose_file,
        expected_version=expected_version,
    )
