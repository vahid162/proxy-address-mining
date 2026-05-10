from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.db import query_database, query_database_params

ALLOWED_STATUSES = {"active", "paused", "expired", "deleted"}


@dataclass(frozen=True)
class CustomerRecord:
    id: int
    customer_key: str | None
    lane: str
    name: str
    port: int
    status: str
    activation_mode: str | None
    expires_at: str | None
    deleted_at: str | None


@dataclass(frozen=True)
class CustomerShowRecord:
    id: int
    customer_key: str | None
    lane: str
    name: str
    port: int
    status: str
    activation_mode: str | None
    service_days: int | None
    activated_at: str | None
    starts_at: str | None
    expires_at: str | None
    first_connected_at: str | None
    expired_at: str | None
    delete_eligible_at: str | None
    deleted_at: str | None
    auto_expire_enabled: bool
    auto_delete_enabled: bool
    lifecycle_note: str | None
    miners: int | None
    farms: int | None
    maxconn: int | None
    rate_per_min: int | None
    burst: int | None
    ips_mode: str | None
    abuse_exempt: bool | None
    abuse_exempt_reason: str | None
    abuse_exempt_until: str | None
    abuse_exempt_by: str | None
    enabled_ip_pins: list[str]


def list_customers(
    config: MPFConfig,
    *,
    lane: str | None = None,
    status: str | None = None,
    include_deleted: bool = True,
    limit: int = 100,
) -> tuple[bool, list[CustomerRecord], str]:
    safe_limit = max(1, min(limit, 1000))
    clauses: list[str] = []
    params: list[object] = []
    if lane:
        clauses.append("coalesce(lanes.name, 'unknown') = %s")
        params.append(lane)
    if status:
        if status not in ALLOWED_STATUSES:
            return False, [], "invalid status filter"
        clauses.append("customers.status = %s")
        params.append(status)
    elif not include_deleted:
        clauses.append("customers.status <> 'deleted'")

    where_sql = f" where {' and '.join(clauses)}" if clauses else ""
    sql = f"""
        select
            customers.id,
            customers.customer_key,
            coalesce(lanes.name, 'unknown') as lane,
            customers.name,
            customers.port,
            customers.status,
            customers.activation_mode,
            customers.expires_at::text as expires_at,
            customers.deleted_at::text as deleted_at
        from customers
        left join lanes on lanes.id = customers.lane_id
        {where_sql}
        order by customers.port
        limit %s
    """
    params.append(safe_limit)
    result = query_database_params(config, sql, tuple(params))
    if not result.ok:
        return False, [], result.message
    records = [
        CustomerRecord(
            id=int(row["id"]),
            customer_key=row.get("customer_key"),
            lane=str(row["lane"]),
            name=str(row["name"]),
            port=int(row["port"]),
            status=str(row["status"]),
            activation_mode=row.get("activation_mode"),
            expires_at=str(row["expires_at"]) if row.get("expires_at") else None,
            deleted_at=str(row["deleted_at"]) if row.get("deleted_at") else None,
        )
        for row in result.rows
    ]
    return True, records, "OK"


def _base_customer_select() -> str:
    return """
        select c.id, c.customer_key, coalesce(l.name, 'unknown') as lane, c.name, c.port, c.status,
               c.activation_mode, c.service_days, c.activated_at::text as activated_at, c.starts_at::text as starts_at,
               c.expires_at::text as expires_at, c.first_connected_at::text as first_connected_at, c.expired_at::text as expired_at,
               c.delete_eligible_at::text as delete_eligible_at, c.deleted_at::text as deleted_at, c.auto_expire_enabled,
               c.auto_delete_enabled, c.lifecycle_note, p.miners, p.farms, p.maxconn, p.rate_per_min, p.burst, p.ips_mode,
               p.abuse_exempt, p.abuse_exempt_reason, p.abuse_exempt_until::text as abuse_exempt_until, p.abuse_exempt_by
        from customers c
        left join lanes l on l.id = c.lane_id
        left join customer_policies p on p.customer_id = c.id and p.is_current = true
    """


def _map_show(row: dict[str, object]) -> CustomerShowRecord:
    service_days = row.get("service_days")
    return CustomerShowRecord(
        id=int(row["id"]),
        customer_key=row.get("customer_key"),
        lane=str(row["lane"]),
        name=str(row["name"]),
        port=int(row["port"]),
        status=str(row["status"]),
        activation_mode=row.get("activation_mode"),
        service_days=int(service_days) if service_days is not None else None,
        activated_at=row.get("activated_at"),
        starts_at=row.get("starts_at"),
        expires_at=row.get("expires_at"),
        first_connected_at=row.get("first_connected_at"),
        expired_at=row.get("expired_at"),
        delete_eligible_at=row.get("delete_eligible_at"),
        deleted_at=row.get("deleted_at"),
        auto_expire_enabled=bool(row.get("auto_expire_enabled")),
        auto_delete_enabled=bool(row.get("auto_delete_enabled")),
        lifecycle_note=row.get("lifecycle_note"),
        miners=int(row["miners"]) if row.get("miners") is not None else None,
        farms=int(row["farms"]) if row.get("farms") is not None else None,
        maxconn=int(row["maxconn"]) if row.get("maxconn") is not None else None,
        rate_per_min=int(row["rate_per_min"]) if row.get("rate_per_min") is not None else None,
        burst=int(row["burst"]) if row.get("burst") is not None else None,
        ips_mode=row.get("ips_mode"),
        abuse_exempt=bool(row["abuse_exempt"]) if row.get("abuse_exempt") is not None else None,
        abuse_exempt_reason=row.get("abuse_exempt_reason"),
        abuse_exempt_until=row.get("abuse_exempt_until"),
        abuse_exempt_by=row.get("abuse_exempt_by"),
        enabled_ip_pins=[],
    )


def get_customer_show(config: MPFConfig, *, customer_key: str | None = None, customer_id: int | None = None, port: int | None = None):
    if sum(x is not None for x in (customer_key, customer_id, port)) != 1:
        return False, None, "exactly one target is required"
    where, value = ("c.customer_key = %s", customer_key) if customer_key is not None else (("c.id = %s", customer_id) if customer_id is not None else ("c.port = %s", port))
    res = query_database_params(config, _base_customer_select() + f" where {where} limit 1", (value,))
    if not res.ok:
        return False, None, res.message
    if not res.rows:
        return False, None, "customer not found"
    rec = _map_show(res.rows[0])
    pins = query_database_params(config, "select ip_cidr from customer_ip_pins where customer_id=%s and enabled=true order by ip_cidr", (rec.id,))
    if pins.ok:
        rec = CustomerShowRecord(**{**rec.__dict__, "enabled_ip_pins": [str(r["ip_cidr"]) for r in pins.rows]})
    return True, rec, "OK"
