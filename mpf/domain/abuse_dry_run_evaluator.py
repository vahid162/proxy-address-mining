from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AbusePolicySnapshot:
    miners: int
    farms: int
    maxconn: int
    rate_per_min: int
    burst: int
    abuse_exempt: bool = False
    abuse_exempt_reason: str | None = None
    abuse_exempt_until: datetime | None = None


@dataclass(frozen=True)
class AbuseEvidenceSnapshot:
    customer_id: int | None
    lane_id: int | None
    customer_key: str | None
    port: int
    active_sessions: int | None
    hot_sessions: int | None
    unique_source_ips: int | None
    unique_workers: int | None
    evidence_status: str
    evidence_source: str
    observed_at: datetime | None
    confidence: int
    missing_reasons: list[str]


@dataclass(frozen=True)
class AbuseStateSnapshot:
    status: str
    first_seen_over: datetime | None
    last_seen_over: datetime | None
    last_recovery_at: datetime | None
    hard_applied_at: datetime | None
    current_hot: int = 0
    current_unique_ips: int = 0
    current_unique_workers: int = 0


@dataclass(frozen=True)
class AbuseDryRunInput:
    policy: AbusePolicySnapshot
    evidence: AbuseEvidenceSnapshot
    state: AbuseStateSnapshot
    now: datetime
    threshold_seconds: int = 3600
    grace_seconds: int = 900


@dataclass
class AbuseDryRunResult:
    current_state: str; proposed_state: str; decision: str; final_decision: str
    dry_run: bool; execution_allowed: bool; transition_allowed: bool; hardening_allowed: bool
    would_transition: bool; would_harden: bool; miner_over: bool; farms_over: bool; worker_over: bool
    sustained_over_seconds: int; threshold_seconds: int; grace_seconds: int; evidence_status: str; evidence_complete: bool
    missing_reasons: list[str]; blockers: list[str]; warnings: list[str]; reason: str
    audit_event_required_future: bool; restore_reference_required_future: bool; policy_backup_required_future: bool
    firewall_apply_required_future: bool; conntrack_flush_required_future: bool


def evaluate_abuse_dry_run(inp: AbuseDryRunInput) -> AbuseDryRunResult:
    evidence_complete = inp.evidence.evidence_status == "complete"
    blockers = list(inp.evidence.missing_reasons)
    warnings: list[str] = []
    hot = inp.evidence.hot_sessions
    if hot is None and inp.evidence.active_sessions is not None:
        hot = inp.evidence.active_sessions
        warnings.append("hot_sessions_missing_active_sessions_fallback")
    if hot is None:
        blockers.append("missing_hot_and_active_sessions")
    miner_over = hot is not None and hot > inp.policy.miners
    farms_over = (inp.evidence.unique_source_ips or 0) > inp.policy.farms
    worker_over = (inp.evidence.unique_workers or 0) > inp.policy.miners
    if farms_over and not miner_over: warnings.append("farms_over_report_only")
    if worker_over and not miner_over: warnings.append("worker_over_report_only")

    res = AbuseDryRunResult(
        current_state=inp.state.status, proposed_state=inp.state.status, decision="stays_normal", final_decision="BLOCKED",
        dry_run=True, execution_allowed=False, transition_allowed=False, hardening_allowed=False,
        would_transition=False, would_harden=False, miner_over=miner_over, farms_over=farms_over, worker_over=worker_over,
        sustained_over_seconds=0, threshold_seconds=inp.threshold_seconds, grace_seconds=inp.grace_seconds,
        evidence_status=inp.evidence.evidence_status, evidence_complete=evidence_complete, missing_reasons=list(inp.evidence.missing_reasons),
        blockers=blockers, warnings=warnings, reason="dry_run_only", audit_event_required_future=False, restore_reference_required_future=False,
        policy_backup_required_future=False, firewall_apply_required_future=False, conntrack_flush_required_future=False,
    )

    if inp.policy.abuse_exempt and inp.policy.abuse_exempt_until and inp.policy.abuse_exempt_reason and inp.now <= inp.policy.abuse_exempt_until:
        res.decision = "exempt_report_only"; res.reason = "active_exemption"; return res
    if inp.policy.abuse_exempt and inp.policy.abuse_exempt_until and inp.now > inp.policy.abuse_exempt_until:
        res.warnings.append("expired_exemption_ignored")

    if inp.evidence.evidence_status in {"missing", "stale", "partial", "evaluation_blocked"} or blockers:
        res.blockers.append(f"evidence_{inp.evidence.evidence_status}_blocks_transition")
        res.decision = f"evaluation_blocked_{inp.evidence.evidence_status}"
        return res

    state = inp.state.status
    if state == "normal":
        if miner_over: res.proposed_state = "over_tracking"; res.would_transition = True; res.decision = "would_enter_over_tracking"
    elif state == "over_tracking":
        if miner_over:
            if not inp.state.first_seen_over: res.warnings.append("first_seen_over_missing"); res.decision = "tracking_without_hardening_due_missing_first_seen"
            else:
                elapsed = max(0, int((inp.now - inp.state.first_seen_over).total_seconds())); res.sustained_over_seconds = elapsed
                if elapsed >= inp.threshold_seconds:
                    res.proposed_state = "hard"; res.would_transition = True; res.would_harden = True; res.decision = "would_harden_after_sustained_miner_abuse"
                    res.audit_event_required_future = res.restore_reference_required_future = res.policy_backup_required_future = True
                    res.firewall_apply_required_future = res.conntrack_flush_required_future = True
                else: res.decision = "continues_over_tracking"
        else: res.proposed_state = "over_grace"; res.would_transition = True; res.decision = "would_enter_over_grace"
    elif state == "over_grace":
        if miner_over: res.proposed_state = "over_tracking"; res.would_transition = True; res.decision = "would_return_to_over_tracking"
        elif inp.state.last_recovery_at:
            elapsed = max(0, int((inp.now - inp.state.last_recovery_at).total_seconds())); res.sustained_over_seconds = elapsed
            if elapsed >= inp.grace_seconds: res.proposed_state = "normal"; res.would_transition = True; res.decision = "would_recover_normal"
            else: res.decision = "continues_over_grace"
        else: res.warnings.append("last_recovery_at_missing"); res.decision = "grace_without_recovery_timestamp"
    elif state == "hard":
        res.proposed_state = "hard"; res.decision = "hard_requires_manual_unhard_future_gated"
    else:
        res.blockers.append("unknown_abuse_state"); res.decision = "evaluation_blocked_unknown_state"
    return res
