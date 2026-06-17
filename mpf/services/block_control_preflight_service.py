"""Read-only customer block control-intent preflight service."""

from __future__ import annotations

from dataclasses import dataclass, field

from mpf.config import MPFConfig
from mpf.db import query_database_params
from mpf.domain.control_blocks import CustomerBlockPreflightRequest
from mpf.models import Base, Block


_CUSTOMER_SELECT = """
select c.id, c.customer_key, c.status, c.deleted_at
from customers c
where c.customer_key=%s
"""

_BLOCK_TABLE_SELECT = """
select 1 as present
from information_schema.tables
where table_schema = current_schema()
  and table_name = 'blocks'
limit 1
"""

_ACTIVE_BLOCK_SELECT = """
select id
from blocks
where scope='customer'
  and customer_id=%s
  and status='active'
  and removed_at is null
  and (expires_at is null or expires_at > now())
limit 1
"""


@dataclass(slots=True)
class CustomerBlockPreflightResult:
    ok: bool
    message: str
    method: str = "block_control_intent_preflight"
    ready: bool = False
    customer_id: int | None = None
    customer_key: str | None = None
    existing_active_block_intent: bool = False
    would_create_block: bool = False
    would_create_event: bool = False
    would_create_audit: bool = False
    would_mutate_customer: bool = False
    would_apply_firewall: bool = False
    would_flush_conntrack: bool = False
    would_restart_docker: bool = False
    would_restart_systemd: bool = False
    executed: bool = False
    yes_used: bool = False
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "message": self.message,
            "method": self.method,
            "ready": self.ready,
            "customer_id": self.customer_id,
            "customer_key": self.customer_key,
            "existing_active_block_intent": self.existing_active_block_intent,
            "would_create_block": self.would_create_block,
            "would_create_event": self.would_create_event,
            "would_create_audit": self.would_create_audit,
            "would_mutate_customer": self.would_mutate_customer,
            "would_apply_firewall": self.would_apply_firewall,
            "would_flush_conntrack": self.would_flush_conntrack,
            "would_restart_docker": self.would_restart_docker,
            "would_restart_systemd": self.would_restart_systemd,
            "executed": self.executed,
            "yes_used": self.yes_used,
            "blockers": list(self.blockers),
        }


def _blocked(message: str, blocker: str, *, customer_key: str | None = None) -> CustomerBlockPreflightResult:
    return CustomerBlockPreflightResult(ok=False, message=message, customer_key=customer_key, blockers=[blocker])


def _block_model_available() -> bool:
    table = Base.metadata.tables.get("blocks")
    required = {"scope", "customer_id", "reason", "starts_at", "expires_at", "status", "created_by", "removed_at", "removed_by"}
    return Block.__tablename__ == "blocks" and table is not None and required.issubset(set(table.columns.keys()))


def preflight_customer_block_intent(config: MPFConfig, req: CustomerBlockPreflightRequest) -> CustomerBlockPreflightResult:
    """Validate a future customer block intent without writing DB/runtime state."""
    try:
        req.validate()
    except Exception as exc:  # noqa: BLE001 - fail closed as structured preflight JSON.
        return _blocked(str(exc), "block_preflight_failed", customer_key=getattr(req, "customer_key", None))

    if not _block_model_available():
        return _blocked("block model is unavailable", "block_model_unavailable", customer_key=req.customer_key)

    table_result = query_database_params(config, _BLOCK_TABLE_SELECT)
    if not table_result.ok:
        return _blocked("database read failed", "db_read_failed", customer_key=req.customer_key)
    if not table_result.rows:
        return _blocked("blocks table is unavailable", "block_table_unavailable", customer_key=req.customer_key)

    customer_result = query_database_params(config, _CUSTOMER_SELECT, (req.customer_key,))
    if not customer_result.ok:
        return _blocked("database read failed", "db_read_failed", customer_key=req.customer_key)
    if len(customer_result.rows) != 1:
        return _blocked("target customer could not be resolved safely", "customer_show_or_target_resolution_failed", customer_key=req.customer_key)

    customer = customer_result.rows[0]
    status = str(customer.get("status") or "")
    if status == "deleted" or customer.get("deleted_at") not in (None, ""):
        return _blocked("deleted customer cannot be blocked by preflight", "customer_deleted", customer_key=req.customer_key)

    try:
        customer_id = int(customer["id"])
    except Exception:  # noqa: BLE001
        return _blocked("target customer could not be resolved safely", "customer_show_or_target_resolution_failed", customer_key=req.customer_key)

    active_result = query_database_params(config, _ACTIVE_BLOCK_SELECT, (customer_id,))
    if not active_result.ok:
        return _blocked("database read failed", "db_read_failed", customer_key=req.customer_key)

    return CustomerBlockPreflightResult(
        ok=True,
        message="DRY_RUN_OK",
        ready=True,
        customer_id=customer_id,
        customer_key=str(customer.get("customer_key") or req.customer_key),
        existing_active_block_intent=bool(active_result.rows),
        would_create_block=True,
        would_create_event=True,
        would_create_audit=True,
        blockers=[],
    )
