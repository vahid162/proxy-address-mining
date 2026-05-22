from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mpf.config import MPFConfig
from mpf.domain.customers import (
    CustomerCreateRequest,
    CustomerDeleteRequest,
    CustomerDisableRequest,
    CustomerRenewRequest,
    CustomerSetIpsRequest,
    CustomerUpdateRequest,
)


@dataclass(frozen=True)
class CustomerMutationResult:
    ok: bool
    message: str
    customer_id: int | None = None
    customer_key: str | None = None
    firewall_change: str = "no"
    nat_change: str = "no"
    runtime_change: str = "no"
    would_create_customer: bool = False
    would_mutate_customer: bool = False
    would_create_policy_version: bool = False
    would_mutate_ip_pins: bool = False
    would_create_event: bool = False
    would_create_audit: bool = False


CustomerCreateResult = CustomerMutationResult


def _load_customer(cur, customer_key: str):
    cur.execute(
        """
        select c.id, c.customer_key, c.name, c.status, c.lane_id, c.activation_mode, c.service_days, c.deleted_at
        from customers c
        where c.customer_key=%s
        """,
        (customer_key,),
    )
    return cur.fetchone()


def _load_current_policy(cur, customer_id: int):
    cur.execute(
        """
        select id, version, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason
        from customer_policies
        where customer_id=%s and is_current=true
        """,
        (customer_id,),
    )
    return cur.fetchone()


def _insert_event_audit(cur, *, customer_id: int, event_type: str, message: str, action: str, reason: str | None = None) -> None:
    cur.execute(
        """
        insert into events (event_type, severity, subject_type, subject_id, message, data_json, created_by)
        values (%s,%s,%s,%s,%s,%s::jsonb,%s)
        """,
        (event_type, "info", "customer", customer_id, message, "{}", None),
    )
    cur.execute(
        """
        insert into audit_log (actor_type, actor_id, action, resource_type, resource_id, after_json, reason)
        values (%s,%s,%s,%s,%s,%s::jsonb,%s)
        """,
        ("system", None, action, "customer", customer_id, "{}", reason),
    )


def create_customer(config: MPFConfig, req: CustomerCreateRequest, *, dry_run: bool = False) -> CustomerCreateResult:
    req.validate()
    try:
        import psycopg
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("select id, enabled from lanes where lower(name)=lower(%s)", (req.lane,))
                    lane_row = cur.fetchone()
                    if lane_row is None:
                        return CustomerMutationResult(ok=False, message=f"unknown lane: {req.lane}")
                    lane_id, lane_enabled = int(lane_row[0]), bool(lane_row[1])
                    if not lane_enabled:
                        return CustomerMutationResult(ok=False, message=f"lane is disabled: {req.lane}")

                    cur.execute("select 1 from customers where port=%s", (req.port,))
                    if cur.fetchone() is not None:
                        return CustomerMutationResult(ok=False, message=f"duplicate port: {req.port}")

                    if req.customer_key is not None:
                        cur.execute("select 1 from customers where customer_key=%s", (req.customer_key,))
                        if cur.fetchone() is not None:
                            return CustomerMutationResult(ok=False, message=f"duplicate customer_key: {req.customer_key}")

                    if dry_run:
                        return CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_key=req.customer_key, would_create_customer=True, would_mutate_customer=True, would_create_policy_version=True, would_mutate_ip_pins=req.policy.ips_mode == "whitelist", would_create_event=True, would_create_audit=True)

                    now = datetime.now(UTC)
                    starts_at, expires_at, activated_at = None, None, None
                    if req.lifecycle.activation_mode == "immediate" and req.lifecycle.service_days:
                        starts_at, expires_at = req.lifecycle.immediate_window(now) or (None, None)
                        activated_at = now
                    cur.execute("""
                        insert into customers (
                            lane_id, name, port, status, starts_at, expires_at,
                            customer_key, activation_mode, service_days, activated_at, lifecycle_note
                        ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        returning id
                    """, (lane_id, req.name, req.port, req.status, starts_at, expires_at, req.customer_key, req.lifecycle.activation_mode, req.lifecycle.service_days, activated_at, req.lifecycle.lifecycle_note))
                    customer_id = int(cur.fetchone()[0])
                    cur.execute("""insert into customer_policies
                        (customer_id, version, is_current, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason)
                        values (%s,1,true,%s,%s,%s,%s,%s,%s,%s)""", (customer_id, req.policy.miners, req.policy.farms, req.policy.maxconn, req.policy.rate_per_min, req.policy.burst, req.policy.ips_mode, req.policy.reason))
                    if req.policy.ips_mode == "whitelist":
                        for cidr in req.policy.ip_whitelist:
                            cur.execute("insert into customer_ip_pins (customer_id, ip_cidr, enabled, reason) values (%s,%s,true,%s)", (customer_id, cidr, req.policy.reason))
                    _insert_event_audit(cur, customer_id=customer_id, event_type="customer.created", message=f"Customer created: {req.name}", action="customer.create", reason=req.policy.reason)
    except Exception as exc:  # noqa: BLE001
        return CustomerMutationResult(ok=False, message=str(exc), customer_key=req.customer_key)
    return CustomerMutationResult(ok=True, message="OK", customer_id=customer_id, customer_key=req.customer_key)


