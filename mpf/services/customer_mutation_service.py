from __future__ import annotations

from mpf.config import MPFConfig
from mpf.domain.customers import (
    CustomerCreateRequest,
    CustomerDeleteRequest,
    CustomerDisableRequest,
    CustomerRenewRequest,
    CustomerSetIpsRequest,
    CustomerUpdateRequest,
)
from mpf.repositories.customer_write_repo import (
    CustomerMutationResult,
    create_customer,
    disable_customer,
    renew_customer,
    set_customer_ips,
    soft_delete_customer,
    update_customer,
)


def create_db_only_customer(config: MPFConfig, req: CustomerCreateRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return create_customer(config, req, dry_run=dry_run)


def update_db_only_customer(config: MPFConfig, req: CustomerUpdateRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return update_customer(config, req, dry_run=dry_run)


def renew_db_only_customer(config: MPFConfig, req: CustomerRenewRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return renew_customer(config, req, dry_run=dry_run)


def disable_db_only_customer(config: MPFConfig, req: CustomerDisableRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return disable_customer(config, req, dry_run=dry_run)


def soft_delete_db_only_customer(config: MPFConfig, req: CustomerDeleteRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return soft_delete_customer(config, req, dry_run=dry_run)


def set_ips_db_only_customer(config: MPFConfig, req: CustomerSetIpsRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return set_customer_ips(config, req, dry_run=dry_run)
