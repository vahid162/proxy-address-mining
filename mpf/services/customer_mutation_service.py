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
from mpf.services.customer_dry_run_readiness_service import (
    dry_run_disable_customer,
    dry_run_update_customer,
)
from mpf.repositories.customer_write_repo import (
    CustomerMutationResult,
    create_customer,
    disable_customer,
    renew_customer,
    set_customer_ips,
    soft_delete_customer,
    update_customer,
    restore_phase11_exact_canary_db_visibility_customer as _restore_phase11_exact_canary_db_visibility_customer,
)


def create_db_only_customer(config: MPFConfig, req: CustomerCreateRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return create_customer(config, req, dry_run=dry_run)


def update_db_only_customer(config: MPFConfig, req: CustomerUpdateRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    if dry_run:
        return dry_run_update_customer(config, req)
    return update_customer(config, req, dry_run=False)


def renew_db_only_customer(config: MPFConfig, req: CustomerRenewRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return renew_customer(config, req, dry_run=dry_run)


def disable_db_only_customer(config: MPFConfig, req: CustomerDisableRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    if dry_run:
        return dry_run_disable_customer(config, req)
    return disable_customer(config, req, dry_run=False)


def soft_delete_db_only_customer(config: MPFConfig, req: CustomerDeleteRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return soft_delete_customer(config, req, dry_run=dry_run)


def set_ips_db_only_customer(config: MPFConfig, req: CustomerSetIpsRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    return set_customer_ips(config, req, dry_run=dry_run)


def restore_phase11_exact_canary_db_visibility_customer(config: MPFConfig, **kwargs) -> CustomerMutationResult:
    return _restore_phase11_exact_canary_db_visibility_customer(config, **kwargs)


def activate_phase11e_limited_customer(config: MPFConfig, **kwargs) -> CustomerMutationResult:
    """Exact-scope Phase 11E activation wrapper; intentionally not a generic customer activation API."""
    from mpf.repositories.customer_write_repo import activate_phase11e_limited_customer as _activate
    return _activate(config, **kwargs)


def rollback_phase11e_limited_customer(config: MPFConfig, **kwargs) -> CustomerMutationResult:
    """Exact-scope Phase 11E rollback wrapper; intentionally not a generic customer pause API."""
    from mpf.repositories.customer_write_repo import rollback_phase11e_limited_customer as _rollback
    return _rollback(config, **kwargs)
