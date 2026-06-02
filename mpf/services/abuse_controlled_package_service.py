from __future__ import annotations

from datetime import datetime
from typing import Any

from mpf.domain.abuse_operational import OperationalAbuseCustomer, OperationalAbuseEvidence, OperationalAbusePolicy, OperationalAbuseState
from mpf.repositories.abuse_operational_repo import InMemoryAbuseOperationalRepo


def _dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("timestamp must be ISO-8601 text")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def repo_from_controlled_package(package: dict[str, Any]) -> InMemoryAbuseOperationalRepo:
    customers = package.get("customers")
    if not isinstance(customers, list):
        raise ValueError("controlled package requires customers list")
    parsed: list[OperationalAbuseCustomer] = []
    for item in customers:
        policy = item.get("policy", {})
        state = item.get("state", {})
        evidence = item.get("evidence")
        parsed.append(OperationalAbuseCustomer(
            customer_id=int(item["customer_id"]), lane_id=int(item["lane_id"]), customer_key=str(item["customer_key"]), port=int(item["port"]),
            active=bool(item.get("active", True)), lane_enabled=bool(item.get("lane_enabled", True)),
            policy=OperationalAbusePolicy(miners=int(policy["miners"]), farms=int(policy["farms"]), expires_at=_dt(policy.get("expires_at")), abuse_exempt=bool(policy.get("abuse_exempt", False)), abuse_exempt_reason=policy.get("abuse_exempt_reason"), abuse_exempt_until=_dt(policy.get("abuse_exempt_until"))),
            state=OperationalAbuseState(status=str(state.get("status", "normal")), first_seen_over=_dt(state.get("first_seen_over")), last_seen_over=_dt(state.get("last_seen_over")), last_recovery_at=_dt(state.get("last_recovery_at")), hard_applied_at=_dt(state.get("hard_applied_at"))),
            evidence=None if evidence is None else OperationalAbuseEvidence(hot_sessions=evidence.get("hot_sessions"), unique_source_ips=evidence.get("unique_source_ips"), unique_workers=evidence.get("unique_workers"), observed_at=_dt(evidence.get("observed_at")), collected_at=_dt(evidence.get("collected_at")), source=str(evidence.get("source", "controlled_package"))),
        ))
    return InMemoryAbuseOperationalRepo(parsed)
