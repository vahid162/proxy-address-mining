from __future__ import annotations

from pathlib import Path
import yaml

from mpf.adapters import docker_compose, socket_inspector
from mpf.config import DEFAULT_CONFIG_PATH, MPFConfig, load_config
from mpf.domain.health import HealthCheck, HealthReport, HealthStatus, worst_status

EXPECTED_RUNTIME_CONTAINERS = {"mpf-v2raya", "mpf-forwarder-btc"}


def run(config_path: Path = DEFAULT_CONFIG_PATH) -> HealthReport:
    """Run proxy doctor checks without mutating runtime state."""
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
        *_compose_template_contract_checks(cfg),
        _firewall_apply_mode_check(cfg),
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
        *_compose_template_contract_checks(cfg),
        _v2raya_bind_check(cfg),
        *_lane_forwarder_config_checks(cfg),
        _container_state_check(cfg),
        *_listening_socket_checks(cfg),
        _no_customer_nat_redirects_check(),
        _firewall_apply_mode_check(cfg),
    ]


def _runtime_activation_check(cfg: MPFConfig) -> HealthCheck:
    if cfg.proxy.runtime_activation_allowed:
        return HealthCheck(
            key="proxy.runtime_activation_allowed",
            status=HealthStatus.CRITICAL,
            message="proxy runtime activation is enabled through general app/config state",
            evidence={"runtime_activation_allowed": True},
            remediation="Keep proxy.runtime_activation_allowed=false; Phase 4 runtime is limited to the guarded operator Compose path.",
        )
    return HealthCheck(
        key="proxy.runtime_activation_allowed",
        status=HealthStatus.OK,
        message="proxy runtime activation remains disabled for general app/API mutation",
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


def _compose_template_contract_checks(cfg: MPFConfig) -> list[HealthCheck]:
    inspection = docker_compose.inspect_compose_file(cfg.proxy.compose_file)
    if not inspection.ok:
        return [
            HealthCheck(
                key="compose_template_contract",
                status=HealthStatus.WARN,
                message=inspection.message,
                evidence={"compose_file": str(cfg.proxy.compose_file)},
                remediation="Add a parseable Compose template before runtime activation.",
            )
        ]

    checks: list[HealthCheck] = []

    if "phase4-runtime" not in inspection.runtime_profiles:
        checks.append(
            HealthCheck(
                key="compose_runtime_profile_guard",
                status=HealthStatus.CRITICAL,
                message="proxy services are not guarded by the phase4-runtime profile",
                evidence={"runtime_profiles": inspection.runtime_profiles},
                remediation="Keep Phase 4 runtime services behind an explicit runtime profile.",
            )
        )
    else:
        checks.append(
            HealthCheck(
                key="compose_runtime_profile_guard",
                status=HealthStatus.OK,
                message="proxy services require an explicit phase4-runtime profile",
                evidence={"runtime_profiles": inspection.runtime_profiles},
            )
        )

    if docker_compose.has_public_bind_for_port(inspection, cfg.v2raya.ui_port):
        checks.append(
            HealthCheck(
                key="backend_docker_publish_mode.v2raya_ui",
                status=HealthStatus.CRITICAL,
                message="Compose template publishes v2rayA UI on a public bind",
                evidence={"ui_port": cfg.v2raya.ui_port},
                remediation="Publish v2rayA UI only on 127.0.0.1.",
            )
        )
    elif docker_compose.has_local_bind_for_port(inspection, cfg.v2raya.ui_port):
        checks.append(
            HealthCheck(
                key="backend_docker_publish_mode.v2raya_ui",
                status=HealthStatus.OK,
                message="Compose template publishes v2rayA UI local-only",
                evidence={"ui_port": cfg.v2raya.ui_port},
            )
        )
    else:
        checks.append(
            HealthCheck(
                key="backend_docker_publish_mode.v2raya_ui",
                status=HealthStatus.WARN,
                message="Compose template does not publish the configured v2rayA UI port",
                evidence={"ui_port": cfg.v2raya.ui_port},
                remediation="Runtime activation must document how the local-only UI is reached.",
            )
        )

    for lane_name, lane in sorted(cfg.lanes.items()):
        if not lane.enabled:
            continue
        key = f"backend_docker_publish_mode.{lane_name}"
        if docker_compose.has_public_bind_for_port(inspection, lane.backend_port):
            checks.append(
                HealthCheck(
                    key=key,
                    status=HealthStatus.CRITICAL,
                    message="Compose template publishes a backend port publicly",
                    evidence={"lane": lane_name, "backend_port": lane.backend_port},
                    remediation="Backend ports must be local/internal only, never 0.0.0.0.",
                )
            )
        elif docker_compose.has_local_bind_for_port(inspection, lane.backend_port):
            checks.append(
                HealthCheck(
                    key=key,
                    status=HealthStatus.OK,
                    message="Compose template publishes backend port local-only",
                    evidence={"lane": lane_name, "backend_port": lane.backend_port},
                )
            )
        else:
            checks.append(
                HealthCheck(
                    key=key,
                    status=HealthStatus.WARN,
                    message="Compose template does not publish the configured backend port",
                    evidence={"lane": lane_name, "backend_port": lane.backend_port},
                    remediation="Runtime activation must document the internal backend reachability path.",
                )
            )


    # Internal SOCKS bridge model: forwarder must use v2raya:22070 (bridge),
    # not direct v2raya:20170 (loopback-only inside v2rayA container).
    for lane_name, lane in sorted(cfg.lanes.items()):
        if not lane.enabled or lane.forwarder is None or not lane.forwarder.upstream_socks:
            continue
        expected = lane.forwarder.upstream_socks
        if expected.endswith(":20170"):
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.forwarder_upstream_socks",
                    status=HealthStatus.CRITICAL,
                    message="lane forwarder upstream_socks points to direct v2rayA loopback SOCKS endpoint",
                    evidence={"lane": lane_name, "upstream_socks": expected},
                    remediation="Use bridge endpoint v2raya:22070 so forwarder can reach SOCKS through sidecar bridge.",
                )
            )
        elif expected.endswith(":22070"):
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.forwarder_upstream_socks",
                    status=HealthStatus.OK,
                    message="lane forwarder upstream_socks uses bridge endpoint",
                    evidence={"lane": lane_name, "upstream_socks": expected},
                )
            )
        else:
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.forwarder_upstream_socks",
                    status=HealthStatus.WARN,
                    message="lane forwarder upstream_socks does not match approved bridge endpoint",
                    evidence={"lane": lane_name, "upstream_socks": expected},
                    remediation="Use v2raya:22070 unless a reviewed alternative bridge endpoint is accepted.",
                )
            )

    if docker_compose.has_public_bind_for_port(inspection, 22070):
        checks.append(
            HealthCheck(
                key="backend_docker_publish_mode.v2raya_socks",
                status=HealthStatus.CRITICAL,
                message="Compose template publishes v2rayA SOCKS bridge port publicly",
                evidence={"socks_port": 22070},
                remediation="Keep SOCKS internal-only in Docker network (no host port publish).",
            )
        )
    elif docker_compose.has_local_bind_for_port(inspection, 22070):
        checks.append(
            HealthCheck(
                key="backend_docker_publish_mode.v2raya_socks",
                status=HealthStatus.WARN,
                message="Compose template publishes v2rayA SOCKS bridge on host loopback; prefer internal-only expose",
                evidence={"socks_port": 22070},
                remediation="Prefer Docker-network-only exposure for SOCKS upstream.",
            )
        )
    else:
        checks.append(
            HealthCheck(
                key="backend_docker_publish_mode.v2raya_socks",
                status=HealthStatus.OK,
                message="Compose template keeps v2rayA SOCKS internal-only",
                evidence={"socks_port": 22070},
            )
        )

    checks.extend(_socks_bridge_contract_checks(cfg.proxy.compose_file))

    missing_healthchecks = docker_compose.services_missing_healthchecks(inspection)
    if missing_healthchecks:
        checks.append(
            HealthCheck(
                key="healthcheck_state",
                status=HealthStatus.WARN,
                message="some Compose services do not define healthchecks",
                evidence={"missing_healthchecks": missing_healthchecks},
                remediation="Add healthchecks or document why a service cannot be healthchecked.",
            )
        )
    else:
        checks.append(
            HealthCheck(
                key="healthcheck_state",
                status=HealthStatus.OK,
                message="Compose template defines healthchecks for all services",
                evidence={"services": inspection.services},
            )
        )

    return checks


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


