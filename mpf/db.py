from __future__ import annotations

from dataclasses import dataclass

import psycopg

from mpf.config import MPFConfig


@dataclass(frozen=True)
class DBPingResult:
    ok: bool
    message: str


def ping_database(config: MPFConfig) -> DBPingResult:
    """Check PostgreSQL connectivity without creating schema or mutating state."""
    try:
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("select 1")
                row = cur.fetchone()
    except Exception as exc:  # noqa: BLE001 - CLI should return actionable diagnostics, not traceback by default.
        return DBPingResult(False, str(exc))

    if row != (1,):
        return DBPingResult(False, f"unexpected DB ping result: {row!r}")
    return DBPingResult(True, "OK")
