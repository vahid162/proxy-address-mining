from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.db import ping_database, query_database


@dataclass(frozen=True)
class DatabaseStatus:
    ok: bool
    message: str
    alembic_version: str | None = None
    public_table_count: int | None = None
    lanes: int | None = None
    customers: int | None = None
    job_runs: int | None = None
    firewall_applies: int | None = None
    abuse_states: int | None = None


def ping(config: MPFConfig) -> tuple[bool, str]:
    result = ping_database(config)
    return result.ok, result.message


def status(config: MPFConfig) -> DatabaseStatus:
    ping_result = ping_database(config)
    if not ping_result.ok:
        return DatabaseStatus(ok=False, message=ping_result.message)

    sql = """
        select
            (select version_num from alembic_version limit 1) as alembic_version,
            (
                select count(*)
                from information_schema.tables
                where table_schema = 'public'
                  and table_type = 'BASE TABLE'
            ) as public_table_count,
            (select count(*) from lanes) as lanes,
            (select count(*) from customers) as customers,
            (select count(*) from job_runs) as job_runs,
            (select count(*) from firewall_applies) as firewall_applies,
            (select count(*) from abuse_states) as abuse_states
    """
    query_result = query_database(config, sql)
    if not query_result.ok:
        return DatabaseStatus(ok=False, message=query_result.message)
    if not query_result.rows:
        return DatabaseStatus(ok=False, message="database status query returned no rows")

    row = query_result.rows[0]
    return DatabaseStatus(
        ok=True,
        message="OK",
        alembic_version=str(row["alembic_version"]) if row.get("alembic_version") else None,
        public_table_count=int(row["public_table_count"]),
        lanes=int(row["lanes"]),
        customers=int(row["customers"]),
        job_runs=int(row["job_runs"]),
        firewall_applies=int(row["firewall_applies"]),
        abuse_states=int(row["abuse_states"]),
    )
