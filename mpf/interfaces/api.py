from __future__ import annotations

from pathlib import Path
from typing import Any

from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.domain.dto import ReadOnlyResponse
from mpf.domain.taxonomy import RequestContext
from mpf.services import customer_read_service, db_service, job_service, lane_service


def _response(ok: bool, message: str, context: RequestContext | None, data: dict[str, Any]) -> dict[str, Any]:
    request_context = context or RequestContext(source_interface="internal_api")
    return ReadOnlyResponse(
        ok=ok,
        message=message,
        correlation_id=request_context.correlation_id,
        data=data,
    ).to_dict()


def get_db_status(
    config_path: Path = DEFAULT_CONFIG_PATH,
    context: RequestContext | None = None,
) -> dict[str, Any]:
    """Return DB status for a future local-only API route.

    Phase 3 exposes only function-level API foundation. It does not bind a
    network listener and does not define mutation endpoints.
    """
    result = db_service.status(load_config(config_path))
    return _response(
        ok=result.ok,
        message=result.message,
        context=context,
        data={
            "alembic_version": result.alembic_version,
            "public_table_count": result.public_table_count,
            "lanes": result.lanes,
            "customers": result.customers,
            "job_runs": result.job_runs,
            "firewall_applies": result.firewall_applies,
            "abuse_states": result.abuse_states,
        },
    )


def list_lanes(
    config_path: Path = DEFAULT_CONFIG_PATH,
    context: RequestContext | None = None,
) -> dict[str, Any]:
    result = lane_service.list_lane_status(load_config(config_path))
    return _response(
        ok=result.ok,
        message=result.message,
        context=context,
        data={"lanes": result.lanes},
    )


def list_customers(
    config_path: Path = DEFAULT_CONFIG_PATH,
    limit: int = 100,
    context: RequestContext | None = None,
) -> dict[str, Any]:
    result = customer_read_service.list_customer_status(load_config(config_path), limit=limit)
    return _response(
        ok=result.ok,
        message=result.message,
        context=context,
        data={"customers": result.customers},
    )


def list_jobs(
    config_path: Path = DEFAULT_CONFIG_PATH,
    limit: int = 20,
    context: RequestContext | None = None,
) -> dict[str, Any]:
    result = job_service.list_job_status(load_config(config_path), limit=limit)
    return _response(
        ok=result.ok,
        message=result.message,
        context=context,
        data={"jobs": result.jobs},
    )