def _socks_bridge_contract_checks(compose_file: Path) -> list[HealthCheck]:
    try:
        data = yaml.safe_load(compose_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [
            HealthCheck(
                key="v2raya_socks_bridge_contract",
                status=HealthStatus.WARN,
                message="compose file parse failed for socks bridge contract checks",
                evidence={"compose_file": str(compose_file), "error": str(exc)},
            )
        ]

    services = (data or {}).get("services", {}) if isinstance(data, dict) else {}
    bridge = services.get("mpf-v2raya-socks-bridge") if isinstance(services, dict) else None
    if not isinstance(bridge, dict):
        return [
            HealthCheck(
                key="v2raya_socks_bridge_service",
                status=HealthStatus.CRITICAL,
                message="socks bridge service is missing in compose template",
                evidence={"service": "mpf-v2raya-socks-bridge"},
                remediation="Add internal socks bridge sidecar for v2rayA loopback SOCKS.",
            )
        ]

    checks: list[HealthCheck] = []
    network_mode = str(bridge.get("network_mode", ""))
    checks.append(
        HealthCheck(
            key="v2raya_socks_bridge_network_mode",
            status=HealthStatus.OK if network_mode == "service:mpf-v2raya" else HealthStatus.CRITICAL,
            message="socks bridge network_mode is valid" if network_mode == "service:mpf-v2raya" else "socks bridge must share v2rayA network namespace",
            evidence={"network_mode": network_mode},
            remediation="Set network_mode to service:mpf-v2raya." if network_mode != "service:mpf-v2raya" else None,
        )
    )

    command_text = " ".join(str(x) for x in bridge.get("command", [])) if isinstance(bridge.get("command"), list) else str(bridge.get("command", ""))
    expected = "-L=tcp://:22070/127.0.0.1:20170"
    checks.append(
        HealthCheck(
            key="v2raya_socks_bridge_command",
            status=HealthStatus.OK if expected in command_text else HealthStatus.CRITICAL,
            message="socks bridge command routes 22070 to loopback 20170" if expected in command_text else "socks bridge command does not route to v2rayA loopback SOCKS",
            evidence={"command": command_text},
            remediation=f"Use command argument {expected}." if expected not in command_text else None,
        )
    )

    if "ports" in bridge and bridge.get("ports"):
        checks.append(
            HealthCheck(
                key="v2raya_socks_bridge_host_publish",
                status=HealthStatus.CRITICAL,
                message="socks bridge must not publish host ports",
                evidence={"ports": bridge.get("ports")},
                remediation="Remove ports from mpf-v2raya-socks-bridge.",
            )
        )
    else:
        checks.append(
            HealthCheck(
                key="v2raya_socks_bridge_host_publish",
                status=HealthStatus.OK,
                message="socks bridge has no host port publish",
                evidence={"ports": bridge.get("ports", [])},
            )
        )

    return checks


def _container_state_check(cfg: MPFConfig) -> HealthCheck:
    containers = docker_compose.list_project_containers(cfg.proxy.project_name)
    container_names = {container.name for container in containers}
    if not containers:
        return HealthCheck(
            key="proxy_container_state",
            status=HealthStatus.WARN,
            message="accepted limited proxy runtime containers are not present",
            evidence={"project_name": cfg.proxy.project_name, "containers": []},
            remediation="The accepted Phase 4 runtime should be running before Phase 5 server validation.",
        )

    missing = sorted(EXPECTED_RUNTIME_CONTAINERS - container_names)
    if missing:
        return HealthCheck(
            key="proxy_container_state",
            status=HealthStatus.CRITICAL,
            message="accepted limited proxy runtime is missing required containers",
            evidence={"missing": missing, "containers": [container.__dict__ for container in containers]},
            remediation="Restart the guarded Phase 4 runtime or stop and review evidence.",
        )

    unhealthy = [container for container in containers if "unhealthy" in container.status.lower()]
    not_running = [container for container in containers if not container.status.lower().startswith("up")]
    if unhealthy or not_running:
        return HealthCheck(
            key="proxy_container_state",
            status=HealthStatus.CRITICAL,
            message="accepted limited proxy runtime containers are not healthy/running",
            evidence={
                "unhealthy": [container.__dict__ for container in unhealthy],
                "not_running": [container.__dict__ for container in not_running],
                "containers": [container.__dict__ for container in containers],
            },
            remediation="Inspect Docker logs and restart only through the guarded Phase 4 runtime script.",
        )

    return HealthCheck(
        key="proxy_container_state",
        status=HealthStatus.OK,
        message="accepted limited proxy runtime containers are present and running",
        evidence={"project_name": cfg.proxy.project_name, "containers": [container.__dict__ for container in containers]},
    )


def _listening_socket_checks(cfg: MPFConfig) -> list[HealthCheck]:
    sockets = socket_inspector.list_listening_tcp_sockets()
    checks: list[HealthCheck] = []

    ui_matches = [sock for sock in sockets if sock.port == cfg.v2raya.ui_port]
    if not ui_matches:
        checks.append(
            HealthCheck(
                key="v2raya_ui_listener_state",
                status=HealthStatus.WARN,
                message="accepted v2rayA UI runtime listener is not present",
                evidence={"ui_port": cfg.v2raya.ui_port},
                remediation="Verify the accepted Phase 4 runtime is running through the guarded script.",
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
                status=HealthStatus.OK,
                message="accepted v2rayA UI runtime listener is local-only",
                evidence={"matches": [sock.__dict__ for sock in ui_matches]},
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
                    status=HealthStatus.WARN,
                    message="accepted backend runtime listener is not present",
                    evidence={"lane": lane_name, "backend_port": lane.backend_port},
                    remediation="Verify the accepted Phase 4 runtime is running through the guarded script.",
                )
            )
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.backend_internal_reachability",
                    status=HealthStatus.WARN,
                    message="backend internal reachability cannot be confirmed because listener is absent",
                    evidence={"lane": lane_name, "backend_port": lane.backend_port},
                    remediation="Start/review the guarded limited runtime before Phase 5 server validation.",
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
                    status=HealthStatus.OK,
                    message="accepted backend runtime listener is local-only",
                    evidence={"lane": lane_name, "matches": [sock.__dict__ for sock in matches]},
                )
            )
            checks.append(
                HealthCheck(
                    key=f"lane.{lane_name}.backend_internal_reachability",
                    status=HealthStatus.OK,
                    message="backend internal reachability is accepted through local-only runtime listener",
                    evidence={"lane": lane_name, "matches": [sock.__dict__ for sock in matches]},
                )
            )
    return checks


def _no_customer_nat_redirects_check() -> HealthCheck:
    return HealthCheck(
        key="no_customer_nat_redirects",
        status=HealthStatus.OK,
        message="accepted Phase 4 runtime does not create MPF customer NAT redirects",
        evidence={"nat_redirects_created_by_mpf": False},
    )


def _firewall_apply_mode_check(cfg: MPFConfig) -> HealthCheck:
    if cfg.firewall.apply_mode != "plan_only":
        return HealthCheck(
            key="firewall_apply_mode_plan_only",
            status=HealthStatus.CRITICAL,
            message="firewall apply mode is not plan_only",
            evidence={"apply_mode": cfg.firewall.apply_mode},
            remediation="Set firewall.apply_mode to plan_only before continuing Phase 5 DB-only customer work.",
        )
    return HealthCheck(
        key="firewall_apply_mode_plan_only",
        status=HealthStatus.OK,
        message="firewall apply mode remains plan_only",
        evidence={"apply_mode": cfg.firewall.apply_mode},
    )
