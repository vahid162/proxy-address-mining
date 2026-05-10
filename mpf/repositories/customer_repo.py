from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from mpf.config import MPFConfig
from mpf.db import query_database, query_database_params

ALLOWED_STATUSES = {"active", "paused", "expired", "deleted"}
ALLOWED_EVENT_SEVERITIES = {"info", "warning", "error", "critical"}
RESERVED_CUSTOMER_PORTS = {2015, 60010, 60015, 60020}


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


@dataclass(frozen=True)
class NextPortSuggestion:
    lane: str
    lane_enabled: bool
    suggested_port: int
    checked_range: str
    occupied_count: int
    skipped_reserved_count: int


@dataclass(frozen=True)
class CustomerLifecycleReportRow:
    customer_key: str | None
    lane: str
    name: str
    port: int
    status: str
    expires_at: str | None
    expired_at: str | None = None
    delete_eligible_at: str | None = None
    days_remaining: int | None = None


@dataclass(frozen=True)
class CustomerHistoryTarget:
    id: int
    customer_key: str | None
    lane: str
    port: int


def clamp_limit(limit: int) -> int:
    return max(1, min(limit, 1000))


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



def _to_bool(value: object, *, nullable: bool = False) -> bool | None:
    if value is None:
        return None if nullable else False
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"t", "true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"f", "false", "0", "no", "n", "off"}:
        return False
    return bool(value)

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
        auto_expire_enabled=bool(_to_bool(row.get("auto_expire_enabled"))),
        auto_delete_enabled=bool(_to_bool(row.get("auto_delete_enabled"))),
        lifecycle_note=row.get("lifecycle_note"),
        miners=int(row["miners"]) if row.get("miners") is not None else None,
        farms=int(row["farms"]) if row.get("farms") is not None else None,
        maxconn=int(row["maxconn"]) if row.get("maxconn") is not None else None,
        rate_per_min=int(row["rate_per_min"]) if row.get("rate_per_min") is not None else None,
        burst=int(row["burst"]) if row.get("burst") is not None else None,
        ips_mode=row.get("ips_mode"),
        abuse_exempt=_to_bool(row.get("abuse_exempt"), nullable=True),
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


def resolve_customer_target(config: MPFConfig, *, customer_key: str | None = None, customer_id: int | None = None, port: int | None = None):
    if sum(x is not None for x in (customer_key, customer_id, port)) != 1:
        return False, None, "provide exactly one target: --customer-key or --id or --port"
    where, value = ("c.customer_key = %s", customer_key) if customer_key is not None else (("c.id = %s", customer_id) if customer_id is not None else ("c.port = %s", port))
    sql = f"""
    select c.id, c.customer_key, coalesce(l.name, 'unknown') as lane, c.port
    from customers c
    left join lanes l on l.id = c.lane_id
    where {where}
    limit 1
    """
    res = query_database_params(config, sql, (value,))
    if not res.ok:
        return False, None, res.message
    if not res.rows:
        return False, None, "customer not found"
    row = res.rows[0]
    return True, CustomerHistoryTarget(id=int(row["id"]), customer_key=row.get("customer_key"), lane=str(row["lane"]), port=int(row["port"])), "OK"


def list_customer_policy_history(config: MPFConfig, *, customer_id: int, limit: int):
    sql = """
    select
      c.id as customer_id, c.customer_key, coalesce(l.name, 'unknown') as lane, c.port,
      p.id as policy_id, p.version, p.is_current, p.miners, p.farms, p.maxconn, p.rate_per_min, p.burst,
      p.ips_mode, p.abuse_exempt, p.abuse_exempt_reason, p.abuse_exempt_until::text as abuse_exempt_until,
      p.abuse_exempt_by, p.created_at::text as created_at, p.created_by, p.reason
    from customer_policies p
    join customers c on c.id = p.customer_id
    left join lanes l on l.id = c.lane_id
    where p.customer_id = %s
    order by p.version desc, p.id desc
    limit %s
    """
    return query_database_params(config, sql, (customer_id, clamp_limit(limit)))


def list_customer_events(config: MPFConfig, *, customer_id: int, limit: int):
    sql = """
    select id, event_type, severity, subject_type, subject_id, message, data_json::text as data_json,
           created_at::text as created_at, created_by, correlation_id
    from events
    where subject_type = 'customer' and subject_id = %s
    order by created_at desc, id desc
    limit %s
    """
    return query_database_params(config, sql, (customer_id, clamp_limit(limit)))


def list_customer_audit(config: MPFConfig, *, customer_id: int, limit: int):
    sql = """
    select id, actor_type, actor_id, action, resource_type, resource_id, before_json::text as before_json,
           after_json::text as after_json, reason, created_at::text as created_at, correlation_id
    from audit_log
    where resource_type = 'customer' and resource_id = %s
    order by created_at desc, id desc
    limit %s
    """
    return query_database_params(config, sql, (customer_id, clamp_limit(limit)))


def list_latest_events(config: MPFConfig, *, limit: int, subject_type: str | None = None, severity: str | None = None):
    if severity is not None and severity not in ALLOWED_EVENT_SEVERITIES:
        return False, [], "invalid severity; expected one of: info, warning, error, critical"
    clauses: list[str] = []
    params: list[object] = []
    if subject_type:
        clauses.append("subject_type = %s")
        params.append(subject_type)
    if severity:
        clauses.append("severity = %s")
        params.append(severity)
    where_sql = f"where {' and '.join(clauses)}" if clauses else ""
    sql = f"""
    select id, event_type, severity, subject_type, subject_id, message,
           created_at::text as created_at, created_by, correlation_id
    from events
    {where_sql}
    order by created_at desc, id desc
    limit %s
    """
    params.append(clamp_limit(limit))
    res = query_database_params(config, sql, tuple(params))
    if not res.ok:
        return False, [], res.message
    return True, res.rows, "OK"


