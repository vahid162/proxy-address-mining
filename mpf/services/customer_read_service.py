from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.repositories import customer_repo
from mpf.repositories.customer_repo import CustomerRecord, CustomerShowRecord


@dataclass(frozen=True)
class CustomerList:
    ok: bool
    message: str
    customers: list[CustomerRecord]


@dataclass(frozen=True)
class CustomerShowResult:
    ok: bool
    message: str
    customer: CustomerShowRecord | None


@dataclass(frozen=True)
class NextPortResult:
    ok: bool
    message: str
    suggestion: object | None


@dataclass(frozen=True)
class CustomerLifecycleReportResult:
    ok: bool
    message: str
    rows: list[object]


def list_customer_status(
    config: MPFConfig,
    *,
    lane: str | None = None,
    status: str | None = None,
    include_deleted: bool = True,
    limit: int = 100,
) -> CustomerList:
    ok, records, message = customer_repo.list_customers(
        config,
        lane=lane,
        status=status,
        include_deleted=include_deleted,
        limit=limit,
    )
    return CustomerList(ok=ok, message=message, customers=records)


def show_customer(config: MPFConfig, *, customer_key: str | None = None, customer_id: int | None = None, port: int | None = None) -> CustomerShowResult:
    ok, rec, message = customer_repo.get_customer_show(config, customer_key=customer_key, customer_id=customer_id, port=port)
    return CustomerShowResult(ok=ok, message=message, customer=rec)


def suggest_next_customer_port(config: MPFConfig, *, lane: str, start: int = 20000, end: int = 59999) -> NextPortResult:
    if start < 1 or end > 65535 or start > end:
        return NextPortResult(ok=False, message="invalid range; expected 1 <= start <= end <= 65535", suggestion=None)
    ok, suggestion, message = customer_repo.suggest_next_port(config, lane=lane, start=start, end=end)
    return NextPortResult(ok=ok, message=message, suggestion=suggestion)


def report_expiring_customers(config: MPFConfig, *, within_days: int = 7, include_paused: bool = False, limit: int = 100) -> CustomerLifecycleReportResult:
    if within_days < 0 or within_days > 3650:
        return CustomerLifecycleReportResult(ok=False, message="within-days must be between 0 and 3650", rows=[])
    safe_limit = max(1, min(limit, 1000))
    ok, rows, message = customer_repo.list_expiring_customers(config, within_days=within_days, include_paused=include_paused, limit=safe_limit)
    return CustomerLifecycleReportResult(ok=ok, message=message, rows=rows)


def report_expired_customers(config: MPFConfig, *, include_deleted: bool = False, limit: int = 100) -> CustomerLifecycleReportResult:
    safe_limit = max(1, min(limit, 1000))
    ok, rows, message = customer_repo.list_expired_customers(config, include_deleted=include_deleted, limit=safe_limit)
    return CustomerLifecycleReportResult(ok=ok, message=message, rows=rows)


def report_delete_eligible_customers(config: MPFConfig, *, limit: int = 100) -> CustomerLifecycleReportResult:
    safe_limit = max(1, min(limit, 1000))
    ok, rows, message = customer_repo.list_delete_eligible_customers(config, limit=safe_limit)
    return CustomerLifecycleReportResult(ok=ok, message=message, rows=rows)