def update_customer(config: MPFConfig, req: CustomerUpdateRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    try:
        import psycopg
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    row = _load_customer(cur, req.customer_key)
                    if row is None:
                        return CustomerMutationResult(ok=False, message="customer not found", customer_key=req.customer_key)
                    customer_id, _, name, status, lane_id, activation_mode, service_days, deleted_at = row
                    if deleted_at is not None or status == "deleted":
                        return CustomerMutationResult(ok=False, message="deleted customer cannot be mutated", customer_key=req.customer_key)
                    if req.status == "deleted":
                        return CustomerMutationResult(ok=False, message="use soft_delete_customer", customer_key=req.customer_key)
                    current_policy = None
                    if req.policy is not None:
                        current_policy = _load_current_policy(cur, int(customer_id))
                        if current_policy is None:
                            return CustomerMutationResult(ok=False, message="current policy not found", customer_key=req.customer_key)
                        current_ips_mode = str(current_policy[7])
                        if req.policy.ips_mode != current_ips_mode or req.policy.ip_whitelist:
                            return CustomerMutationResult(ok=False, message="use set_customer_ips", customer_key=req.customer_key)
                    new_lane_id = lane_id
                    if req.lane is not None:
                        cur.execute("select id, enabled from lanes where lower(name)=lower(%s)", (req.lane,))
                        lane_row = cur.fetchone()
                        if lane_row is None:
                            return CustomerMutationResult(ok=False, message=f"unknown lane: {req.lane}", customer_key=req.customer_key)
                        if not bool(lane_row[1]):
                            return CustomerMutationResult(ok=False, message=f"lane is disabled: {req.lane}", customer_key=req.customer_key)
                        new_lane_id = int(lane_row[0])
                    wants_policy = req.policy is not None
                    if dry_run:
                        return CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_id=int(customer_id), customer_key=req.customer_key, would_mutate_customer=True, would_create_policy_version=wants_policy, would_create_event=True, would_create_audit=True)

                    cur.execute("update customers set lane_id=%s, name=coalesce(%s,name), status=coalesce(%s,status), activation_mode=coalesce(%s,activation_mode), service_days=coalesce(%s,service_days), lifecycle_note=coalesce(%s,lifecycle_note), updated_at=now() where id=%s", (new_lane_id, req.name, req.status, req.lifecycle.activation_mode if req.lifecycle else None, req.lifecycle.service_days if req.lifecycle else None, req.lifecycle.lifecycle_note if req.lifecycle else None, customer_id))
                    if wants_policy:
                        _, version, *_ = current_policy
                        cur.execute("update customer_policies set is_current=false where customer_id=%s and is_current=true", (customer_id,))
                        cur.execute("""insert into customer_policies (customer_id, version, is_current, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason)
                            values (%s,%s,true,%s,%s,%s,%s,%s,%s,%s)""", (customer_id, int(version) + 1, req.policy.miners, req.policy.farms, req.policy.maxconn, req.policy.rate_per_min, req.policy.burst, req.policy.ips_mode, req.policy.reason))
                    _insert_event_audit(cur, customer_id=int(customer_id), event_type="customer.updated", message=f"Customer updated: {name}", action="customer.update", reason=(req.policy.reason if req.policy else None))
    except Exception as exc:  # noqa: BLE001
        return CustomerMutationResult(ok=False, message=str(exc), customer_key=req.customer_key)
    return CustomerMutationResult(ok=True, message="OK", customer_id=int(customer_id), customer_key=req.customer_key)


