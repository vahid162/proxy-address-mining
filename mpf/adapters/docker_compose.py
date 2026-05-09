from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any

import yaml


@dataclass(frozen=True)
class ComposeConfigResult:
    ok: bool
    message: str
    compose_file: Path


@dataclass(frozen=True)
class DockerContainerSummary:
    name: str
    image: str
    status: str
    ports: str


@dataclass(frozen=True)
class ComposePortBinding:
    service: str
    published: int | None
    target: int | None
    host_ip: str | None
    raw: object


@dataclass(frozen=True)
class ComposeInspection:
    ok: bool
    message: str
    services: list[str]
    port_bindings: list[ComposePortBinding]
    healthcheck_services: list[str]
    runtime_profiles: list[str]


def compose_file_exists(compose_file: Path) -> bool:
    return compose_file.exists() and compose_file.is_file()


def validate_compose_config(compose_file: Path, project_name: str) -> ComposeConfigResult:
    """Run Docker Compose config validation only.

    This function must not start, stop, create, or remove containers.
    """
    if not compose_file_exists(compose_file):
        return ComposeConfigResult(False, "compose file is missing", compose_file)

    cmd = [
        "docker",
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose_file),
        "config",
        "--quiet",
    ]
    try:
        result = subprocess.run(cmd, text=True, capture_output=True)
    except FileNotFoundError:
        return ComposeConfigResult(False, "docker command is not available", compose_file)

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "docker compose config failed"
        return ComposeConfigResult(False, message, compose_file)
    return ComposeConfigResult(True, "OK", compose_file)


def inspect_compose_file(compose_file: Path) -> ComposeInspection:
    """Inspect Compose YAML without invoking Docker or starting services."""
    if not compose_file_exists(compose_file):
        return ComposeInspection(False, "compose file is missing", [], [], [], [])

    try:
        data = yaml.safe_load(compose_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return ComposeInspection(False, f"compose file could not be parsed: {exc}", [], [], [], [])

    if not isinstance(data, dict):
        return ComposeInspection(False, "compose file must contain a YAML object", [], [], [], [])

    services_raw = data.get("services", {})
    if not isinstance(services_raw, dict):
        return ComposeInspection(False, "compose services section must be an object", [], [], [], [])

    services: list[str] = []
    port_bindings: list[ComposePortBinding] = []
    healthcheck_services: list[str] = []
    runtime_profiles: set[str] = set()

    for service_name, service_raw in services_raw.items():
        if not isinstance(service_name, str) or not isinstance(service_raw, dict):
            continue
        services.append(service_name)

        profiles = service_raw.get("profiles", [])
        if isinstance(profiles, list):
            runtime_profiles.update(str(profile) for profile in profiles)
        elif isinstance(profiles, str):
            runtime_profiles.add(profiles)

        if "healthcheck" in service_raw:
            healthcheck_services.append(service_name)

        ports = service_raw.get("ports", [])
        if not isinstance(ports, list):
            continue
        for raw_binding in ports:
            binding = _parse_port_binding(service_name, raw_binding)
            if binding:
                port_bindings.append(binding)

    return ComposeInspection(
        ok=True,
        message="OK",
        services=sorted(services),
        port_bindings=port_bindings,
        healthcheck_services=sorted(healthcheck_services),
        runtime_profiles=sorted(runtime_profiles),
    )


def has_public_bind_for_port(inspection: ComposeInspection, port: int) -> bool:
    for binding in inspection.port_bindings:
        if binding.published != port:
            continue
        if binding.host_ip in {None, "", "0.0.0.0", "::", "[::]", "*"}:
            return True
    return False


def has_local_bind_for_port(inspection: ComposeInspection, port: int) -> bool:
    for binding in inspection.port_bindings:
        if binding.published == port and binding.host_ip in {"127.0.0.1", "::1", "[::1]", "localhost"}:
            return True
    return False


def services_missing_healthchecks(inspection: ComposeInspection) -> list[str]:
    return sorted(set(inspection.services) - set(inspection.healthcheck_services))


def list_project_containers(project_name: str) -> list[DockerContainerSummary]:
    """Return Docker containers for the project using read-only docker ps."""
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
        return []

    if result.returncode != 0:
        return []

    containers: list[DockerContainerSummary] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        while len(parts) < 4:
            parts.append("")
        containers.append(
            DockerContainerSummary(
                name=parts[0],
                image=parts[1],
                status=parts[2],
                ports=parts[3],
            )
        )
    return containers


def _parse_port_binding(service: str, raw: object) -> ComposePortBinding | None:
    if isinstance(raw, int):
        return ComposePortBinding(service=service, published=raw, target=raw, host_ip=None, raw=raw)

    if isinstance(raw, str):
        return _parse_string_port_binding(service, raw)

    if isinstance(raw, dict):
        published = _parse_int(raw.get("published"))
        target = _parse_int(raw.get("target"))
        host_ip = raw.get("host_ip")
        if host_ip is not None:
            host_ip = str(host_ip)
        return ComposePortBinding(service=service, published=published, target=target, host_ip=host_ip, raw=raw)

    return None


def _parse_string_port_binding(service: str, raw: str) -> ComposePortBinding | None:
    value = raw.strip()
    if not value:
        return None

    # Compose short syntax examples:
    #   "127.0.0.1:60010:60010"
    #   "60010:60010"
    #   "60010"
    parts = value.rsplit(":", 2)
    if len(parts) == 3:
        host_ip, published_text, target_text = parts
        return ComposePortBinding(
            service=service,
            published=_parse_int(published_text),
            target=_parse_int(target_text),
            host_ip=host_ip.strip("[]"),
            raw=raw,
        )
    if len(parts) == 2:
        published_text, target_text = parts
        return ComposePortBinding(
            service=service,
            published=_parse_int(published_text),
            target=_parse_int(target_text),
            host_ip=None,
            raw=raw,
        )

    port = _parse_int(value)
    return ComposePortBinding(service=service, published=port, target=port, host_ip=None, raw=raw)


def _parse_int(value: Any) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None
