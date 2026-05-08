from __future__ import annotations

from pathlib import Path

from mpf.adapters import docker_compose, socket_inspector
from mpf.config import DEFAULT_CONFIG_PATH, MPFConfig, load_config
from mpf.domain.health import HealthCheck, HealthReport, HealthStatus, worst_status


def run(config_path: Path = DEFAULT_CONFIG_PATH) -> HealthReport:
    """Run Phase 4 proxy doctor checks without mutating runtime state."""
    cfg = load_config(config_path)
    checks = build_checks(cfg)
    return HealthReport(component="proxy", final_verdict=worst_status(checks), checks=checks)


def config_check(config_path: Path = DEFAULT_CONFIG_PATH) -> HealthReport:
    """Check proxy-related config contracts only."""
    cfg = load_config(config_path)
    checks = [
        _runtime_activation_check(cfg),
        _v2raya_bind_check(cfg),
        *_lane_forwarder_config_checks(cfg),
    ]
    return HealthReport(component="proxy_config", final_verdict=worst_status(checks), checks=checks)


def status(config_path: Path = DEFAULT_CONFIG_PATH) -> HealthReport:
    """Inspect proxy project state without starting or stopping containers."""
    cfg = load_config(config_path)
    checks = [
        _compose_file_check(cfg),
        _container_state_check(cfg),
        *_listening_socket_checks(cfg),
    ]
    return HealthReport(component="proxy_status", final_verdict=worst_status(checks), checks=checks)


def build_checks(cfg: MPFConfig) -> list[HealthCheck]:
    return [
        _runtime_activation_check(cfg),
        _compose_file_check(cfg),
        _compose_config_check(cfg),
        _v2raya_bind_check(cfg),
        *_lane_forwarder_config_checks(cfg),
        _container_state_check(cfg),
        *_listening_socket_checks(cfg),
        _firewall_apply_mode_check(cfg),
    ]


def _runtime_activation_check(cfg: MPFConfig) -> HealthCheck:
    if cfg.proxy.runtime_activation_allowed:
        return HealthCheck(
            key="proxy.runtime_activation_allowed",
            status=HealthStatus.CRITICAL,
            message="proxy runtime activation is enabled during Phase 4 planning",
            evidence={"runtime_activation_allowed": True},
            remediation="Set proxy.runtime_activation_allowed to false until a runtime activation task is accepted.",
        )
    return HealthCheck(
        key="proxy.runtime_activation_allowed",
        status=HealthStatus.OK,
        message="proxy runtime activation remains disabled",
        evidence={"runtime_activation_allowed": False},
    )


def _compose_file_check(cfg: MPFConfig) -> HealthCheck:
    exists = docker_compose.compose_file_exists(cfg.proxy.compose_file)
    if not exists:
        return HealthCheck(
            key="compose_file_exists",
            status=HealthStatus.WARN,
            message="proxy compose file is not present yet",
            evidence={"compose_file": str(cfg.proxy.compose_file)},
            remediation="Add a Compose template before Phase 4 runtime activation.",
        )
    return HealthCheck(
        key="compose_file_exists",
        status=HealthStatus.OK,
        message="proxy compose file exists",
        evidence={"compose_file": str(cfg.proxy.compose_file)},
    )


def _compose_config_check(cfg: MPFConfig) -> HealthCheck:
    result = docker_compose.validate_compose_config(cfg.proxy.compose_file, cfg.proxy.project_name)
    if not result.ok:
        status = HealthStatus.WARN if result.message == "compose file is missing" else HealthStatus.CRITICAL
        return HealthCheck(
            key="compose_config_valid",
            status=status,
            message=result.message,
            evidence={"compose_file": str(result.compose_file), "project_name": cfg.proxy.project_name},
            remediation="Run docker compose config validation after adding the Compose template.",
        )
    return HealthCheck(
        key="compose_config_valid",
        status=HealthStatus.OK,
        message="docker compose config validates",
        evidence={"compose_file": str(result.compose_file), "project_name": cfg.proxy.project_name},
    )


def _v2raya_bind_check(cfg: MPFConfig) -> HealthCheck:
    host = cfg.v2raya.ui_bind_host
    if socket_inspector.is_public_bind_address(host):
        return HealthCheck(
            key="v2raya_ui_local_only",
            status=HealthStatus.CRITICAL,
            message="v2rayA UI is configured for a public bind address",
            evidence={"ui_bind_host": host, "ui_port": cfg.v2raya.ui_port},
            remediation="Bind v2rayA UI to 127.0.0.1 or a Unix/local-only path.",
        )
    if not socket_inspector.is_local_bind_address(host):
        return HealthCheck(
            key="v2raya_ui_local_only",
            status=HealthStatus.WARN,
            message="v2rayA UI bind is not clearly local-only",
            evidence={"ui_bind_host": host, "ui_port": cfg.v2raya.ui_port},
            remediation="Use 127.0.0.1 unless there is a reviewed local-only binding reason.",
        )
    return HealthCheck(
        key="v2raya_ui_local_only",
        status=HealthStatus.OK,
        message="v2rayA UI is configured local-only",
        evidence={"ui_bind_host": host, "ui_port": cfg.v2raya.ui_port},
    )


