"""Phase 11 backend-target normalization helpers."""
from __future__ import annotations

import ipaddress
from typing import Any

BACKEND_PORT = 60010


def canonical_expected_backend_target(backend_target: dict[str, Any] | None) -> dict[str, object]:
    blockers: list[str] = []
    if not isinstance(backend_target, dict):
        return {"expected_backend_target": None, "blockers": ["expected_backend_target_missing"], "status": "blocked"}
    raw_host = backend_target.get("resolved_ipv4") or backend_target.get("target_host")
    host = str(raw_host or "").strip()
    if not host:
        blockers.append("expected_backend_target_missing")
    port_raw = backend_target.get("target_port")
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = None
    if port != BACKEND_PORT:
        blockers.append("expected_backend_target_port_mismatch")
    if host:
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            blockers.append("expected_backend_target_invalid_ipv4")
        else:
            if not isinstance(ip, ipaddress.IPv4Address):
                blockers.append("expected_backend_target_invalid_ipv4")
            elif ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
                blockers.append("expected_backend_target_invalid_ipv4")
            elif not ip.is_private:
                blockers.append("expected_backend_target_public_forbidden")
    target = f"{host}:{port}" if host and port == BACKEND_PORT and not blockers else None
    return {"expected_backend_target": target, "blockers": sorted(set(blockers)), "status": "ok" if not blockers else "blocked"}
