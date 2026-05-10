from __future__ import annotations

from mpf.config import MPFConfig
from mpf.db import write_local_peer_root_guard_message
from mpf.repositories.lane_write_repo import LaneSyncResult, sync_lanes_from_config


def sync_lane_config_db_only(config: MPFConfig, *, dry_run: bool = True, yes: bool = False, command_hint: str = "/usr/local/bin/mpf lanes sync-config --yes") -> LaneSyncResult:
    if not dry_run and not yes:
        return LaneSyncResult(ok=False, message="refusing write without --yes")

    if not dry_run:
        guard = write_local_peer_root_guard_message(config.database.url, command_hint=command_hint)
        if guard:
            return LaneSyncResult(ok=False, message=guard)

    for lane_name, lane in config.lanes.items():
        if not lane_name.strip() or not lane.chain_prefix.strip() or lane.backend_port <= 0:
            return LaneSyncResult(ok=False, message=f"invalid lane config: {lane_name}")

    enabled_ports: dict[int, str] = {}
    if not dry_run:
        guard = write_local_peer_root_guard_message(config.database.url, command_hint=command_hint)
        if guard:
            return LaneSyncResult(ok=False, message=guard)

    for lane_name, lane in config.lanes.items():
        if not lane.enabled:
            continue
        if lane.backend_port in enabled_ports:
            return LaneSyncResult(
                ok=False,
                message=f"duplicate backend_port among enabled lanes: {lane.backend_port} ({enabled_ports[lane.backend_port]}, {lane_name})",
            )
        enabled_ports[lane.backend_port] = lane_name

    return sync_lanes_from_config(config, dry_run=dry_run)
