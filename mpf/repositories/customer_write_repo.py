from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from mpf.config import MPFConfig
from mpf.domain.customers import CustomerCreateRequest


@dataclass(frozen=True)
class CustomerCreateResult:
    ok: bool
    message: str
    customer_id: int | None = None
    customer_key: str | None = None
    firewall_change: str = "no"
    nat_change: str = "no"
    runtime_change: str = "no"
    would_create_customer: bool = False
    would_create_policy_version: bool = False
    would_create_event: bool = False
    would_create_audit: bool = False


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
                        return CustomerCreateResult(ok=False, message=f"unknown lane: {req.lane}")
                    lane_id, lane_enabled = int(lane_row[0]), bool(lane_row[1])
                    if not lane_enabled:
                        return CustomerCreateResult(ok=False, message=f"lane is disabled: {req.lane}")

                    cur.execute("select 1 from customers where port=%s", (req.port,))
                    if cur.fetchone() is not None:
                        return CustomerCreateResult(ok=False, message=f"duplicate port: {req.port}")

                    if req.customer_key is not None:
                        cur.execute("select 1 from customers where customer_key=%s", (req.customer_key,))
                        if cur.fetchone() is not None:
                            return CustomerCreateResult(ok=False, message=f"duplicate customer_key: {req.customer_key}")

                    if dry_run:
                        return CustomerCreateResult(
                            ok=True,
                            message="DRY_RUN_OK",
                            customer_key=req.customer_key,
                            would_create_customer=True,
                            would_create_policy_version=True,
                            would_create_event=True,
                            would_create_audit=True,
                        )

                    now = datetime.now(UTC)
                    starts_at, expires_at, activated_at = None, None, None
                    if req.lifecycle.activation_mode == "immediate" and req.lifecycle.service_days:
                        starts_at, expires_at = req.lifecycle.immediate_window(now) or (None, None)
                        activated_at = now

                    cur.execute(
                        """
                        insert into customers (
                            lane_id, name, port, status, starts_at, expires_at,
                            customer_key, activation_mode, service_days, activated_at, lifecycle_note
                        ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        returning id
                        """,
                        (
                            lane_id,
                            req.name,
                            req.port,
                            req.status,
                            starts_at,
                            expires_at,
                            req.customer_key,
                            req.lifecycle.activation_mode,
                            req.lifecycle.service_days,
                            activated_at,
                            req.lifecycle.lifecycle_note,
                        ),
                    )
                    customer_id = int(cur.fetchone()[0])

                    cur.execute(
                        """
                        insert into customer_policies
                        (customer_id, version, is_current, miners, farms, maxconn, rate_per_min, burst, ips_mode, reason)
                        values (%s,1,true,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            customer_id,
                            req.policy.miners,
                            req.policy.farms,
                            req.policy.maxconn,
                            req.policy.rate_per_min,
                            req.policy.burst,
                            req.policy.ips_mode,
                            req.policy.reason,
                        ),
                    )

                    if req.policy.ips_mode == "whitelist":
                        for cidr in req.policy.ip_whitelist:
                            cur.execute(
                                """
                                insert into customer_ip_pins (customer_id, ip_cidr, enabled, reason)
                                values (%s,%s,true,%s)
                                """,
                                (customer_id, cidr, req.policy.reason),
                            )

                    cur.execute(
                        """
                        insert into events (event_type, severity, subject_type, subject_id, message, data_json, created_by)
                        values (%s,%s,%s,%s,%s,%s::jsonb,%s)
                        """,
                        (
                            "customer.created",
                            "info",
                            "customer",
                            customer_id,
                            f"Customer created: {req.name}",
                            "{}",
                            None,
                        ),
                    )

                    cur.execute(
                        """
                        insert into audit_log (actor_type, actor_id, action, resource_type, resource_id, after_json, reason)
                        values (%s,%s,%s,%s,%s,%s::jsonb,%s)
                        """,
                        (
                            "system",
                            None,
                            "customer.create",
                            "customer",
                            customer_id,
                            "{}",
                            req.policy.reason,
                        ),
                    )
    except Exception as exc:  # noqa: BLE001
        return CustomerCreateResult(ok=False, message=str(exc), customer_key=req.customer_key)

    return CustomerCreateResult(ok=True, message="OK", customer_id=customer_id, customer_key=req.customer_key)
