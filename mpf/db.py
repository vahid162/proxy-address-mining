from __future__ import annotations

import csv
from dataclasses import dataclass
import io
import os
import subprocess
from urllib.parse import urlparse

from mpf.config import MPFConfig


@dataclass(frozen=True)
class DBPingResult:
    ok: bool
    message: str


@dataclass(frozen=True)
class DBQueryResult:
    ok: bool
    rows: list[dict[str, object]]
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


def _ensure_read_only_sql(sql: str) -> str | None:
    stripped = sql.lstrip().lower()
    if stripped.startswith(("select", "with")):
        return None
    return "phase 3 database helper accepts read-only SELECT/WITH queries only"


def _ping_local_peer_as_mpf(dbname: str) -> DBPingResult:
    cmd = ["sudo", "-u", "mpf", "psql", "-d", dbname, "-tAc", "select 1"]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "db ping failed"
        return DBPingResult(False, message)
    if result.stdout.strip() != "1":
        return DBPingResult(False, f"unexpected DB ping result: {result.stdout.strip()!r}")
    return DBPingResult(True, "OK")


def _query_local_peer_as_mpf(dbname: str, sql: str) -> DBQueryResult:
    cmd = ["sudo", "-u", "mpf", "psql", "-d", dbname, "--csv", "-X", "-q", "-c", sql]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "db query failed"
        return DBQueryResult(False, [], message)

    output = result.stdout.strip()
    if not output:
        return DBQueryResult(True, [], "OK")

    try:
        rows = list(csv.DictReader(io.StringIO(output)))
    except csv.Error as exc:
        return DBQueryResult(False, [], f"failed to parse psql CSV output: {exc}")
    return DBQueryResult(True, [dict(row) for row in rows], "OK")



def write_local_peer_root_guard_message(url: str, *, command_hint: str) -> str | None:
    """Return a safe operator instruction when root cannot write via local peer URL."""
    dbname = _local_peer_dbname(url)
    if dbname and os.geteuid() == 0:
        return f"local peer PostgreSQL write requires mpf OS user; run: sudo -u mpf {command_hint}"
    return None

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


def query_database(config: MPFConfig, sql: str) -> DBQueryResult:
    """Run a read-only SQL query for Phase 3 inspection commands.

    This helper intentionally accepts only SELECT/WITH queries. It exists for
    Phase 3 read-only inspection commands and must not be used for mutations.
    """
    error = _ensure_read_only_sql(sql)
    if error:
        return DBQueryResult(False, [], error)

    local_peer_dbname = _local_peer_dbname(config.database.url)
    if local_peer_dbname and os.geteuid() == 0:
        return _query_local_peer_as_mpf(local_peer_dbname, sql)

    try:
        import psycopg
    except ImportError as exc:
        return DBQueryResult(False, [], f"psycopg is not installed: {exc}")

    try:
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            conn.execute("set transaction read only")
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description is None:
                    return DBQueryResult(True, [], "OK")
                columns = [column.name for column in cur.description]
                rows = [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]
    except Exception as exc:  # noqa: BLE001 - CLI should return actionable diagnostics, not traceback by default.
        return DBQueryResult(False, [], str(exc))

    return DBQueryResult(True, rows, "OK")


def query_database_params(config: MPFConfig, sql: str, params: tuple[object, ...] = ()) -> DBQueryResult:
    """Run a parameterized read-only query for inspection/report commands."""
    error = _ensure_read_only_sql(sql)
    if error:
        return DBQueryResult(False, [], error)

    local_peer_dbname = _local_peer_dbname(config.database.url)
    if local_peer_dbname and os.geteuid() == 0:
        return DBQueryResult(False, [], "parameterized local-peer read queries are not supported in root fallback mode")

    try:
        import psycopg
    except ImportError as exc:
        return DBQueryResult(False, [], f"psycopg is not installed: {exc}")

    try:
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            conn.execute("set transaction read only")
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description is None:
                    return DBQueryResult(True, [], "OK")
                columns = [column.name for column in cur.description]
                rows = [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]
    except Exception as exc:  # noqa: BLE001
        return DBQueryResult(False, [], str(exc))

    return DBQueryResult(True, rows, "OK")
