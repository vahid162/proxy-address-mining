"""Strict argv-only read-only command adapter for Phase 11 packet-path evidence."""
from __future__ import annotations

import hashlib
import ipaddress
import os
import selectors
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
_SAFE_PATH = "/usr/sbin:/usr/bin:/sbin:/bin"

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
    stdout_observed_size: int | None = None
    stderr_observed_size: int | None = None
    stdout: str | None = None
    stderr: str | None = None

    def metadata(self) -> dict[str, object]:
        data = asdict(self)
        if self.redacted:
            data.pop("stdout", None)
            data.pop("stderr", None)
        return data


def _validate_backend_ipv4(value: str) -> str:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValueError("backend_ipv4_invalid") from exc
    if not isinstance(ip, ipaddress.IPv4Address):
        raise ValueError("backend_ipv4_not_ipv4")
    if ip.is_loopback:
        raise ValueError("backend_ipv4_loopback_forbidden")
    if ip.is_link_local:
        raise ValueError("backend_ipv4_link_local_forbidden")
    if ip.is_multicast:
        raise ValueError("backend_ipv4_multicast_forbidden")
    if ip.is_unspecified:
        raise ValueError("backend_ipv4_unspecified_forbidden")
    if not ip.is_private:
        raise ValueError("backend_ipv4_public_forbidden")
    if str(ip) == "172.18.0.3":
        raise ValueError("backend_ipv4_historical_forbidden")
    return str(ip)


def allowed_argv(command_id: str, *, backend_ipv4: str | None = None) -> list[str]:
    if command_id == "ip_route_get_backend":
        if backend_ipv4 is None:
            raise ValueError("backend_ipv4_required")
        return ["ip", "-json", "route", "get", _validate_backend_ipv4(backend_ipv4)]
    if command_id not in _FIXED:
        raise ValueError(f"command_not_allowlisted:{command_id}")
    return list(_FIXED[command_id])


def all_static_allowed_argv() -> dict[str, list[str]]:
    return {key: list(value) for key, value in sorted(_FIXED.items())}


class Phase11ReadOnlyCommandAdapter:
    def __init__(self, *, run_func: Callable[..., subprocess.CompletedProcess[bytes]] | None = None, timeout: float = _TIMEOUT) -> None:
        self._run = run_func
        self.timeout = timeout
        self.env = {"PATH": _SAFE_PATH, "LC_ALL": "C", "LANG": "C"}

    def run(self, command_id: str, *, backend_ipv4: str | None = None, redact_stdout: bool = False, require_non_empty: bool = False) -> ReadOnlyCommandResult:
        try:
            argv = allowed_argv(command_id, backend_ipv4=backend_ipv4)
        except ValueError as exc:
            return _synthetic_result(command_id, [], 126, str(exc))
        limit = _MAX[command_id]
        started = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        start = time.monotonic()
        stdout = b""
        stderr = b""
        stdout_seen = 0
        stderr_seen = 0
        rc = 127
        timed_out = False
        truncated = False
        try:
            if self._run is not None:
                completed = self._run(argv, shell=False, check=False, capture_output=True, timeout=self.timeout, env=self.env, cwd="/")
                stdout = completed.stdout or b""
                stderr = completed.stderr or b""
                stdout_seen = len(stdout)
                stderr_seen = len(stderr)
                rc = int(completed.returncode)
                if len(stdout) > limit or len(stderr) > limit:
                    truncated = True
                    stdout = stdout[:limit]
                    stderr = stderr[:limit]
            else:
                proc = subprocess.Popen(argv, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env, cwd="/")
                stdout, stderr, stdout_seen, stderr_seen, truncated, timed_out = _bounded_communicate(proc, limit, self.timeout)
                rc = proc.returncode if proc.returncode is not None else 124
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            stdout_seen = len(stdout)
            stderr_seen = len(stderr)
            rc = 124
            timed_out = True
        except FileNotFoundError as exc:
            stderr = str(exc).encode()
            stderr_seen = len(stderr)
            rc = 127
        if require_non_empty and not stdout.strip() and rc == 0:
            rc = 65
            stderr = (stderr + b"\nempty_required_output").strip()
            stderr_seen = len(stderr)
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
            stdout_observed_size=stdout_seen,
            stderr_observed_size=stderr_seen,
            stdout_sha256=hashlib.sha256(stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr).hexdigest(),
            output_truncated=truncated,
            redacted=redact_stdout,
            sanitized_projection_ref=("sanitized-backend-target.json" if command_id == "docker_inspect_backend" else "sanitized-docker-network.json" if command_id == "docker_network_inspect" else None),
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=None if redact_stdout else stderr.decode("utf-8", errors="replace"),
        )


def _bounded_communicate(proc: subprocess.Popen[bytes], limit: int, timeout: float) -> tuple[bytes, bytes, int, int, bool, bool]:
    sel = selectors.DefaultSelector()
    assert proc.stdout is not None and proc.stderr is not None
    sel.register(proc.stdout, selectors.EVENT_READ, "stdout")
    sel.register(proc.stderr, selectors.EVENT_READ, "stderr")
    bufs = {"stdout": bytearray(), "stderr": bytearray()}
    seen = {"stdout": 0, "stderr": 0}
    truncated = False
    timed_out = False
    deadline = time.monotonic() + timeout
    while sel.get_map():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            proc.kill()
            break
        for key, _ in sel.select(timeout=min(0.1, remaining)):
            chunk = key.fileobj.read1(65536) if hasattr(key.fileobj, "read1") else key.fileobj.read(65536)
            name = key.data
            if not chunk:
                sel.unregister(key.fileobj)
                continue
            seen[name] += len(chunk)
            if len(bufs[name]) + len(chunk) > limit:
                keep = max(0, limit - len(bufs[name]))
                bufs[name].extend(chunk[:keep])
                truncated = True
                proc.kill()
                break
            bufs[name].extend(chunk)
        if truncated:
            break
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait(timeout=1)
    return bytes(bufs["stdout"]), bytes(bufs["stderr"]), seen["stdout"], seen["stderr"], truncated, timed_out


def _synthetic_result(command_id: str, argv: list[str], rc: int, stderr: str) -> ReadOnlyCommandResult:
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    err = stderr.encode()
    return ReadOnlyCommandResult(command_id, argv, now, now, 0, rc, False, 0, len(err), hashlib.sha256(b"").hexdigest(), hashlib.sha256(err).hexdigest(), False, stderr=stderr, stderr_observed_size=len(err), stdout_observed_size=0)
