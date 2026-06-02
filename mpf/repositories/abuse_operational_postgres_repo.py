from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from mpf.config import MPFConfig
from mpf.db import query_database_params
from mpf.domain.abuse_operational import (
    OperationalAbuseCustomer,
    OperationalAbuseEvidence,
    OperationalAbuseEvaluation,
    OperationalAbusePolicy,
    OperationalAbuseState,
)

_ALLOWED_DB_ONLY_STATES = {"normal", "over_tracking", "over_grace"}


def _empty_to_none(value: Any) -> Any:
    if value == "":
        return None
    return value


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    if text in {"t", "true", "1", "yes", "on"}:
        return True
    if text in {"f", "false", "0", "no", "off", ""}:
        return False
    return False


def _parse_int(value: Any, *, default: int = 0) -> int:
    value = _empty_to_none(value)
    if value is None:
        return default
    return int(value)


def _parse_datetime(value: Any) -> datetime | None:
    value = _empty_to_none(value)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    text = str(value).strip()
    if not text:
        return None
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _parse_text_array(value: Any) -> list[str]:
    value = _empty_to_none(value)
    if value is None:
        return []
    if isinstance(value, list | tuple):
        return [str(item) for item in value]
    text = str(value).strip()
    if not text or text == "{}":
        return []
    if text.startswith("{") and text.endswith("}"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"') for item in inner.split(",") if item.strip()]
    return [text]


def _parse_json_value(value: Any) -> Any:
    value = _empty_to_none(value)
    if value is None or isinstance(value, dict | list):
        return value if value is not None else {}
    text = str(value).strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


class PostgresAbuseOperationalRepo:
    """Controlled PostgreSQL abuse repository.

    Reads are DB-backed. Fresh evidence is accepted only when explicitly supplied
    by an operator-controlled package; persisted default counters are visibility
    fields, not an implicit evidence source. Writes are restricted to
    abuse_states, abuse_events, and job_runs.
    """

    def __init__(self, config: MPFConfig, *, evidence_by_customer_id: dict[int, OperationalAbuseEvidence] | None = None) -> None:
        self.config = config
        self.evidence_by_customer_id = dict(evidence_by_customer_id or {})
        self._loaded_customers: dict[int, OperationalAbuseCustomer] = {}

    def _query(self, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, Any]]:
        result = query_database_params(self.config, sql, params)
        if not result.ok:
            raise RuntimeError(result.message)
        return result.rows

    def _connect(self):
        import psycopg

        return psycopg.connect(self.config.database.url, connect_timeout=5)

    def list_eligible_customers(self, now: datetime) -> list[OperationalAbuseCustomer]:
        rows = self._query(
            """
            select c.id as customer_id, c.lane_id, coalesce(c.customer_key, 'customer-id-' || c.id::text) as customer_key,
                   c.port, l.enabled as lane_enabled, p.miners, p.farms, c.expires_at as policy_expires_at,
                   p.abuse_exempt, p.abuse_exempt_reason, p.abuse_exempt_until,
                   coalesce(s.status, 'normal') as abuse_status, s.first_seen_over, s.last_seen_over,
                   s.last_recovery_at, s.hard_applied_at
            from customers c
            join lanes l on l.id = c.lane_id and l.enabled = true
            join customer_policies p on p.customer_id = c.id and p.is_current = true
            left join abuse_states s on s.customer_id = c.id
            where c.status = 'active' and c.deleted_at is null
              and (c.expires_at is null or c.expires_at >= %s)
            order by lower(l.name), c.port, c.id
            """,
            (now,),
        )
        customers = [self._customer_from_row(row) for row in rows]
        self._loaded_customers = {customer.customer_id: customer for customer in customers}
        return customers

    def _customer_from_row(self, row: dict[str, Any]) -> OperationalAbuseCustomer:
        customer_id = _parse_int(row["customer_id"])
        return OperationalAbuseCustomer(
            customer_id=customer_id,
            lane_id=_parse_int(row["lane_id"]),
            customer_key=str(row["customer_key"]),
            port=_parse_int(row["port"]),
            active=True,
            lane_enabled=_parse_bool(row["lane_enabled"]),
            policy=OperationalAbusePolicy(
                miners=_parse_int(row["miners"]),
                farms=_parse_int(row["farms"]),
                expires_at=_parse_datetime(row.get("policy_expires_at")),
                abuse_exempt=_parse_bool(row.get("abuse_exempt", False)),
                abuse_exempt_reason=_empty_to_none(row.get("abuse_exempt_reason")),
                abuse_exempt_until=_parse_datetime(row.get("abuse_exempt_until")),
            ),
            state=OperationalAbuseState(
                status=str(row["abuse_status"]),
                first_seen_over=_parse_datetime(row.get("first_seen_over")),
                last_seen_over=_parse_datetime(row.get("last_seen_over")),
                last_recovery_at=_parse_datetime(row.get("last_recovery_at")),
                hard_applied_at=_parse_datetime(row.get("hard_applied_at")),
            ),
            evidence=self.evidence_by_customer_id.get(customer_id),
        )

    def list_status_rows(self) -> list[dict[str, Any]]:
        rows = self._query(
            """
            select c.id as customer_id, coalesce(c.customer_key, 'customer-id-' || c.id::text) as customer_key,
                   l.name as lane, c.port, coalesce(s.status, 'normal') as status,
                   coalesce(s.current_hot, 0) as current_hot,
                   coalesce(s.current_unique_ips, 0) as current_unique_ips,
                   coalesce(s.current_unique_workers, 0) as current_unique_workers,
                   s.first_seen_over, s.last_seen_over, s.last_recovery_at, s.hard_applied_at,
                   latest.event_type as latest_event,
                   (case when c.customer_key is null then array['missing_customer_key']::text[] else array[]::text[] end ||
                    case when p.abuse_exempt and (p.abuse_exempt_reason is null or p.abuse_exempt_until is null or p.abuse_exempt_until < now())
                         then array['invalid_or_expired_exemption_ignored']::text[] else array[]::text[] end) as warnings,
                   array[]::text[] as blockers
            from customers c
            join lanes l on l.id = c.lane_id and l.enabled = true
            join customer_policies p on p.customer_id = c.id and p.is_current = true
            left join abuse_states s on s.customer_id = c.id
            left join lateral (
                select ae.event_type from abuse_events ae where ae.customer_id = c.id
                order by ae.created_at desc, ae.id desc limit 1
            ) latest on true
            where c.status = 'active' and c.deleted_at is null
              and (c.expires_at is null or c.expires_at >= now())
            order by lower(l.name), c.port, c.id
            """
        )
        return [self._status_row_from_row(row) for row in rows]

    def _status_row_from_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "customer_id": _parse_int(row.get("customer_id")),
            "customer_key": str(row.get("customer_key", "")),
            "lane": str(row.get("lane", "")),
            "port": _parse_int(row.get("port")),
            "status": str(row.get("status", "normal")),
            "current_hot": _parse_int(row.get("current_hot")),
            "current_unique_ips": _parse_int(row.get("current_unique_ips")),
            "current_unique_workers": _parse_int(row.get("current_unique_workers")),
            "first_seen_over": _parse_datetime(row.get("first_seen_over")),
            "last_seen_over": _parse_datetime(row.get("last_seen_over")),
            "last_recovery_at": _parse_datetime(row.get("last_recovery_at")),
            "hard_applied_at": _parse_datetime(row.get("hard_applied_at")),
            "latest_event": _empty_to_none(row.get("latest_event")),
            "warnings": _parse_text_array(row.get("warnings")),
            "blockers": _parse_text_array(row.get("blockers")),
        }

    def list_events(self, *, limit: int = 50, customer_key: str | None = None) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 500))
        customer_filter = "and c.customer_key = %s" if customer_key else ""
        params: tuple[object, ...] = (customer_key,) if customer_key else ()
        rows = self._query(
            f"""
            select ae.customer_id, c.customer_key, ae.event_type, ae.old_status, ae.new_status,
                   ae.created_at, ae.created_by, ae.evidence_json
            from abuse_events ae
            join customers c on c.id = ae.customer_id
            where true {customer_filter}
            order by ae.created_at desc, ae.id desc
            limit {safe_limit}
            """,
            params,
        )
        return [self._event_row_from_row(row) for row in rows]

    def _event_row_from_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "customer_id": _parse_int(row.get("customer_id")),
            "customer_key": _empty_to_none(row.get("customer_key")),
            "event_type": str(row.get("event_type", "")),
            "old_status": _empty_to_none(row.get("old_status")),
            "new_status": str(row.get("new_status", "")),
            "created_at": _parse_datetime(row.get("created_at")),
            "created_by": _empty_to_none(row.get("created_by")),
            "evidence_json": _parse_json_value(row.get("evidence_json")),
        }

    def record_evaluation_event(self, evaluation: OperationalAbuseEvaluation, *, actor: str) -> None:
        self._insert_event(evaluation, actor=actor)

    def write_transition(self, evaluation: OperationalAbuseEvaluation, *, actor: str, hard_applied_at: datetime | None = None, audit: bool = False) -> None:
        if hard_applied_at is not None or evaluation.proposed_state not in _ALLOWED_DB_ONLY_STATES:
            raise RuntimeError("controlled_postgresql_repo_forbids_hard_apply")
        customer = self._loaded_customers.get(evaluation.customer_id)
        evidence = customer.evidence if customer else None
        hot = evidence.hot_sessions if evidence and evidence.hot_sessions is not None else 0
        ips = evidence.unique_source_ips if evidence and evidence.unique_source_ips is not None else 0
        workers = evidence.unique_workers if evidence and evidence.unique_workers is not None else 0
        now = datetime.now(UTC)
        with self._connect() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into abuse_states (customer_id, status, current_hot, current_unique_ips, current_unique_workers,
                                                  first_seen_over, last_seen_over, last_recovery_at, hard_applied_at, updated_at)
                        values (%s, %s, %s, %s, %s,
                                case when %s = 'over_tracking' then %s else null end,
                                case when %s = 'over_tracking' then %s else null end,
                                case when %s = 'over_grace' then %s else null end,
                                null, %s)
                        on conflict (customer_id) do update set
                            status = excluded.status,
                            current_hot = excluded.current_hot,
                            current_unique_ips = excluded.current_unique_ips,
                            current_unique_workers = excluded.current_unique_workers,
                            first_seen_over = case
                                when excluded.status = 'normal' then null
                                when excluded.status = 'over_tracking' then coalesce(abuse_states.first_seen_over, excluded.first_seen_over)
                                else abuse_states.first_seen_over end,
                            last_seen_over = case when excluded.status = 'normal' then null else coalesce(excluded.last_seen_over, abuse_states.last_seen_over) end,
                            last_recovery_at = case
                                when excluded.status = 'normal' then null
                                when excluded.status = 'over_grace' then excluded.last_recovery_at
                                else abuse_states.last_recovery_at end,
                            hard_applied_at = abuse_states.hard_applied_at,
                            updated_at = excluded.updated_at
                        """,
                        (evaluation.customer_id, evaluation.proposed_state, hot, ips, workers,
                         evaluation.proposed_state, now, evaluation.proposed_state, now,
                         evaluation.proposed_state, now, now),
                    )
                    self._insert_event_with_cursor(cur, evaluation, actor=actor)

    def _insert_event(self, evaluation: OperationalAbuseEvaluation, *, actor: str) -> None:
        with self._connect() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    self._insert_event_with_cursor(cur, evaluation, actor=actor)

    def _insert_event_with_cursor(self, cur: Any, evaluation: OperationalAbuseEvaluation, *, actor: str) -> None:
        if not evaluation.event_type:
            return
        cur.execute(
            """
            insert into abuse_events (customer_id, old_status, new_status, event_type, evidence_json, created_by)
            values (%s, %s, %s, %s, %s::jsonb, %s)
            """,
            (evaluation.customer_id, evaluation.current_state, evaluation.proposed_state,
             evaluation.event_type, json.dumps(evaluation.as_dict(), default=str, sort_keys=True), actor),
        )

    def record_job_run(self, *, status: str, data: dict[str, Any]) -> None:
        now = datetime.now(UTC)
        with self._connect() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into job_runs (job_name, status, started_at, finished_at, affected_count, data_json)
                        values (%s, %s, %s, %s, %s, %s::jsonb)
                        """,
                        ("abuse.controlled_operator_cycle", status, now, now, data.get("scanned_customer_count", 0),
                         json.dumps(data, default=str, sort_keys=True)),
                    )
