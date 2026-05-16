from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AbuseWorkerPreAcceptanceContract:
    package_name: str
    worker_execution_allowed_in_this_pr: bool
    scheduler_allowed_in_this_pr: bool
    timer_allowed_in_this_pr: bool
    abuse_runner_allowed_in_this_pr: bool
    real_customer_evaluation_allowed_in_this_pr: bool
    production_db_execution_allowed_in_this_pr: bool
    db_reads_allowed_in_this_pr: bool
    db_writes_allowed_in_this_pr: bool
    firewall_mutation_allowed_in_this_pr: bool
    customer_mutation_allowed_in_this_pr: bool
    hard_block_allowed_in_this_pr: bool
    soft_block_allowed_in_this_pr: bool
    pause_automation_allowed_in_this_pr: bool
    phase8_acceptance_allowed_in_this_pr: bool
    required_before_worker_dry_run: list[str]
    required_operator_approvals: list[str]
    required_sync_evidence: list[str]
    required_kill_switches: list[str]
    required_locks: list[str]
    required_reports: list[str]
    forbidden_actions: list[str]


@dataclass(frozen=True)
class AbuseWorkerPreAcceptanceInput:
    latest_recorded_farm5_sync_evidence: str
    repository_version: str
    previous_reports_fail_closed: bool
    worker_harness_present: bool
    runtime_worker_readiness_present: bool
    operator_approval_present: bool
    kill_switch_present: bool
    lock_contract_present: bool
    no_silent_skip_contract_present: bool
    fresh_sync_required: bool


@dataclass
class AbuseWorkerPreAcceptanceResult:
    final_decision: str
    pre_acceptance_status: str
    execution_allowed: bool
    phase8_acceptance_allowed: bool
    controlled_worker_dry_run_allowed_now: bool
    farm5_sync_required_before_worker_dry_run: bool
    operator_approval_required: bool
    blockers: list[str]
    warnings: list[str]
    required_next_steps: list[str]


def _version_tuple(v: str) -> tuple[int, ...]:
    parts = v.strip().split(".")
    return tuple(int(p) for p in parts if p.isdigit())


def build_abuse_worker_pre_acceptance_contract() -> AbuseWorkerPreAcceptanceContract:
    return AbuseWorkerPreAcceptanceContract(
        package_name="phase8_controlled_worker_pre_acceptance",
        worker_execution_allowed_in_this_pr=False,
        scheduler_allowed_in_this_pr=False,
        timer_allowed_in_this_pr=False,
        abuse_runner_allowed_in_this_pr=False,
        real_customer_evaluation_allowed_in_this_pr=False,
        production_db_execution_allowed_in_this_pr=False,
        db_reads_allowed_in_this_pr=False,
        db_writes_allowed_in_this_pr=False,
        firewall_mutation_allowed_in_this_pr=False,
        customer_mutation_allowed_in_this_pr=False,
        hard_block_allowed_in_this_pr=False,
        soft_block_allowed_in_this_pr=False,
        pause_automation_allowed_in_this_pr=False,
        phase8_acceptance_allowed_in_this_pr=False,
        required_before_worker_dry_run=["fresh_farm5_sync_evidence", "operator_approval", "kill_switch", "lock_contract", "no_silent_skip_contract"],
        required_operator_approvals=["operator_approval_required"],
        required_sync_evidence=["farm5_sync_0_1_116", "farm5_sync_0_1_117", "farm5_sync_0_1_118"],
        required_kill_switches=["global_kill_switch_required"],
        required_locks=["worker_lock_required"],
        required_reports=["state_machine", "evidence_reporting", "dry_run_evaluator", "db_transition_readiness", "db_transition_execution", "runtime_worker_readiness", "runtime_worker_dry_run_harness"],
        forbidden_actions=["start_worker", "enable_scheduler", "enable_timer", "run_abuse_runner", "evaluate_real_customers", "execute_production_db", "mutate_firewall", "mutate_customers", "apply_hard_soft_block", "apply_pause_automation"],
    )


def evaluate_abuse_worker_pre_acceptance(input: AbuseWorkerPreAcceptanceInput) -> AbuseWorkerPreAcceptanceResult:
    blockers: list[str] = []
    warnings: list[str] = []

    sync_required = _version_tuple(input.repository_version) > _version_tuple(input.latest_recorded_farm5_sync_evidence)
    if sync_required:
        blockers.append("fresh_farm5_sync_required_before_worker_dry_run")

    if not input.previous_reports_fail_closed:
        blockers.append("previous_fail_closed_reports_missing")
    if not input.worker_harness_present:
        blockers.append("worker_harness_missing")
    if not input.runtime_worker_readiness_present:
        blockers.append("runtime_worker_readiness_missing")
    if not input.kill_switch_present:
        blockers.append("kill_switch_contract_missing")
    if not input.lock_contract_present:
        blockers.append("lock_contract_missing")
    if not input.no_silent_skip_contract_present:
        blockers.append("no_silent_skip_contract_missing")
    if not input.operator_approval_present:
        blockers.append("operator_approval_missing")

    if input.fresh_sync_required and not sync_required:
        warnings.append("fresh_sync_required_flag_set_without_version_delta")

    return AbuseWorkerPreAcceptanceResult(
        final_decision="BLOCKED",
        pre_acceptance_status="CONTROLLED_WORKER_PRE_ACCEPTANCE_DEFINED_NOT_ACCEPTED",
        execution_allowed=False,
        phase8_acceptance_allowed=False,
        controlled_worker_dry_run_allowed_now=False,
        farm5_sync_required_before_worker_dry_run=sync_required,
        operator_approval_required=True,
        blockers=blockers,
        warnings=warnings,
        required_next_steps=["batch_farm5_sync_0_1_116_0_1_117_0_1_118", "collect_farm5_test_evidence", "separate_controlled_worker_dry_run_pr", "operator_approval_before_worker_dry_run"],
    )