def _lane_forwarder_config_checks(cfg: MPFConfig) -> list[HealthCheck]:
    checks: list[HealthCheck] = []
    for lane_name, lane in sorted(cfg.lanes.items()):
        if not lane.enabled:
            continue
        if lane.forwarder is None:
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.forwarder_config",
                    status=HealthStatus.WARN,
                    message="enabled lane has no forwarder planning config",
                    evidence={"lane": lane_name, "backend_port": lane.backend_port},
                    remediation="Add lane.forwarder config before runtime activation.",
                )
            )
            continue
        bind_host = lane.forwarder.bind_host
        if socket_inspector.is_public_bind_address(bind_host):
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.forwarder_bind",
                    status=HealthStatus.CRITICAL,
                    message="lane forwarder is configured for a public bind address",
                    evidence={"lane": lane_name, "bind_host": bind_host, "backend_port": lane.backend_port},
                    remediation="Bind backend listeners to local/internal paths only.",
                )
            )
        else:
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.forwarder_bind",
                    status=HealthStatus.OK,
                    message="lane forwarder bind is not public",
                    evidence={"lane": lane_name, "bind_host": bind_host, "backend_port": lane.backend_port},
                )
            )
    return checks


def _container_state_check(cfg: MPFConfig) -> HealthCheck:
    containers = docker_compose.list_project_containers(cfg.proxy.project_name)
    if not containers:
        return HealthCheck(
            key="proxy_container_state",
            status=HealthStatus.OK,
            message="no proxy project containers are present during planning",
            evidence={"project_name": cfg.proxy.project_name, "containers": []},
        )
    return HealthCheck(
        key="proxy_container_state",
        status=HealthStatus.WARN,
        message="proxy project containers exist during planning",
        evidence={
            "project_name": cfg.proxy.project_name,
            "containers": [container.__dict__ for container in containers],
        },
        remediation="Do not start proxy runtime before an accepted runtime activation task.",
    )


def _listening_socket_checks(cfg: MPFConfig) -> list[HealthCheck]:
    sockets = socket_inspector.list_listening_tcp_sockets()
    checks: list[HealthCheck] = []

    ui_matches = [sock for sock in sockets if sock.port == cfg.v2raya.ui_port]
    if not ui_matches:
        checks.append(
            HealthCheck(
                key="v2raya_ui_listener_state",
                status=HealthStatus.OK,
                message="v2rayA UI port is not listening during planning",
                evidence={"ui_port": cfg.v2raya.ui_port},
            )
        )
    elif any(socket_inspector.is_public_bind_address(sock.local_address) for sock in ui_matches):
        checks.append(
            HealthCheck(
                key="v2raya_ui_listener_state",
                status=HealthStatus.CRITICAL,
                message="v2rayA UI is listening publicly",
                evidence={"matches": [sock.__dict__ for sock in ui_matches]},
                remediation="Stop the public listener and bind UI only to 127.0.0.1.",
            )
        )
    else:
        checks.append(
            HealthCheck(
                key="v2raya_ui_listener_state",
                status=HealthStatus.WARN,
                message="v2rayA UI port is already listening during planning",
                evidence={"matches": [sock.__dict__ for sock in ui_matches]},
                remediation="Runtime listeners require an accepted activation task.",
            )
        )

    for lane_name, lane in sorted(cfg.lanes.items()):
        if not lane.enabled:
            continue
        matches = [sock for sock in sockets if sock.port == lane.backend_port]
        if not matches:
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.backend_listener_state",
                    status=HealthStatus.OK,
                    message="backend port is not listening during planning",
                    evidence={"lane": lane_name, "backend_port": lane.backend_port},
                )
            )
        elif any(socket_inspector.is_public_bind_address(sock.local_address) for sock in matches):
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.backend_external_exposure",
                    status=HealthStatus.CRITICAL,
                    message="backend port is listening publicly",
                    evidence={"lane": lane_name, "matches": [sock.__dict__ for sock in matches]},
                    remediation="Backend ports must not be directly exposed publicly.",
                )
            )
        else:
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.backend_listener_state",
                    status=HealthStatus.WARN,
                    message="backend port is already listening during planning",
                    evidence={"lane": lane_name, "matches": [sock.__dict__ for sock in matches]},
                    remediation="Runtime listeners require an accepted activation task.",
                )
            )
    return checks


def _firewall_apply_mode_check(cfg: MPFConfig) -> HealthCheck:
    if cfg.firewall.apply_mode != "plan_only":
        return HealthCheck(
            key="firewall_apply_mode_plan_only",
            status=HealthStatus.CRITICAL,
            message="firewall apply mode is not plan_only",
            evidence={"apply_mode": cfg.firewall.apply_mode},
            remediation="Set firewall.apply_mode to plan_only before continuing Phase 4 planning.",
        )
    return HealthCheck(
        key="firewall_apply_mode_plan_only",
        status=HealthStatus.OK,
        message="firewall apply mode remains plan_only",
        evidence={"apply_mode": cfg.firewall.apply_mode},
    )
