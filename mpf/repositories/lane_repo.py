from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.db import query_database


@dataclass(frozen=True)
class LaneRecord:
    name: str
    enabled: bool
    backend_port: int
    chain_prefix: str
    protocol: str
    source: str


def list_lanes(config: MPFConfig) -> tuple[bool, list[LaneRecord], str]:
    """Return lane rows without mutating database or traffic state."""
    sql = """
        select name, enabled, backend_port, chain_prefix, protocol
        from lanes
        order by name
    """
    result = query_database(config, sql)
    if not result.ok:
        return False, [], result.message

    records = [
        LaneRecord(
            name=str(row["name"]),
            enabled=str(row["enabled"]).lower() in {"true", "t", "1"},
            backend_port=int(row["backend_port"]),
            chain_prefix=str(row["chain_prefix"]),
            protocol=str(row.get("protocol") or "stratum"),
            source="db",
        )
        for row in result.rows
    ]

    if records:
        return True, records, "OK"

    config_records = [
        LaneRecord(
            name=name,
            enabled=lane.enabled,
            backend_port=lane.backend_port,
            chain_prefix=lane.chain_prefix,
            protocol="stratum",
            source="config",
        )
        for name, lane in sorted(config.lanes.items())
    ]
    return True, config_records, "OK: no DB lanes found; showing config lanes"
