from __future__ import annotations

from pathlib import Path
from typing import Any

from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.services import customer_read_service, db_service, job_service, lane_service


def get_db_status(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Return DB status for a future local-only API route.

    Phase 3 exposes only function-level API foundation. It does not bind a
    network listener and does not define mutation endpoints.
    """
    result = db_service.status(load_config(config_path))
    return result.__dict__


def list_lanes(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    result = lane_service.list_lane_status(load_config(config_path))
    return {
        "ok": result.ok,
        "message": result.message,
        "lanes": [lane.__dict__ for lane in result.lanes],
    }


def list_customers(config_path: Path = DEFAULT_CONFIG_PATH, limit: int = 100) -> dict[str, Any]:
    result = customer_read_service.list_customer_status(load_config(config_path), limit=limit)
    return {
        "ok": result.ok,
        "message": result.message,
        "customers": [customer.__dict__ for customer in result.customers],
    }


def list_jobs(config_path: Path = DEFAULT_CONFIG_PATH, limit: int = 20) -> dict[str, Any]:
    result = job_service.list_job_status(load_config(config_path), limit=limit)
    return {
        "ok": result.ok,
        "message": result.message,
        "jobs": [job.__dict__ for job in result.jobs],
    }
