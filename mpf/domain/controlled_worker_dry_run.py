from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ControlledWorkerDryRunInput:
    repository_version: str
    latest_recorded_farm5_sync_evidence: str
    operator_confirmed: bool
    explicit_dry_run: bool
    batch_limit: int
    kill_switch_enabled: bool
    lock_acquired: bool
    no_real_customers: bool
    no_db_writes: bool
    no_firewall_mutation: bool
    no_customer_mutation: bool
    no_production_traffic: bool


@dataclass(frozen=True)
class ControlledWorkerDryRunItem:
    item_id: str
    lane: str
    customer_ref: str
    simulated_state_before: str
    simulated_observation: str
    simulated_state_after: str
    action: str
    reason: str
    would_write_db: bool
    would_mutate_firewall: bool
    would_mutate_customer: bool
    would_touch_production_traffic: bool


@dataclass(frozen=True)
class ControlledWorkerDryRunResult:
    final_decision: str
    dry_run_status: str
    execution_allowed: bool
    production_side_effects_allowed: bool
    phase8_acceptance_allowed: bool
    operator_invoked_only: bool
    scheduler_allowed: bool
    timer_allowed: bool
    abuse_runner_allowed: bool
    real_customer_evaluation_allowed: bool
    db_writes_allowed: bool
    firewall_mutation_allowed: bool
    customer_mutation_allowed: bool
    production_traffic_allowed: bool
    items: List[ControlledWorkerDryRunItem]
    blockers: List[str]
    warnings: List[str]
    required_next_steps: List[str]


def build_controlled_worker_dry_run_synthetic_items() -> list[ControlledWorkerDryRunItem]:
    scenarios = ["no_work","lock_contention","normal_stays_normal","over_tracking_observed_but_no_hard","over_grace_observed_but_no_hard","hard_candidate_reported_but_not_applied","stale_evidence_skipped","missing_evidence_skipped","db_failure_reported_no_write","firewall_failure_reported_no_mutation","idempotency_duplicate_skipped"]
    return [ControlledWorkerDryRunItem(s,"BTC",f"synthetic-{i}","before","observation","after","report_only",s,False,False,False,False) for i,s in enumerate(scenarios,1)]


def evaluate_controlled_worker_dry_run(input: ControlledWorkerDryRunInput, items: list[ControlledWorkerDryRunItem] | None = None) -> ControlledWorkerDryRunResult:
    work_items = items or build_controlled_worker_dry_run_synthetic_items()
    blockers: list[str] = []
    if input.repository_version > input.latest_recorded_farm5_sync_evidence:
        blockers.append("fresh_farm5_sync_test_required_before_evidence_collection")
    if not input.explicit_dry_run:
        blockers.append("explicit_dry_run_required")
    if not input.operator_confirmed:
        blockers.append("operator_confirmation_required")
    if input.batch_limit <= 0 or input.batch_limit > 10:
        blockers.append("batch_limit_out_of_range")
    if not input.kill_switch_enabled:
        blockers.append("kill_switch_must_be_enabled")
    if not input.lock_acquired:
        blockers.append("lock_acquisition_required")
    if not input.no_real_customers:
        blockers.append("real_customer_evaluation_disallowed")
    if not input.no_db_writes:
        blockers.append("db_writes_disallowed")
    if not input.no_firewall_mutation:
        blockers.append("firewall_mutation_disallowed")
    if not input.no_customer_mutation:
        blockers.append("customer_mutation_disallowed")
    if not input.no_production_traffic:
        blockers.append("production_traffic_disallowed")
    return ControlledWorkerDryRunResult(
        final_decision="BLOCKED" if blockers else "DRY_RUN_ONLY",
        dry_run_status="CONTROLLED_WORKER_DRY_RUN_SYNTHETIC_ONLY",
        execution_allowed=False, production_side_effects_allowed=False, phase8_acceptance_allowed=False,
        operator_invoked_only=True, scheduler_allowed=False, timer_allowed=False, abuse_runner_allowed=False,
        real_customer_evaluation_allowed=False, db_writes_allowed=False, firewall_mutation_allowed=False,
        customer_mutation_allowed=False, production_traffic_allowed=False, items=work_items, blockers=blockers,
        warnings=[], required_next_steps=["sync_test_0_1_120_on_farm5_before_future_evidence_collection"],
    )
