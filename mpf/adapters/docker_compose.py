from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


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
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "docker compose config failed"
        return ComposeConfigResult(False, message, compose_file)
    return ComposeConfigResult(True, "OK", compose_file)


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
    result = subprocess.run(cmd, text=True, capture_output=True)
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
