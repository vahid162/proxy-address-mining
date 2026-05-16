from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class AbuseWorkerDryRunItem:
    item_id: str
    customer_id: int | None
    lane_id: int | None
    customer_key: str | None
    port: int
    current_state: str
    synthetic_evidence_status: str
    synthetic_decision_hint: str
    should_simulate_lock_contention: bool = False
    should_simulate_duplicate_idempotency: bool = False
    should_simulate_kill_switch: bool = False
    should_simulate_db_failure: bool = False
    should_simulate_firewall_failure: bool = False


@dataclass(frozen=True)
class AbuseWorkerDryRunCycleInput:
    cycle_id: str
    mode: str
    now_iso: str
    items: list[AbuseWorkerDryRunItem]
    global_kill_switch_enabled: bool
    worker_enabled: bool
    scheduler_enabled: bool
    max_batch_size: int
    lock_name: str


@dataclass
class AbuseWorkerDryRunItemResult:
    item_id: str
    customer_id: int | None
    lane_id: int | None
    port: int
    status: str
    action: str
    skipped: bool
    skip_reason: str | None
    evaluated: bool
    would_transition: bool
    would_harden: bool
    db_execution_attempted: bool
    db_execution_allowed: bool
    db_write_executed: bool
    firewall_action_attempted: bool
    firewall_action_allowed: bool
    hard_block_attempted: bool
    hard_block_allowed: bool
    pause_attempted: bool
    pause_allowed: bool
    warnings: list[str]
    blockers: list[str]


@dataclass
class AbuseWorkerDryRunCycleResult:
    cycle_id: str
    final_decision: str
    mode: str
    dry_run: bool
    execution_allowed: bool
    worker_started: bool
    scheduler_started: bool
    runtime_worker_authorized: bool
    scheduler_authorized: bool
    abuse_runner_authorized: bool
    production_db_execution_authorized: bool
    real_customer_evaluation_authorized: bool
    lock_acquired: bool
    lock_released: bool
    global_kill_switch_respected: bool
    total_items: int
    evaluated_items: int
    skipped_items: int
    no_work: bool
    no_silent_skip: bool
    item_results: list[AbuseWorkerDryRunItemResult]
    blockers: list[str]
    warnings: list[str]
    summary: dict[str, object]


def build_worker_dry_run_cycle_id(seed: str, now_iso: str) -> str:
    return f"wdrh-{sha256(f'{seed}:{now_iso}'.encode()).hexdigest()[:16]}"


def _base_result(item: AbuseWorkerDryRunItem) -> AbuseWorkerDryRunItemResult:
    return AbuseWorkerDryRunItemResult(item_id=item.item_id, customer_id=item.customer_id, lane_id=item.lane_id, port=item.port, status="SKIPPED", action="none", skipped=True, skip_reason=None, evaluated=False, would_transition=False, would_harden=False, db_execution_attempted=False, db_execution_allowed=False, db_write_executed=False, firewall_action_attempted=False, firewall_action_allowed=False, hard_block_attempted=False, hard_block_allowed=False, pause_attempted=False, pause_allowed=False, warnings=[], blockers=[])


def evaluate_worker_dry_run_cycle(input: AbuseWorkerDryRunCycleInput) -> AbuseWorkerDryRunCycleResult:
    items = list(input.items)
    results: list[AbuseWorkerDryRunItemResult] = []
    blockers: list[str] = []
    warnings: list[str] = []

    if input.scheduler_enabled:
        blockers.append("scheduler_enabled_not_allowed_in_this_pr")
        for item in items:
            r = _base_result(item); r.skip_reason = "scheduler_enabled"; results.append(r)
    elif not input.worker_enabled:
        for item in items:
            r = _base_result(item); r.skip_reason = "worker_disabled"; results.append(r)
    elif input.global_kill_switch_enabled:
        for item in items:
            r = _base_result(item); r.skip_reason = "global_kill_switch"; results.append(r)
    else:
        work_items = items[: max(input.max_batch_size, 0)]
        overflow = items[max(input.max_batch_size, 0):]
        for item in overflow:
            r = _base_result(item); r.skip_reason = "batch_limit"; results.append(r)
        for item in work_items:
            r = _base_result(item)
            if item.should_simulate_lock_contention:
                r.skip_reason = "lock_contention"; results.append(r); continue
            if item.should_simulate_duplicate_idempotency:
                r.skip_reason = "duplicate_idempotency"; results.append(r); continue
            if item.should_simulate_kill_switch:
                r.skip_reason = "item_kill_switch"; results.append(r); continue
            if item.synthetic_evidence_status in {"missing", "stale", "partial", "evaluation_blocked"}:
                r.skip_reason = item.synthetic_evidence_status
                r.status = "BLOCKED_EVIDENCE"
                results.append(r)
                continue
            if item.should_simulate_db_failure:
                r.status = "BLOCKED_FAILURE"; r.skip_reason = "db_failure"; r.blockers.append("db_failure"); results.append(r); continue
            if item.should_simulate_firewall_failure:
                r.status = "BLOCKED_FAILURE"; r.skip_reason = "firewall_failure"; r.blockers.append("firewall_failure"); results.append(r); continue
            r.skipped = False; r.evaluated = True; r.status = "EVALUATED"; r.action = "report_only"
            hint = item.synthetic_decision_hint
            if hint == "normal":
                pass
            elif hint == "miner_over":
                r.would_transition = True
            elif hint == "sustained_hard":
                r.would_transition = True; r.would_harden = True
            elif hint == "farms_over_only":
                r.warnings.append("farms_over_report_only")
            elif hint == "worker_over_only":
                r.warnings.append("worker_over_report_only")
            else:
                r.blockers.append("unknown_synthetic_decision_hint")
                r.status = "BLOCKED_HINT"
            results.append(r)

    evaluated = sum(1 for r in results if r.evaluated)
    skipped = sum(1 for r in results if r.skipped)
    no_work = len(items) == 0
    no_silent_skip = all((not r.skipped) or (r.skip_reason is not None) for r in results)
    return AbuseWorkerDryRunCycleResult(
        cycle_id=input.cycle_id, final_decision="BLOCKED", mode=input.mode, dry_run=True, execution_allowed=False,
        worker_started=False, scheduler_started=False, runtime_worker_authorized=False, scheduler_authorized=False,
        abuse_runner_authorized=False, production_db_execution_authorized=False, real_customer_evaluation_authorized=False,
        lock_acquired=not input.scheduler_enabled, lock_released=not input.scheduler_enabled,
        global_kill_switch_respected=input.global_kill_switch_enabled, total_items=len(items), evaluated_items=evaluated,
        skipped_items=skipped, no_work=no_work, no_silent_skip=no_silent_skip, item_results=results, blockers=blockers,
        warnings=warnings, summary={"cycle_id": input.cycle_id, "mode": input.mode, "evaluated_items": evaluated, "skipped_items": skipped, "no_work": no_work},
    )
