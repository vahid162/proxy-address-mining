from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.db import query_database


@dataclass(frozen=True)
class CustomerRecord:
    id: int
    lane: str
    name: str
    port: int
    status: str
    expires_at: str | None


def list_customers(config: MPFConfig, limit: int = 100) -> tuple[bool, list[CustomerRecord], str]:
    """Return customer rows without mutating customer state."""
    safe_limit = max(1, min(limit, 1000))
    sql = f"""
        select
            customers.id,
            coalesce(lanes.name, 'unknown') as lane,
            customers.name,
            customers.port,
            customers.status,
            customers.expires_at::text as expires_at
        from customers
        left join lanes on lanes.id = customers.lane_id
        order by customers.port
        limit {safe_limit}
    """
    result = query_database(config, sql)
    if not result.ok:
        return False, [], result.message

    records = [
        CustomerRecord(
            id=int(row["id"]),
            lane=str(row["lane"]),
            name=str(row["name"]),
            port=int(row["port"]),
            status=str(row["status"]),
            expires_at=str(row["expires_at"]) if row.get("expires_at") else None,
        )
        for row in result.rows
    ]
    return True, records, "OK"
