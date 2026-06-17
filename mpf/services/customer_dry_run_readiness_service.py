from __future__ import annotations

from mpf.config import MPFConfig
from mpf.db import query_database_params
from mpf.domain.customers import CustomerDisableRequest, CustomerUpdateRequest
from mpf.repositories.customer_write_repo import CustomerMutationResult


_CUSTOMER_SELECT = """
select c.id, c.customer_key, c.status, c.deleted_at
from customers c
where c.customer_key=%s
"""

_POLICY_SELECT = """
select id, version, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason
from customer_policies
where customer_id=%s and is_current=true
"""

_LANE_SELECT = """
select id, enabled
from lanes
where lower(name)=lower(%s)
"""


def _load_customer(config: MPFConfig, customer_key: str) -> tuple[CustomerMutationResult | None, dict[str, object] | None]:
    result = query_database_params(config, _CUSTOMER_SELECT, (customer_key,))
    if not result.ok:
        return CustomerMutationResult(ok=False, message=result.message, customer_key=customer_key), None
    if not result.rows:
        return CustomerMutationResult(ok=False, message="customer not found", customer_key=customer_key), None
    row = result.rows[0]
    if row.get("deleted_at") is not None or row.get("status") == "deleted":
        return CustomerMutationResult(ok=False, message="deleted customer cannot be mutated", customer_key=customer_key), None
    return None, row


def dry_run_disable_customer(config: MPFConfig, req: CustomerDisableRequest) -> CustomerMutationResult:
    """Resolve customer disable dry-run using read-only query helpers only."""
    req.validate()
    failure, customer = _load_customer(config, req.customer_key)
    if failure is not None:
        return failure
    assert customer is not None
    return CustomerMutationResult(
        ok=True,
        message="DRY_RUN_OK",
        customer_id=int(customer["id"]),
        customer_key=str(customer["customer_key"]),
        would_mutate_customer=True,
        would_create_event=True,
        would_create_audit=True,
        firewall_change="no",
        nat_change="no",
        runtime_change="no",
    )


def dry_run_update_customer(config: MPFConfig, req: CustomerUpdateRequest) -> CustomerMutationResult:
    """Resolve customer update dry-run using read-only query helpers only."""
    req.validate()
    failure, customer = _load_customer(config, req.customer_key)
    if failure is not None:
        return failure
    assert customer is not None
    customer_id = int(customer["id"])

    if req.status == "deleted":
        return CustomerMutationResult(ok=False, message="use soft_delete_customer", customer_key=req.customer_key)

    wants_policy = req.policy is not None
    if req.policy is not None:
        policy_result = query_database_params(config, _POLICY_SELECT, (customer_id,))
        if not policy_result.ok:
            return CustomerMutationResult(ok=False, message=policy_result.message, customer_key=req.customer_key)
        if not policy_result.rows:
            return CustomerMutationResult(ok=False, message="current policy not found", customer_key=req.customer_key)
        current_policy = policy_result.rows[0]
        if req.policy.ips_mode != str(current_policy.get("ips_mode")) or req.policy.ip_whitelist:
            return CustomerMutationResult(ok=False, message="use set_customer_ips", customer_key=req.customer_key)

    if req.lane is not None:
        lane_result = query_database_params(config, _LANE_SELECT, (req.lane,))
        if not lane_result.ok:
            return CustomerMutationResult(ok=False, message=lane_result.message, customer_key=req.customer_key)
        if not lane_result.rows:
            return CustomerMutationResult(ok=False, message=f"unknown lane: {req.lane}", customer_key=req.customer_key)
        lane = lane_result.rows[0]
        if not bool(lane.get("enabled")):
            return CustomerMutationResult(ok=False, message=f"lane is disabled: {req.lane}", customer_key=req.customer_key)

    return CustomerMutationResult(
        ok=True,
        message="DRY_RUN_OK",
        customer_id=customer_id,
        customer_key=str(customer["customer_key"]),
        would_mutate_customer=True,
        would_create_policy_version=wants_policy,
        would_create_event=True,
        would_create_audit=True,
        firewall_change="no",
        nat_change="no",
        runtime_change="no",
    )
