from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.db import query_database


@dataclass(frozen=True)
class JobRunRecord:
    id: int
    job_name: str
    status: str
    started_at: str
    finished_at: str | None
    duration_ms: int | None


def list_recent_jobs(config: MPFConfig, limit: int = 20) -> tuple[bool, list[JobRunRecord], str]:
    """Return recent job rows without running jobs or activating timers."""
    safe_limit = max(1, min(limit, 100))
    sql = f"""
        select
            id,
            job_name,
            status,
            started_at::text as started_at,
            finished_at::text as finished_at,
            duration_ms
        from job_runs
        order by started_at desc, id desc
        limit {safe_limit}
    """
    result = query_database(config, sql)
    if not result.ok:
        return False, [], result.message

    records = [
        JobRunRecord(
            id=int(row["id"]),
            job_name=str(row["job_name"]),
            status=str(row["status"]),
            started_at=str(row["started_at"]),
            finished_at=str(row["finished_at"]) if row.get("finished_at") else None,
            duration_ms=int(row["duration_ms"]) if row.get("duration_ms") else None,
        )
        for row in result.rows
    ]
    return True, records, "OK"
