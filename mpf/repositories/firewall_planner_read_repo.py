from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.db import query_database


@dataclass(frozen=True)
class FirewallPlannerInputLoadResult:
    ok: bool
    lanes: list[dict]
    customers: list[dict]
    message: str


def load_firewall_planner_input(config: MPFConfig) -> FirewallPlannerInputLoadResult:
    lanes_sql = """
        select name, enabled, backend_port
        from lanes
        order by name
    """
    lanes_result = query_database(config, lanes_sql)
    if not lanes_result.ok:
        return FirewallPlannerInputLoadResult(ok=False, lanes=[], customers=[], message=f"failed to load lanes: {lanes_result.message}")

    customers_sql = """
        select
            c.id,
            c.customer_key,
            coalesce(l.name, 'unknown') as lane,
            c.port,
            c.status,
            p.miners,
            p.farms,
            p.maxconn,
            p.rate_per_min,
            p.burst,
            p.ips_mode,
            p.abuse_exempt,
            p.abuse_exempt_reason,
            p.abuse_exempt_until::text as abuse_exempt_until,
            p.abuse_exempt_by
        from customers c
        left join lanes l on l.id = c.lane_id
        left join customer_policies p on p.customer_id = c.id and p.is_current = true
        where c.status <> 'deleted'
        order by c.port
    """
    customers_result = query_database(config, customers_sql)
    if not customers_result.ok:
        return FirewallPlannerInputLoadResult(ok=False, lanes=[], customers=[], message=f"failed to load customers: {customers_result.message}")

    lanes = [
        {"name": str(row["name"]), "enabled": str(row["enabled"]).lower() in {"true", "t", "1"}, "backend_port": int(row["backend_port"])}
        for row in lanes_result.rows
    ]
    pins_sql = """
        select customer_id, id, ip_cidr, enabled
        from customer_ip_pins
        order by customer_id, id
    """
    pins_result = query_database(config, pins_sql)
    if not pins_result.ok:
        return FirewallPlannerInputLoadResult(ok=False, lanes=[], customers=[], message=f"failed to load customer_ip_pins: {pins_result.message}")
    pins_by_customer: dict[int, list[dict]] = {}
    for row in pins_result.rows:
        cid = int(row["customer_id"])
        pins_by_customer.setdefault(cid, []).append({"id": int(row["id"]), "ip_cidr": str(row["ip_cidr"]), "enabled": str(row.get("enabled")).lower() in {"true", "t", "1"}})

    customers: list[dict] = []
    for row in customers_result.rows:
        cid = int(row["id"])
        enabled_pins = [pin for pin in pins_by_customer.get(cid, []) if pin.get("enabled")]
        customers.append(
            {
                "id": cid,
                "customer_key": row.get("customer_key"),
                "lane": str(row["lane"]),
                "port": int(row["port"]),
                "status": str(row["status"]),
                "ip_pins": pins_by_customer.get(cid, []),
                "ip_whitelist": [pin["ip_cidr"] for pin in enabled_pins],
                "ip_pin_identity": [{"id": pin["id"], "ip_cidr": pin["ip_cidr"]} for pin in enabled_pins],
                "policy": {
                    "miners": int(row["miners"]) if row.get("miners") is not None else None,
                    "farms": int(row["farms"]) if row.get("farms") is not None else None,
                    "maxconn": int(row["maxconn"]) if row.get("maxconn") is not None else None,
                    "rate_per_min": int(row["rate_per_min"]) if row.get("rate_per_min") is not None else None,
                    "burst": int(row["burst"]) if row.get("burst") is not None else None,
                    "ips_mode": row.get("ips_mode"),
                    "abuse_exempt": row.get("abuse_exempt"),
                    "abuse_exempt_reason": row.get("abuse_exempt_reason"),
                    "abuse_exempt_until": row.get("abuse_exempt_until"),
                    "abuse_exempt_by": row.get("abuse_exempt_by"),
                },
            }
        )

    return FirewallPlannerInputLoadResult(ok=True, lanes=lanes, customers=customers, message="OK")
