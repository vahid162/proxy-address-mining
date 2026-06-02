from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

ABUSE_STATES = {"normal", "over_tracking", "over_grace", "hard"}
DEFAULT_THRESHOLD_SECONDS = 3600
DEFAULT_GRACE_SECONDS = 900
DEFAULT_EVIDENCE_MAX_AGE_SECONDS = 300


@dataclass(frozen=True)
class OperationalAbusePolicy:
    miners: int
    farms: int
    expires_at: datetime | None = None
    abuse_exempt: bool = False
    abuse_exempt_reason: str | None = None
    abuse_exempt_until: datetime | None = None


@dataclass(frozen=True)
class OperationalAbuseEvidence:
    hot_sessions: int | None
    unique_source_ips: int | None
    unique_workers: int | None
    observed_at: datetime | None
    collected_at: datetime | None
    source: str = "controlled_package"


@dataclass(frozen=True)
class OperationalAbuseState:
    status: str = "normal"
    first_seen_over: datetime | None = None
    last_seen_over: datetime | None = None
    last_recovery_at: datetime | None = None
    hard_applied_at: datetime | None = None


@dataclass(frozen=True)
class OperationalAbuseCustomer:
    customer_id: int
    lane_id: int
    customer_key: str
    port: int
    active: bool
    lane_enabled: bool
    policy: OperationalAbusePolicy
    state: OperationalAbuseState
    evidence: OperationalAbuseEvidence | None


@dataclass
class OperationalAbuseEvaluation:
    customer_id: int
    lane_id: int
    customer_key: str
    port: int
    current_state: str
    proposed_state: str
    result: str
    event_type: str | None = None
    miner_over: bool = False
    farms_over: bool = False
    worker_over: bool = False
    sustained_over_seconds: int = 0
    write_transition: bool = False
    requires_controlled_hard: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _seconds_since(now: datetime, value: datetime | None) -> int:
    if value is None:
        return 0
    return max(0, int((now - value).total_seconds()))


def evaluate_operational_abuse(
    customer: OperationalAbuseCustomer,
    *,
    now: datetime | None = None,
    threshold_seconds: int = DEFAULT_THRESHOLD_SECONDS,
    grace_seconds: int = DEFAULT_GRACE_SECONDS,
    evidence_max_age_seconds: int = DEFAULT_EVIDENCE_MAX_AGE_SECONDS,
) -> OperationalAbuseEvaluation:
    now = now or datetime.now(UTC)
    state = customer.state
    result = OperationalAbuseEvaluation(
        customer_id=customer.customer_id,
        lane_id=customer.lane_id,
        customer_key=customer.customer_key,
        port=customer.port,
        current_state=state.status,
        proposed_state=state.status,
        result="no_change",
    )
    if state.status not in ABUSE_STATES:
        result.result = "evaluation_failed"
        result.blockers.append("invalid_abuse_state")
        return result
    if not customer.active or not customer.lane_enabled:
        result.result = "out_of_scope"
        return result
    if customer.policy.expires_at is not None and customer.policy.expires_at < now:
        result.result = "out_of_scope_expired_policy"
        return result
    if customer.policy.abuse_exempt:
        if customer.policy.abuse_exempt_reason and customer.policy.abuse_exempt_until and customer.policy.abuse_exempt_until >= now:
            result.result = "exempt"
            return result
        result.warnings.append("invalid_or_expired_exemption_ignored")

    evidence = customer.evidence
    if evidence is None:
        result.result = "evaluation_failed"
        result.event_type = "abuse.evaluation_failed"
        result.blockers.append("missing_evidence")
        return result
    if evidence.observed_at is None or evidence.collected_at is None:
        result.result = "evaluation_failed"
        result.event_type = "abuse.evaluation_failed"
        result.blockers.append("missing_evidence_timestamp")
        return result
    if _seconds_since(now, evidence.observed_at) > evidence_max_age_seconds or _seconds_since(now, evidence.collected_at) > evidence_max_age_seconds:
        result.result = "stale_evidence"
        result.event_type = "abuse.evaluation_failed"
        result.blockers.append("stale_evidence")
        return result
    if evidence.hot_sessions is None:
        result.result = "evaluation_failed"
        result.event_type = "abuse.evaluation_failed"
        result.blockers.append("missing_hot_sessions")
        return result

    result.miner_over = evidence.hot_sessions > customer.policy.miners
    result.farms_over = (evidence.unique_source_ips or 0) > customer.policy.farms
    result.worker_over = (evidence.unique_workers or 0) > customer.policy.miners
    if result.farms_over and not result.miner_over:
        result.warnings.append("farms_over_report_only")
    if result.worker_over and not result.miner_over:
        result.warnings.append("worker_over_report_only")

    if state.status == "hard":
        result.result = "hard_requires_manual_unhard"
    elif state.status == "normal" and result.miner_over:
        result.proposed_state = "over_tracking"
        result.result = "transition"
        result.event_type = "abuse.entered_over_tracking"
        result.write_transition = True
    elif state.status == "over_tracking" and not result.miner_over:
        result.proposed_state = "over_grace"
        result.result = "transition"
        result.event_type = "abuse.entered_over_grace"
        result.write_transition = True
    elif state.status == "over_tracking" and result.miner_over:
        if state.first_seen_over is None:
            result.result = "evaluation_failed"
            result.event_type = "abuse.evaluation_failed"
            result.blockers.append("missing_first_seen_over")
        else:
            result.sustained_over_seconds = _seconds_since(now, state.first_seen_over)
            if result.sustained_over_seconds >= threshold_seconds:
                result.proposed_state = "hard"
                result.result = "hard_planned"
                result.event_type = "abuse.hard_planned"
                result.requires_controlled_hard = True
            else:
                result.result = "tracking"
    elif state.status == "over_grace" and result.miner_over:
        result.proposed_state = "over_tracking"
        result.result = "transition"
        result.event_type = "abuse.entered_over_tracking"
        result.write_transition = True
    elif state.status == "over_grace":
        if state.last_recovery_at is None:
            result.result = "evaluation_failed"
            result.event_type = "abuse.evaluation_failed"
            result.blockers.append("missing_last_recovery_at")
        elif _seconds_since(now, state.last_recovery_at) >= grace_seconds:
            result.proposed_state = "normal"
            result.result = "transition"
            result.event_type = "abuse.recovered_normal"
            result.write_transition = True
        else:
            result.result = "grace"
    return result
