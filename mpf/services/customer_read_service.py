from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.repositories.customer_repo import CustomerRecord, list_customers


@dataclass(frozen=True)
class CustomerList:
    ok: bool
    message: str
    customers: list[CustomerRecord]


def list_customer_status(config: MPFConfig, limit: int = 100) -> CustomerList:
    ok, records, message = list_customers(config, limit=limit)
    return CustomerList(ok=ok, message=message, customers=records)
