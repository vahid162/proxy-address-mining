from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Protocol

from mpf.domain.abuse_operational import OperationalAbuseCustomer, OperationalAbuseEvaluation, OperationalAbuseState


class AbuseOperationalRepo(Protocol):
    def list_eligible_customers(self, now: datetime) -> list[OperationalAbuseCustomer]: ...
    def record_evaluation_event(self, evaluation: OperationalAbuseEvaluation, *, actor: str) -> None: ...
    def write_transition(self, evaluation: OperationalAbuseEvaluation, *, actor: str, hard_applied_at: datetime | None = None, audit: bool = False) -> None: ...
    def list_events(self, *, limit: int = 50, customer_key: str | None = None) -> list[dict[str, Any]]: ...
    def list_status_rows(self) -> list[dict[str, Any]]: ...
    def record_job_run(self, *, status: str, data: dict[str, Any]) -> None: ...


class InMemoryAbuseOperationalRepo:
    def __init__(self, customers: list[OperationalAbuseCustomer] | None = None, *, fail_reads: bool = False, fail_writes: bool = False) -> None:
        self.customers = list(customers or [])
        self.fail_reads = fail_reads
        self.fail_writes = fail_writes
        self.events: list[dict[str, Any]] = []
        self.job_runs: list[dict[str, Any]] = []
        self.audits: list[dict[str, Any]] = []

    def list_eligible_customers(self, now: datetime) -> list[OperationalAbuseCustomer]:
        if self.fail_reads:
            raise RuntimeError("database_read_failed")
        return [c for c in self.customers if c.active and c.lane_enabled and (c.policy.expires_at is None or c.policy.expires_at >= now)]

    def record_evaluation_event(self, evaluation: OperationalAbuseEvaluation, *, actor: str) -> None:
        if self.fail_writes:
            raise RuntimeError("database_write_failed")
        self.events.append({"event_type": evaluation.event_type, "actor": actor, "evaluation": evaluation.as_dict()})

    def write_transition(self, evaluation: OperationalAbuseEvaluation, *, actor: str, hard_applied_at: datetime | None = None, audit: bool = False) -> None:
        if self.fail_writes:
            raise RuntimeError("database_write_failed")
        for index, customer in enumerate(self.customers):
            if customer.customer_id == evaluation.customer_id:
                state = customer.state
                first_seen = state.first_seen_over
                last_seen = state.last_seen_over
                last_recovery = state.last_recovery_at
                if evaluation.proposed_state == "over_tracking":
                    first_seen = first_seen or datetime.now().astimezone()
                    last_seen = datetime.now().astimezone()
                elif evaluation.proposed_state == "over_grace":
                    last_recovery = datetime.now().astimezone()
                elif evaluation.proposed_state == "normal":
                    first_seen = last_seen = last_recovery = None
                self.customers[index] = OperationalAbuseCustomer(**{**asdict(customer), "policy": customer.policy, "evidence": customer.evidence, "state": OperationalAbuseState(status=evaluation.proposed_state, first_seen_over=first_seen, last_seen_over=last_seen, last_recovery_at=last_recovery, hard_applied_at=hard_applied_at or state.hard_applied_at)})
                break
        self.record_evaluation_event(evaluation, actor=actor)
        if audit:
            self.audits.append({"actor": actor, "action": evaluation.event_type, "customer_id": evaluation.customer_id, "evaluation": evaluation.as_dict()})

    def list_events(self, *, limit: int = 50, customer_key: str | None = None) -> list[dict[str, Any]]:
        if self.fail_reads:
            raise RuntimeError("database_read_failed")
        events = list(self.events)
        if customer_key is not None:
            events = [item for item in events if item.get("customer_key") == customer_key or item.get("evaluation", {}).get("customer_key") == customer_key]
        return events[:max(1, min(limit, 500))]

    def list_status_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "customer_id": customer.customer_id, "customer_key": customer.customer_key, "lane": customer.lane_id,
                "port": customer.port, "status": customer.state.status, "current_hot": customer.evidence.hot_sessions if customer.evidence else None,
                "current_unique_ips": customer.evidence.unique_source_ips if customer.evidence else None,
                "current_unique_workers": customer.evidence.unique_workers if customer.evidence else None,
                "first_seen_over": customer.state.first_seen_over, "last_seen_over": customer.state.last_seen_over,
                "last_recovery_at": customer.state.last_recovery_at, "hard_applied_at": customer.state.hard_applied_at,
                "latest_event": None, "blockers": [], "warnings": [],
            } for customer in self.customers
        ]

    def record_job_run(self, *, status: str, data: dict[str, Any]) -> None:
        if self.fail_writes:
            raise RuntimeError("database_write_failed")
        self.job_runs.append({"status": status, "data": data})
