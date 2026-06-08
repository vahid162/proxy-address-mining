"""Strict argv-only read-only command adapter for Phase 11 packet-path evidence."""
from __future__ import annotations

import hashlib
import os
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Callable

_MAX = {
    "iptables_save": 4_000_000,
    "ip6tables_save": 4_000_000,
    "docker_inspect_backend": 1_500_000,
    "docker_network_inspect": 1_500_000,
    "docker_ps_compose": 500_000,
    "ip_address": 1_000_000,
    "ip_link": 1_000_000,
    "ip_route_all": 1_000_000,
    "ip_rule": 500_000,
    "ip_route_get_backend": 100_000,
    "bridge_link": 1_000_000,
    "ss_listeners": 1_000_000,
    "ss_backend_listener": 100_000,
    "iptables_version": 50_000,
    "ip6tables_version": 50_000,
    "uname_kernel": 50_000,
    "hostname": 50_000,
}
_TIMEOUT = 8.0

_FIXED: dict[str, tuple[str, ...]] = {
    "iptables_save": ("iptables-save",),
    "ip6tables_save": ("ip6tables-save",),
    "iptables_version": ("iptables", "--version"),
    "ip6tables_version": ("ip6tables", "--version"),
    "docker_inspect_backend": ("docker", "inspect", "mpf-forwarder-btc"),
    "docker_network_inspect": ("docker", "network", "inspect", "mpf-proxy-internal"),
    "docker_ps_compose": ("docker", "ps", "-a", "--filter", "label=com.docker.compose.project=mpf-proxy", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"),
    "ip_address": ("ip", "-json", "address", "show"),
    "ip_link": ("ip", "-json", "link", "show"),
    "ip_route_all": ("ip", "-json", "route", "show", "table", "all"),
    "ip_rule": ("ip", "-json", "rule", "show"),
    "bridge_link": ("bridge", "-json", "link", "show"),
    "ss_listeners": ("ss", "-H", "-ltn"),
    "ss_backend_listener": ("ss", "-ltn", "sport", "=", ":60010"),
    "uname_kernel": ("uname", "-r"),
    "hostname": ("hostname",),
}

@dataclass(frozen=True)
class ReadOnlyCommandResult:
    command_id: str
    argv: list[str]
    started_at: str
    finished_at: str
    duration_ms: int
    return_code: int
    timed_out: bool
    stdout_size: int
    stderr_size: int
    stdout_sha256: str
    stderr_sha256: str
    output_truncated: bool
    mutation_performed: bool = False
    redacted: bool = False
    sanitized_projection_ref: str | None = None
    stdout: str | None = None
    stderr: str | None = None

    def metadata(self) -> dict[str, object]:
        data = asdict(self)
        if self.redacted:
            data.pop("stdout", None)
            data.pop("stderr", None)
        return data


def allowed_argv(command_id: str, *, backend_ipv4: str | None = None) -> list[str]:
    if command_id == "ip_route_get_backend":
        if backend_ipv4 is None:
            raise ValueError("backend_ipv4_required")
        return ["ip", "-json", "route", "get", backend_ipv4]
    if command_id not in _FIXED:
        raise ValueError(f"command_not_allowlisted:{command_id}")
    return list(_FIXED[command_id])


def all_static_allowed_argv() -> dict[str, list[str]]:
    return {key: list(value) for key, value in sorted(_FIXED.items())}


class Phase11ReadOnlyCommandAdapter:
    def __init__(self, *, run_func: Callable[..., subprocess.CompletedProcess[bytes]] | None = None, timeout: float = _TIMEOUT) -> None:
        self._run = run_func or subprocess.run
        self.timeout = timeout
        self.env = {"PATH": os.environ.get("PATH", "/usr/sbin:/usr/bin:/sbin:/bin"), "LC_ALL": "C", "LANG": "C"}

    def run(self, command_id: str, *, backend_ipv4: str | None = None, redact_stdout: bool = False, require_non_empty: bool = False) -> ReadOnlyCommandResult:
        argv = allowed_argv(command_id, backend_ipv4=backend_ipv4)
        limit = _MAX[command_id]
        started = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        start = time.monotonic()
        stdout = b""
        stderr = b""
        rc = 127
        timed_out = False
        truncated = False
        try:
            completed = self._run(argv, shell=False, check=False, capture_output=True, timeout=self.timeout, env=self.env, cwd="/")
            stdout = completed.stdout or b""
            stderr = completed.stderr or b""
            rc = int(completed.returncode)
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            rc = 124
            timed_out = True
        except FileNotFoundError as exc:
            stderr = str(exc).encode()
            rc = 127
        if len(stdout) > limit or len(stderr) > limit:
            truncated = True
            stdout = stdout[:limit]
            stderr = stderr[:limit]
        if require_non_empty and not stdout.strip() and rc == 0:
            rc = 65
            stderr = (stderr + b"\nempty_required_output").strip()
        finished = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        duration = int((time.monotonic() - start) * 1000)
        return ReadOnlyCommandResult(
            command_id=command_id,
            argv=argv,
            started_at=started,
            finished_at=finished,
            duration_ms=duration,
            return_code=rc,
            timed_out=timed_out,
            stdout_size=len(stdout),
            stderr_size=len(stderr),
            stdout_sha256=hashlib.sha256(stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr).hexdigest(),
            output_truncated=truncated,
            redacted=redact_stdout,
            sanitized_projection_ref=("sanitized-backend-target.json" if command_id == "docker_inspect_backend" else "sanitized-docker-network.json" if command_id == "docker_network_inspect" else None),
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=None if redact_stdout else stderr.decode("utf-8", errors="replace"),
        )
