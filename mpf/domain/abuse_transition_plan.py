from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class AbuseTransitionIntent:
    customer_id: int | None
    lane_id: int | None
    customer_key: str | None
    port: int
    current_state: str
    proposed_state: str
    decision: str
    would_transition: bool
    would_harden: bool
    transition_allowed: bool
    hardening_allowed: bool
    dry_run: bool
    evidence_status: str
    evidence_source: str
    observed_at_iso: str | None
    sustained_over_seconds: int
    threshold_seconds: int
    grace_seconds: int
    reason: str
    blockers: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class AbuseDBMutationPlan:
    plan_id: str
    idempotency_key: str
    customer_id: int | None
    lane_id: int | None
    port: int
    current_state: str
    proposed_state: str
    writes_allowed: bool
    execution_allowed: bool
    would_write_abuse_state: bool
    would_write_abuse_event: bool
    would_require_policy_backup: bool
    would_require_restore_reference: bool
    would_require_audit_event: bool
    would_require_operator_approval: bool
    future_write_tables: list[str]
    blocked_reason: str
    blockers: list[str]
    warnings: list[str]
    audit_payload: dict[str, object]
    restore_reference_payload: dict[str, object]
    evidence_payload: dict[str, object]


@dataclass(frozen=True)
class AbuseOperatorApprovalContract:
    required: bool
    required_for_states: list[str]
    required_fields: list[str]
    approval_allowed_in_this_pr: bool
    execution_allowed_in_this_pr: bool


def _as_dict(obj: object) -> dict[str, object]:
    keys = ["current_state","proposed_state","decision","would_transition","would_harden","transition_allowed","hardening_allowed","dry_run","evidence_status","sustained_over_seconds","threshold_seconds","grace_seconds","reason","blockers","warnings"]
    data = {k: getattr(obj, k) for k in keys if hasattr(obj, k)}
    if hasattr(obj, "__dict__"):
        data.update(dict(getattr(obj, "__dict__")))
    return data


def build_transition_intent_from_dry_run_result(*, customer_id: int | None, lane_id: int | None, customer_key: str | None, port: int, evidence_source: str, observed_at_iso: str | None, dry_run_result: object) -> AbuseTransitionIntent:
    data = _as_dict(dry_run_result)
    return AbuseTransitionIntent(
        customer_id=customer_id,
        lane_id=lane_id,
        customer_key=customer_key,
        port=port,
        current_state=str(data.get("current_state", "unknown")),
        proposed_state=str(data.get("proposed_state", "unknown")),
        decision=str(data.get("decision", "evaluation_blocked")),
        would_transition=bool(data.get("would_transition", False)),
        would_harden=bool(data.get("would_harden", False)),
        transition_allowed=bool(data.get("transition_allowed", False)),
        hardening_allowed=bool(data.get("hardening_allowed", False)),
        dry_run=bool(data.get("dry_run", True)),
        evidence_status=str(data.get("evidence_status", "missing")),
        evidence_source=evidence_source,
        observed_at_iso=observed_at_iso,
        sustained_over_seconds=int(data.get("sustained_over_seconds", 0)),
        threshold_seconds=int(data.get("threshold_seconds", 3600)),
        grace_seconds=int(data.get("grace_seconds", 900)),
        reason=str(data.get("reason", "dry_run_only")),
        blockers=list(data.get("blockers", [])),
        warnings=list(data.get("warnings", [])),
    )


def _build_idempotency_key(intent: AbuseTransitionIntent) -> str:
    base = {
        "customer_id": intent.customer_id,
        "lane_id": intent.lane_id,
        "port": intent.port,
        "current_state": intent.current_state,
        "proposed_state": intent.proposed_state,
        "decision": intent.decision,
        "observed_at_iso": intent.observed_at_iso,
        "evidence_source": intent.evidence_source,
    }
    return sha256(json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def build_db_mutation_plan(intent: AbuseTransitionIntent) -> AbuseDBMutationPlan:
    evidence_blocked = intent.evidence_status in {"missing", "stale", "partial", "evaluation_blocked"}
    blocked_reason = "execution_blocked"
    would_write = intent.would_transition
    if intent.current_state == intent.proposed_state and not intent.would_transition:
        blocked_reason = "no_state_change"
        would_write = False
    elif evidence_blocked:
        blocked_reason = "evidence_not_eligible"
        would_write = False
    elif intent.blockers:
        blocked_reason = "blockers_present"
        would_write = False

    future_tables = ["abuse_states", "abuse_events"] if would_write else []
    would_require_operator_approval = intent.would_harden or intent.proposed_state == "hard"
    idempotency_key = _build_idempotency_key(intent)
    plan_id = f"plan_{idempotency_key[:24]}"

    return AbuseDBMutationPlan(
        plan_id=plan_id,
        idempotency_key=idempotency_key,
        customer_id=intent.customer_id,
        lane_id=intent.lane_id,
        port=intent.port,
        current_state=intent.current_state,
        proposed_state=intent.proposed_state,
        writes_allowed=False,
        execution_allowed=False,
        would_write_abuse_state=would_write,
        would_write_abuse_event=would_write,
        would_require_policy_backup=intent.would_harden,
        would_require_restore_reference=intent.would_harden,
        would_require_audit_event=intent.would_harden,
        would_require_operator_approval=would_require_operator_approval,
        future_write_tables=future_tables,
        blocked_reason=blocked_reason,
        blockers=list(intent.blockers),
        warnings=list(intent.warnings),
        audit_payload={
            "current_state": intent.current_state,
            "proposed_state": intent.proposed_state,
            "decision": intent.decision,
            "reason": intent.reason,
            "evidence_status": intent.evidence_status,
            "sustained_over_seconds": intent.sustained_over_seconds,
        },
        restore_reference_payload={"required": intent.would_harden, "state": intent.proposed_state if intent.would_harden else "none"},
        evidence_payload={"source": intent.evidence_source, "status": intent.evidence_status, "observed_at_iso": intent.observed_at_iso},
    )


def build_operator_approval_contract() -> AbuseOperatorApprovalContract:
    return AbuseOperatorApprovalContract(
        required=True,
        required_for_states=["hard", "manual_unhard"],
        required_fields=["operator_id", "reason", "evidence_reference", "restore_reference", "policy_backup_reference", "approved_at"],
        approval_allowed_in_this_pr=False,
        execution_allowed_in_this_pr=False,
    )
