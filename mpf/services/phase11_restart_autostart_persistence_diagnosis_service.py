"""Read-only Phase 11 post-reboot restart/autostart persistence diagnosis."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
import subprocess
from typing import Any

from mpf import __version__
from mpf.adapters import docker_compose, socket_inspector
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.services import phase11_controlled_backend_target_service
from mpf.services.phase11_current_controlled_artifact_gate_service import (
    build_phase11_current_controlled_artifact_gate_report,
)
from mpf.services.proxy_doctor_service import EXPECTED_RUNTIME_CONTAINERS


_COMPONENT = "phase11_restart_autostart_persistence_diagnosis"
_BLOCKED = "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_GAP"
_READY = "RESTART_AUTOSTART_PERSISTENCE_READY"
_REQUIRED_LOCAL_LISTENERS = {
    "v2raya_ui": 2015,
    "btc_backend": 60010,
}
_MUTATION_FLAGS: dict[str, bool] = {
    "mutation_performed": False,
    "db_mutation_performed": False,
    "firewall_apply_performed": False,
    "conntrack_flush_performed": False,
    "docker_restart_performed": False,
    "systemd_restart_performed": False,
}


def _container_present(container: docker_compose.DockerContainerSummary) -> bool:
    return bool(container.name)


def _container_running(container: docker_compose.DockerContainerSummary) -> bool:
    return container.status.lower().startswith("up")


def _container_healthy(container: docker_compose.DockerContainerSummary) -> bool:
    status = container.status.lower()
    if not _container_running(container):
        return False
    if "unhealthy" in status or "health: starting" in status:
        return False
    return "healthy" in status or "health" not in status


def _container_health(containers: Iterable[docker_compose.DockerContainerSummary]) -> list[dict[str, object]]:
    return [
        {
            **asdict(container),
            "present": _container_present(container),
            "running": _container_running(container),
            "healthy": _container_healthy(container),
        }
        for container in sorted(containers, key=lambda item: item.name)
    ]


def _listener_state(sockets: Iterable[socket_inspector.ListeningSocket]) -> dict[str, object]:
    socket_list = list(sockets)
    checks: dict[str, dict[str, object]] = {}
    blockers: list[str] = []

    for name, port in _REQUIRED_LOCAL_LISTENERS.items():
        matches = [socket for socket in socket_list if socket.port == port]
        local_only = bool(matches) and all(socket_inspector.is_local_bind_address(socket.local_address) for socket in matches)
        public = any(socket_inspector.is_public_bind_address(socket.local_address) for socket in matches)
        if not matches:
            blockers.append(f"missing_listener:{name}:{port}")
        elif not local_only or public:
            blockers.append(f"non_local_listener:{name}:{port}")
        checks[name] = {
            "port": port,
            "present": bool(matches),
            "local_only": local_only,
            "public_bind_detected": public,
            "listeners": [asdict(socket) for socket in matches],
        }

    return {"checks": checks, "blockers": blockers}


def _read_command_stdout(command: list[str]) -> str:
    try:
        result = subprocess.run(command, text=True, capture_output=True)
    except FileNotFoundError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout


def _build_artifact_gate_report(expected_version: str) -> dict[str, object]:
    backend_target = phase11_controlled_backend_target_service.build_controlled_backend_target_report(expected_version=expected_version)
    expected_backend_target = phase11_controlled_backend_target_service.expected_backend_target_from_report(backend_target)
    iptables_save_text = _read_command_stdout(["iptables-save"])
    ip6tables_save_text = _read_command_stdout(["ip6tables-save"])
    try:
        phase_status_text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    except OSError:
        phase_status_text = ""
    report = build_phase11_current_controlled_artifact_gate_report(
        iptables_save_text=iptables_save_text,
        ip6tables_save_text=ip6tables_save_text,
        phase_status_text=phase_status_text,
        expected_version=expected_version,
        expected_backend_target=expected_backend_target,
    )
    report["backend_target_resolution"] = backend_target
    return report


def build_phase11_restart_autostart_persistence_diagnosis_report(
    *,
    expected_containers: Iterable[str] | None = None,
    actual_containers: Iterable[docker_compose.DockerContainerSummary] | None = None,
    listening_sockets: Iterable[socket_inspector.ListeningSocket] | None = None,
    artifact_gate_report: dict[str, object] | None = None,
    expected_version: str = __version__,
) -> dict[str, object]:
    """Build a read-only post-reboot persistence diagnosis from supplied observations."""

    expected = sorted(set(expected_containers or EXPECTED_RUNTIME_CONTAINERS))
    containers = list(actual_containers or [])
    actual_names = sorted(container.name for container in containers)
    missing = sorted(set(expected) - set(actual_names))
    unexpected_project_containers = sorted(set(actual_names) - set(expected))
    health = _container_health(containers)
    unhealthy_expected = sorted(
        item["name"]
        for item in health
        if item["name"] in expected and (not item["running"] or not item["healthy"])
    )
    listener_summary = _listener_state(listening_sockets or [])

    gate = artifact_gate_report or {}
    known_present = gate.get("known_controlled_artifacts_present") is True
    unknown_artifacts = gate.get("unknown_mpf_artifacts") if isinstance(gate.get("unknown_mpf_artifacts"), list) else []
    unknown_empty = unknown_artifacts == []
    post_reboot_firewall_customer_artifacts_missing = not known_present

    blockers: list[str] = []
    if expected_version != __version__:
        blockers.append("wrong_expected_version")
    blockers.extend(f"missing_container:{name}" for name in missing)
    blockers.extend(f"unhealthy_container:{name}" for name in unhealthy_expected)
    blockers.extend(str(blocker) for blocker in listener_summary["blockers"])
    if not known_present:
        blockers.append("post_reboot_known_controlled_phase11_artifacts_absent")
    if not unknown_empty:
        blockers.append("unknown_mpf_artifacts_present")

    ready = not blockers
    return {
        "component": _COMPONENT,
        "repository_version": __version__,
        "expected_version": expected_version,
        "phase11_operational_completion_scope": "full_cli_production_operations",
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "expected_runtime_containers": expected,
        "actual_docker_project_containers": actual_names,
        "missing_containers": missing,
        "unexpected_project_containers": unexpected_project_containers,
        "container_health": health,
        "local_only_listener_state": listener_summary["checks"],
        "current_controlled_artifact_gate_summary": {
            "final_decision": gate.get("final_decision", "UNKNOWN"),
            "known_controlled_artifacts_present": known_present,
            "allowed_controlled_artifacts": gate.get("allowed_controlled_artifacts", []),
            "unknown_mpf_artifacts": unknown_artifacts,
            "blockers": gate.get("blockers", []),
            "warnings": gate.get("warnings", []),
        },
        "known_controlled_phase11_artifacts_present": known_present,
        "unknown_mpf_artifacts_empty": unknown_empty,
        "post_reboot_firewall_customer_artifacts_missing": post_reboot_firewall_customer_artifacts_missing,
        "blockers": sorted(set(blockers)),
        "warnings": [
            "read_only_post_reboot_diagnosis_only",
            "restart_autostart_proof_remains_missing_or_partial_until_persistence_gap_is_fixed",
        ] if not ready else [],
        **_MUTATION_FLAGS,
        "final_decision": _READY if ready else _BLOCKED,
        "next_required_step": "implement_production_customer_lifecycle_execution" if ready else "fix_restart_autostart_persistence_gap",
    }


def run_phase11_restart_autostart_persistence_diagnosis(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    expected_version: str = __version__,
) -> dict[str, object]:
    """Inspect Docker, sockets, and firewall snapshots using read-only commands only."""

    cfg = load_config(config_path)
    containers = docker_compose.list_project_containers(cfg.proxy.project_name)
    sockets = socket_inspector.list_listening_tcp_sockets()
    artifact_gate = _build_artifact_gate_report(expected_version)
    return build_phase11_restart_autostart_persistence_diagnosis_report(
        actual_containers=containers,
        listening_sockets=sockets,
        artifact_gate_report=artifact_gate,
        expected_version=expected_version,
    )
