from __future__ import annotations

from mpf.config import MPFConfig
from mpf.domain.customers import CustomerCreateRequest
from mpf.repositories.customer_write_repo import CustomerCreateResult, create_customer


def create_db_only_customer(config: MPFConfig, req: CustomerCreateRequest, *, dry_run: bool = False) -> CustomerCreateResult:
    req.validate()
    return create_customer(config, req, dry_run=dry_run)
