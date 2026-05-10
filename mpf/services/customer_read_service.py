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


def list_customer_status(config: MPFConfig, limit: int = 100) -> CustomerList:
    ok, records, message = customer_repo.list_customers(config, limit=limit)
    return CustomerList(ok=ok, message=message, customers=records)


def show_customer(config: MPFConfig, *, customer_key: str | None = None, customer_id: int | None = None, port: int | None = None) -> CustomerShowResult:
    ok, rec, message = customer_repo.get_customer_show(config, customer_key=customer_key, customer_id=customer_id, port=port)
    return CustomerShowResult(ok=ok, message=message, customer=rec)
