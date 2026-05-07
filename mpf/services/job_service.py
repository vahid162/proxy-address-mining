from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.repositories.job_repo import JobRunRecord, list_recent_jobs


@dataclass(frozen=True)
class JobStatusList:
    ok: bool
    message: str
    jobs: list[JobRunRecord]


def list_job_status(config: MPFConfig, limit: int = 20) -> JobStatusList:
    ok, records, message = list_recent_jobs(config, limit=limit)
    return JobStatusList(ok=ok, message=message, jobs=records)