def suggest_next_port(config: MPFConfig, *, lane: str, start: int, end: int):
    lane_res = query_database_params(config, "select name, enabled, backend_port from lanes where name=%s limit 1", (lane,))
    if not lane_res.ok:
        return False, None, lane_res.message
    if not lane_res.rows:
        return False, None, f"lane not found: {lane}"

    lane_row = lane_res.rows[0]
    lane_enabled = _to_bool(lane_row.get("enabled"))
    backend_res = query_database_params(config, "select backend_port from lanes")
    if not backend_res.ok:
        return False, None, backend_res.message
    occupied_res = query_database_params(config, "select port from customers")
    if not occupied_res.ok:
        return False, None, occupied_res.message

    occupied_ports = {int(r["port"]) for r in occupied_res.rows if r.get("port") is not None}
    backend_ports = {int(r["backend_port"]) for r in backend_res.rows if r.get("backend_port") is not None}
    reserved = RESERVED_CUSTOMER_PORTS | backend_ports
    skipped_reserved_count = sum(1 for p in range(start, end + 1) if p in reserved)

    for port in range(start, end + 1):
        if port in reserved:
            continue
        if port in occupied_ports:
            continue
        return True, NextPortSuggestion(lane=lane, lane_enabled=bool(lane_enabled), suggested_port=port, checked_range=f"{start}-{end}", occupied_count=len(occupied_ports), skipped_reserved_count=skipped_reserved_count), "OK"
    return False, None, f"no available port found in range {start}-{end}"


def list_expiring_customers(config: MPFConfig, *, within_days: int, include_paused: bool, limit: int):
    paused_clause = "" if include_paused else " and c.status <> 'paused'"
    sql = f"""
    with now_ref as (select now() as ts)
    select c.customer_key, coalesce(l.name, 'unknown') as lane, c.name, c.port, c.status,
           c.expires_at::text as expires_at,
           floor(extract(epoch from (c.expires_at - now_ref.ts))/86400)::int as days_remaining
    from customers c
    left join lanes l on l.id = c.lane_id
    cross join now_ref
    where c.expires_at is not null
      and c.expires_at >= now_ref.ts
      and c.expires_at <= now_ref.ts + make_interval(days => %s)
      and c.status <> 'deleted'
      {paused_clause}
    order by c.expires_at asc, c.port asc
    limit %s
    """
    res = query_database_params(config, sql, (within_days, limit))
    if not res.ok:
        return False, [], res.message
    rows = [CustomerLifecycleReportRow(customer_key=r.get("customer_key"), lane=str(r["lane"]), name=str(r["name"]), port=int(r["port"]), status=str(r["status"]), expires_at=r.get("expires_at"), days_remaining=int(r["days_remaining"]) if r.get("days_remaining") is not None else None) for r in res.rows]
    return True, rows, "OK"


def list_expired_customers(config: MPFConfig, *, include_deleted: bool, limit: int):
    deleted_clause = "" if include_deleted else "and c.status <> 'deleted'"
    sql = f"""
    with now_ref as (select now() as ts)
    select c.customer_key, coalesce(l.name, 'unknown') as lane, c.name, c.port, c.status,
           c.expires_at::text as expires_at,
           c.expired_at::text as expired_at
    from customers c
    left join lanes l on l.id = c.lane_id
    cross join now_ref
    where ((c.expires_at is not null and c.expires_at < now_ref.ts) or c.status = 'expired')
      {deleted_clause}
    order by coalesce(c.expired_at, c.expires_at) desc nulls last, c.port asc
    limit %s
    """
    res = query_database_params(config, sql, (limit,))
    if not res.ok:
        return False, [], res.message
    rows = [CustomerLifecycleReportRow(customer_key=r.get("customer_key"), lane=str(r["lane"]), name=str(r["name"]), port=int(r["port"]), status=str(r["status"]), expires_at=r.get("expires_at"), expired_at=r.get("expired_at")) for r in res.rows]
    return True, rows, "OK"


def list_delete_eligible_customers(config: MPFConfig, *, limit: int):
    sql = """
    with now_ref as (select now() as ts)
    select c.customer_key, coalesce(l.name, 'unknown') as lane, c.name, c.port, c.status,
           c.expires_at::text as expires_at,
           c.delete_eligible_at::text as delete_eligible_at
    from customers c
    left join lanes l on l.id = c.lane_id
    cross join now_ref
    where c.delete_eligible_at is not null
      and c.delete_eligible_at <= now_ref.ts
      and c.status <> 'deleted'
    order by c.delete_eligible_at asc, c.port asc
    limit %s
    """
    res = query_database_params(config, sql, (limit,))
    if not res.ok:
        return False, [], res.message
    rows = [CustomerLifecycleReportRow(customer_key=r.get("customer_key"), lane=str(r["lane"]), name=str(r["name"]), port=int(r["port"]), status=str(r["status"]), expires_at=r.get("expires_at"), delete_eligible_at=r.get("delete_eligible_at")) for r in res.rows]
    return True, rows, "OK"