def renew_customer(config: MPFConfig, req: CustomerRenewRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    try:
        import psycopg
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    row = _load_customer(cur, req.customer_key)
                    if row is None:
                        return CustomerMutationResult(ok=False, message="customer not found", customer_key=req.customer_key)
                    customer_id, _, name, status, _, activation_mode, _, deleted_at = row
                    if deleted_at is not None or status == "deleted":
                        return CustomerMutationResult(ok=False, message="deleted customer cannot be mutated", customer_key=req.customer_key)
                    if dry_run:
                        return CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_id=int(customer_id), customer_key=req.customer_key, would_mutate_customer=True, would_create_event=True, would_create_audit=True)
                    now = datetime.now(UTC)
                    if activation_mode == "immediate":
                        starts_at = now
                        expires_at = now + timedelta(days=req.service_days)
                        cur.execute("update customers set starts_at=%s, activated_at=%s, expires_at=%s, service_days=%s, lifecycle_note=coalesce(%s,lifecycle_note), updated_at=now() where id=%s", (starts_at, now, expires_at, req.service_days, req.lifecycle_note, customer_id))
                    else:
                        cur.execute("update customers set service_days=%s, lifecycle_note=coalesce(%s,lifecycle_note), updated_at=now() where id=%s", (req.service_days, req.lifecycle_note, customer_id))
                    _insert_event_audit(cur, customer_id=int(customer_id), event_type="customer.renewed", message=f"Customer renewed: {name}", action="customer.renew", reason=req.lifecycle_note)
    except Exception as exc:  # noqa: BLE001
        return CustomerMutationResult(ok=False, message=str(exc), customer_key=req.customer_key)
    return CustomerMutationResult(ok=True, message="OK", customer_id=int(customer_id), customer_key=req.customer_key)


def disable_customer(config: MPFConfig, req: CustomerDisableRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    try:
        import psycopg
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    row = _load_customer(cur, req.customer_key)
                    if row is None:
                        return CustomerMutationResult(ok=False, message="customer not found", customer_key=req.customer_key)
                    customer_id, _, name, status, *_rest, deleted_at = row
                    if deleted_at is not None or status == "deleted":
                        return CustomerMutationResult(ok=False, message="deleted customer cannot be mutated", customer_key=req.customer_key)
                    if dry_run:
                        return CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_id=int(customer_id), customer_key=req.customer_key, would_mutate_customer=True, would_create_event=True, would_create_audit=True)
                    cur.execute("update customers set status='paused', updated_at=now() where id=%s", (customer_id,))
                    _insert_event_audit(cur, customer_id=int(customer_id), event_type="customer.disabled", message=f"Customer paused: {name}", action="customer.disable", reason=req.reason)
    except Exception as exc:  # noqa: BLE001
        return CustomerMutationResult(ok=False, message=str(exc), customer_key=req.customer_key)
    return CustomerMutationResult(ok=True, message="OK", customer_id=int(customer_id), customer_key=req.customer_key)


def soft_delete_customer(config: MPFConfig, req: CustomerDeleteRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    try:
        import psycopg
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    row = _load_customer(cur, req.customer_key)
                    if row is None:
                        return CustomerMutationResult(ok=False, message="customer not found", customer_key=req.customer_key)
                    customer_id, _, name, status, *_rest, deleted_at = row
                    if deleted_at is not None or status == "deleted":
                        return CustomerMutationResult(ok=False, message="deleted customer cannot be mutated", customer_key=req.customer_key)
                    if dry_run:
                        return CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_id=int(customer_id), customer_key=req.customer_key, would_mutate_customer=True, would_create_event=True, would_create_audit=True)
                    cur.execute("update customers set status='deleted', deleted_at=now(), updated_at=now() where id=%s", (customer_id,))
                    _insert_event_audit(cur, customer_id=int(customer_id), event_type="customer.deleted", message=f"Customer soft-deleted: {name}", action="customer.soft_delete", reason=req.reason)
    except Exception as exc:  # noqa: BLE001
        return CustomerMutationResult(ok=False, message=str(exc), customer_key=req.customer_key)
    return CustomerMutationResult(ok=True, message="OK", customer_id=int(customer_id), customer_key=req.customer_key)


