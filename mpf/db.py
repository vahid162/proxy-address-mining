from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from urllib.parse import urlparse

from mpf.config import MPFConfig


@dataclass(frozen=True)
class DBPingResult:
    ok: bool
    message: str


def _local_peer_dbname(url: str) -> str | None:
    """Return DB name for local peer URLs such as postgresql:///mpf.

    Phase 1 creates the PostgreSQL role/database `mpf` and relies on local peer
    auth. When the operator runs `sudo mpf db ping`, a direct psycopg connection
    would try the OS user `root` and fail because the role `root` does not
    exist. For this local-peer URL form, root should probe through the `mpf`
    system user, matching the Phase 1 smoke CLI behavior.
    """
    parsed = urlparse(url)
    if parsed.scheme != "postgresql":
        return None
    if parsed.netloc:
        return None
    dbname = parsed.path.lstrip("/")
    return dbname or None


def _ping_local_peer_as_mpf(dbname: str) -> DBPingResult:
    cmd = ["sudo", "-u", "mpf", "psql", "-d", dbname, "-tAc", "select 1"]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "db ping failed"
        return DBPingResult(False, message)
    if result.stdout.strip() != "1":
        return DBPingResult(False, f"unexpected DB ping result: {result.stdout.strip()!r}")
    return DBPingResult(True, "OK")


def ping_database(config: MPFConfig) -> DBPingResult:
    """Check PostgreSQL connectivity without creating schema or mutating state."""
    local_peer_dbname = _local_peer_dbname(config.database.url)
    if local_peer_dbname and os.geteuid() == 0:
        return _ping_local_peer_as_mpf(local_peer_dbname)

    try:
        import psycopg
    except ImportError as exc:
        return DBPingResult(False, f"psycopg is not installed: {exc}")

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
