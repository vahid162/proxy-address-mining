from __future__ import annotations

from dataclasses import dataclass
import subprocess


@dataclass(frozen=True)
class ListeningSocket:
    local_address: str
    port: int
    process: str | None = None


def is_public_bind_address(address: str) -> bool:
    return address in {"0.0.0.0", "::", "*", "[::]"}


def is_local_bind_address(address: str) -> bool:
    return address in {"127.0.0.1", "::1", "localhost", "[::1]"}


def list_listening_tcp_sockets() -> list[ListeningSocket]:
    """Inspect listening TCP sockets using ss.

    This function is read-only and must not alter sockets or services.
    """
    try:
        result = subprocess.run(["ss", "-lntp"], text=True, capture_output=True)
    except FileNotFoundError:
        return []

    if result.returncode != 0:
        return []

    sockets: list[ListeningSocket] = []
    for line in result.stdout.splitlines():
        if not line.startswith("LISTEN"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        local = parts[3]
        address, port = _split_local_address(local)
        if port is None:
            continue
        process = parts[-1] if len(parts) >= 7 else None
        sockets.append(ListeningSocket(local_address=address, port=port, process=process))
    return sockets


def _split_local_address(local: str) -> tuple[str, int | None]:
    if local.startswith("[") and "]:" in local:
        address, port_text = local.rsplit(":", 1)
        return address, _parse_port(port_text)
    if ":" not in local:
        return local, None
    address, port_text = local.rsplit(":", 1)
    return address, _parse_port(port_text)


def _parse_port(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