def set_customer_ips(config: MPFConfig, req: CustomerSetIpsRequest, *, dry_run: bool = False) -> CustomerMutationResult:
    req.validate()
    try:
        import psycopg
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    row = _load_customer(cur, req.customer_key)
                    if row is None:
                        return CustomerMutationResult(ok=False, message="customer not found", customer_key=req.customer_key)
                    customer_id, _, name, status, *_rest, deleted_at = row
                    if deleted_at is not None or status == "deleted":
                        return CustomerMutationResult(ok=False, message="deleted customer cannot be mutated", customer_key=req.customer_key)
                    current = _load_current_policy(cur, int(customer_id))
                    if current is None:
                        return CustomerMutationResult(ok=False, message="current policy not found", customer_key=req.customer_key)
                    policy_id, version, miners, farms, maxconn, rate_per_min, burst, _, reason = current
                    if dry_run:
                        return CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_id=int(customer_id), customer_key=req.customer_key, would_create_policy_version=True, would_mutate_ip_pins=True, would_create_event=True, would_create_audit=True)
                    cur.execute("update customer_policies set is_current=false where id=%s", (policy_id,))
                    cur.execute("insert into customer_policies (customer_id, version, is_current, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason) values (%s,%s,true,%s,%s,%s,%s,%s,%s,%s)", (customer_id, int(version) + 1, miners, farms, maxconn, rate_per_min, burst, req.ips_mode, reason))
                    cur.execute("update customer_ip_pins set enabled=false where customer_id=%s", (customer_id,))
                    if req.ips_mode == "whitelist":
                        for cidr in req.ip_whitelist:
                            cur.execute("insert into customer_ip_pins (customer_id, ip_cidr, enabled, reason) values (%s,%s,true,%s)", (customer_id, cidr, reason))
                    _insert_event_audit(cur, customer_id=int(customer_id), event_type="customer.ips_set", message=f"Customer IP mode updated: {name}", action="customer.set_ips", reason=reason)
    except Exception as exc:  # noqa: BLE001
        return CustomerMutationResult(ok=False, message=str(exc), customer_key=req.customer_key)
    return CustomerMutationResult(ok=True, message="OK", customer_id=int(customer_id), customer_key=req.customer_key)


def restore_phase11_exact_canary_db_visibility_customer(config: MPFConfig, *, customer_key: str, lane: str, port: int, name: str, miners: int, farms: int, maxconn: int, rate_per_min: int, burst: int, ips_mode: str, reason: str | None = None, dry_run: bool = False) -> CustomerMutationResult:
    if customer_key != "canary-btc-001" or lane != "btc" or port != 20001:
        return CustomerMutationResult(ok=False, message="restore scope must be exact Phase 11 canary")
    try:
        import psycopg
        with psycopg.connect(config.database.url, connect_timeout=5) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("""
                        select c.id, c.status, c.deleted_at, c.name
                        from customers c
                        left join lanes l on l.id = c.lane_id
                        where c.customer_key=%s and lower(coalesce(l.name,''))=lower(%s) and c.port=%s
                        order by c.id desc
                        limit 1
                    """, (customer_key, lane, port))
                    row = cur.fetchone()
                    if row is None:
                        return CustomerMutationResult(ok=False, message="exact deleted canary row not found", customer_key=customer_key)
                    customer_id, status, deleted_at, old_name = int(row[0]), str(row[1]), row[2], str(row[3])
                    if deleted_at is None and status != "deleted":
                        return CustomerMutationResult(ok=False, message="target row is not deleted", customer_key=customer_key)
                    if dry_run:
                        return CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_id=customer_id, customer_key=customer_key, would_mutate_customer=True, would_create_policy_version=True, would_create_event=True, would_create_audit=True)
                    cur.execute("update customers set status='active', deleted_at=null, name=%s, updated_at=now() where id=%s", (name, customer_id))
                    cur.execute("update customer_policies set is_current=false where customer_id=%s and is_current=true", (customer_id,))
                    cur.execute("select coalesce(max(version),0) from customer_policies where customer_id=%s", (customer_id,))
                    next_version = int(cur.fetchone()[0]) + 1
                    cur.execute("""insert into customer_policies
                        (customer_id, version, is_current, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason)
                        values (%s,%s,true,%s,%s,%s,%s,%s,%s,%s)""", (customer_id, next_version, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason))
                    _insert_event_audit(cur, customer_id=customer_id, event_type="customer.restored", message=f"Phase11 exact canary restored: {old_name}", action="customer.phase11_canary_restore", reason=reason)
    except Exception as exc:  # noqa: BLE001
        return CustomerMutationResult(ok=False, message=str(exc), customer_key=customer_key)
    return CustomerMutationResult(ok=True, message="OK", customer_id=customer_id, customer_key=customer_key)
