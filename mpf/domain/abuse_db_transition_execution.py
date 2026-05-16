from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

REQUIRED_CONFIRMATION = "I_UNDERSTAND_DB_ONLY_ABUSE_TRANSITION"
ALLOWED_REQUEST_SOURCE = "explicit_manual_cli"
_ALLOWED_STATES = {"normal", "over_tracking", "over_grace", "hard"}


@dataclass(slots=True)
class AbuseDBExecutionRequest:
    plan_id: str
    idempotency_key: str
    customer_id: int
    lane_id: int
    port: int
    current_state: str
    proposed_state: str
    decision: str
    evidence_status: str
    evidence_reference: str | None
    restore_reference: str | None
    policy_backup_reference: str | None
    operator_id: str | None
    operator_reason: str | None
    operator_confirmation: str | None
    request_source: str
    dry_run: bool = True


@dataclass(slots=True)
class AbuseDBExecutionValidation:
    valid: bool
    dry_run: bool
    execution_allowed: bool
    db_writes_allowed: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_confirmation: str = REQUIRED_CONFIRMATION
    hard_transition: bool = False
    operator_approval_complete: bool = False


@dataclass(slots=True)
class AbuseDBExecutionResult:
    final_decision: str
    dry_run: bool
    execution_allowed: bool
    db_writes_executed: bool
    abuse_state_written: bool
    abuse_event_written: bool
    idempotency_key: str
    plan_id: str
    current_state: str
    proposed_state: str
    decision: str
    blockers: list[str]
    warnings: list[str]
    would_write: dict[str, Any]
    written: dict[str, Any]


def _non_empty(v: str) -> bool:
    return bool(v and v.strip())


def validate_db_execution_request(request: AbuseDBExecutionRequest) -> AbuseDBExecutionValidation:
    blockers: list[str] = []
    hard_transition = request.proposed_state == "hard"
    operator_approval_complete = all([
        _non_empty(request.operator_id or ""),
        _non_empty(request.operator_reason or ""),
        _non_empty(request.evidence_reference or ""),
        _non_empty(request.restore_reference or ""),
        _non_empty(request.policy_backup_reference or ""),
    ])

    if request.dry_run:
        if not _non_empty(request.plan_id): blockers.append("plan_id_required")
        if not _non_empty(request.idempotency_key): blockers.append("idempotency_key_required")
        if request.current_state not in _ALLOWED_STATES: blockers.append("current_state_invalid")
        if request.proposed_state not in _ALLOWED_STATES: blockers.append("proposed_state_invalid")
        return AbuseDBExecutionValidation(valid=not blockers, dry_run=True, execution_allowed=False, db_writes_allowed=False, blockers=blockers, hard_transition=hard_transition, operator_approval_complete=operator_approval_complete)

    if request.operator_confirmation != REQUIRED_CONFIRMATION: blockers.append("operator_confirmation_required")
    if request.request_source != ALLOWED_REQUEST_SOURCE: blockers.append("request_source_not_allowed")
    if request.evidence_status != "complete": blockers.append("evidence_not_complete")
    if not _non_empty(request.idempotency_key): blockers.append("idempotency_key_required")
    if not _non_empty(request.plan_id): blockers.append("plan_id_required")
    if request.customer_id <= 0: blockers.append("customer_id_invalid")
    if request.lane_id <= 0: blockers.append("lane_id_invalid")
    if request.port <= 0: blockers.append("port_invalid")
    if request.current_state not in _ALLOWED_STATES: blockers.append("current_state_invalid")
    if request.proposed_state not in _ALLOWED_STATES: blockers.append("proposed_state_invalid")
    if request.current_state == request.proposed_state: blockers.append("same_state_transition_blocked")
    if request.decision == "manual_unhard": blockers.append("manual_unhard_future_gated")
    if hard_transition and not operator_approval_complete: blockers.append("hard_transition_operator_approval_incomplete")

    allowed = not blockers
    return AbuseDBExecutionValidation(valid=allowed, dry_run=False, execution_allowed=allowed, db_writes_allowed=allowed, blockers=blockers, hard_transition=hard_transition, operator_approval_complete=operator_approval_complete)


def build_dry_run_execution_result(request: AbuseDBExecutionRequest, validation: AbuseDBExecutionValidation) -> AbuseDBExecutionResult:
    would_write = {
        "abuse_state": {"customer_id": request.customer_id, "lane_id": request.lane_id, "state": request.proposed_state},
        "abuse_event": {"customer_id": request.customer_id, "decision": request.decision, "plan_id": request.plan_id},
    }
    return AbuseDBExecutionResult(
        final_decision="BLOCKED" if not validation.execution_allowed else "ALLOWED",
        dry_run=request.dry_run,
        execution_allowed=validation.execution_allowed,
        db_writes_executed=False,
        abuse_state_written=False,
        abuse_event_written=False,
        idempotency_key=request.idempotency_key,
        plan_id=request.plan_id,
        current_state=request.current_state,
        proposed_state=request.proposed_state,
        decision=request.decision,
        blockers=list(validation.blockers),
        warnings=list(validation.warnings),
        would_write=would_write,
        written={},
    )
