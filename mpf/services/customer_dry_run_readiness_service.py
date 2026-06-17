from __future__ import annotations

from mpf.config import MPFConfig
from mpf.db import query_database_params
from mpf.domain.customers import CustomerDisableRequest, CustomerUpdateRequest
from mpf.repositories.customer_write_repo import CustomerMutationResult


def _is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _read_customer(config: MPFConfig, customer_key: str):
    result = query_database_params(
        config,
        """
        select c.id, c.customer_key, c.name, c.status, c.lane_id, c.activation_mode, c.service_days, c.deleted_at::text as deleted_at
        from customers c
        where c.customer_key=%s
        """,
        (customer_key,),
    )
    if not result.ok:
        return False, None, result.message
    if not result.rows:
        return True, None, "OK"
    return True, result.rows[0], "OK"


def _read_current_policy(config: MPFConfig, customer_id: int):
    result = query_database_params(
        config,
        """
        select id, version, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason
        from customer_policies
        where customer_id=%s and is_current=true
        """,
        (customer_id,),
    )
    if not result.ok:
        return False, None, result.message
    if not result.rows:
        return True, None, "OK"
    return True, result.rows[0], "OK"


def _read_lane(config: MPFConfig, lane: str):
    result = query_database_params(
        config,
        "select id, enabled from lanes where lower(name)=lower(%s)",
        (lane,),
    )
    if not result.ok:
        return False, None, result.message
    if not result.rows:
        return True, None, "OK"
    return True, result.rows[0], "OK"


def dry_run_update_customer(config: MPFConfig, req: CustomerUpdateRequest) -> CustomerMutationResult:
    req.validate()
    ok, row, message = _read_customer(config, req.customer_key)
    if not ok:
        return CustomerMutationResult(ok=False, message=message, customer_key=req.customer_key)
    if row is None:
        return CustomerMutationResult(ok=False, message="customer not found", customer_key=req.customer_key)

    customer_id = int(row["id"])
    status = str(row["status"])
    if row.get("deleted_at") or status == "deleted":
        return CustomerMutationResult(
            ok=False,
            message="deleted customer cannot be mutated",
            customer_id=customer_id,
            customer_key=req.customer_key,
        )
    if req.status == "deleted":
        return CustomerMutationResult(
            ok=False,
            message="use soft_delete_customer",
            customer_id=customer_id,
            customer_key=req.customer_key,
        )

    if req.policy is not None:
        ok, current_policy, message = _read_current_policy(config, customer_id)
        if not ok:
            return CustomerMutationResult(ok=False, message=message, customer_id=customer_id, customer_key=req.customer_key)
        if current_policy is None:
            return CustomerMutationResult(
                ok=False,
                message="current policy not found",
                customer_id=customer_id,
                customer_key=req.customer_key,
            )
        current_ips_mode = str(current_policy["ips_mode"])
        if req.policy.ips_mode != current_ips_mode or req.policy.ip_whitelist:
            return CustomerMutationResult(
                ok=False,
                message="use set_customer_ips",
                customer_id=customer_id,
                customer_key=req.customer_key,
            )

    if req.lane is not None:
        ok, lane_row, message = _read_lane(config, req.lane)
        if not ok:
            return CustomerMutationResult(ok=False, message=message, customer_id=customer_id, customer_key=req.customer_key)
        if lane_row is None:
            return CustomerMutationResult(
                ok=False,
                message=f"unknown lane: {req.lane}",
                customer_id=customer_id,
                customer_key=req.customer_key,
            )
        if not _is_truthy(lane_row["enabled"]):
            return CustomerMutationResult(
                ok=False,
                message=f"lane is disabled: {req.lane}",
                customer_id=customer_id,
                customer_key=req.customer_key,
            )

    return CustomerMutationResult(
        ok=True,
        message="DRY_RUN_OK",
        customer_id=customer_id,
        customer_key=req.customer_key,
        would_mutate_customer=True,
        would_create_policy_version=req.policy is not None,
        would_create_event=True,
        would_create_audit=True,
    )


def dry_run_disable_customer(config: MPFConfig, req: CustomerDisableRequest) -> CustomerMutationResult:
    req.validate()
    ok, row, message = _read_customer(config, req.customer_key)
    if not ok:
        return CustomerMutationResult(ok=False, message=message, customer_key=req.customer_key)
    if row is None:
        return CustomerMutationResult(ok=False, message="customer not found", customer_key=req.customer_key)

    customer_id = int(row["id"])
    status = str(row["status"])
    if row.get("deleted_at") or status == "deleted":
        return CustomerMutationResult(
            ok=False,
            message="deleted customer cannot be mutated",
            customer_id=customer_id,
            customer_key=req.customer_key,
        )

    return CustomerMutationResult(
        ok=True,
        message="DRY_RUN_OK",
        customer_id=customer_id,
        customer_key=req.customer_key,
        would_mutate_customer=True,
        would_create_event=True,
        would_create_audit=True,
    )
