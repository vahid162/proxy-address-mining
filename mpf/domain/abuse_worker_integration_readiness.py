from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AbuseWorkerReadinessContract:
    worker_name: str
    enabled_by_default: bool
    scheduler_enabled_by_default: bool
    runtime_execution_allowed: bool
    real_customer_evaluation_allowed: bool
    production_db_execution_allowed: bool
    firewall_mutation_allowed: bool
    customer_mutation_allowed: bool
    required_gates: list[str]
    required_kill_switches: list[str]
    required_locks: list[str]
    required_observability: list[str]
    forbidden_actions: list[str]


@dataclass(frozen=True)
class AbuseWorkerLoopContract:
    loop_name: str
    allowed_modes: list[str]
    default_mode: str
    max_batch_size: int
    lock_required: bool
    idempotency_required: bool
    dry_run_first_required: bool
    manual_enable_required: bool
    production_enable_allowed_in_this_pr: bool


@dataclass(frozen=True)
class AbuseWorkerFailureModeContract:
    failure: str
    action: str
    harden_allowed: bool
    db_write_allowed: bool
    retry_allowed: bool
    operator_review_required: bool


def build_abuse_worker_readiness_contract() -> AbuseWorkerReadinessContract:
    return AbuseWorkerReadinessContract(
        worker_name="phase8_abuse_worker",
        enabled_by_default=False,
        scheduler_enabled_by_default=False,
        runtime_execution_allowed=False,
        real_customer_evaluation_allowed=False,
        production_db_execution_allowed=False,
        firewall_mutation_allowed=False,
        customer_mutation_allowed=False,
        required_gates=["phase7_accepted", "phase8_runtime_worker_future_gate", "fresh_farm5_sync_evidence"],
        required_kill_switches=["abuse_worker_global_disable", "abuse_worker_runtime_disable", "abuse_worker_pause_switch"],
        required_locks=["abuse_worker_loop_lock", "abuse_worker_customer_lock", "abuse_worker_idempotency_guard"],
        required_observability=["worker_loop_cycle_report", "explicit_skip_report", "failure_mode_report", "operator_ack_audit"],
        forbidden_actions=[
            "start_worker_by_default",
            "enable_scheduler_by_default",
            "evaluate_real_customers",
            "execute_production_db_transitions",
            "mutate_firewall",
            "mutate_customer_nat_or_rules",
            "start_abuse_runner",
            "apply_hard_or_soft_block",
            "apply_pause_automation",
            "enable_production_traffic",
        ],
    )


def build_abuse_worker_loop_contract() -> AbuseWorkerLoopContract:
    return AbuseWorkerLoopContract(
        loop_name="phase8_runtime_worker_loop",
        allowed_modes=["report_only", "dry_run"],
        default_mode="report_only",
        max_batch_size=100,
        lock_required=True,
        idempotency_required=True,
        dry_run_first_required=True,
        manual_enable_required=True,
        production_enable_allowed_in_this_pr=False,
    )


def build_abuse_worker_failure_modes() -> list[AbuseWorkerFailureModeContract]:
    return [
        AbuseWorkerFailureModeContract("missing_evidence", "emit_missing_evidence_report_and_skip", False, False, False, True),
        AbuseWorkerFailureModeContract("stale_evidence", "emit_stale_evidence_report_and_skip", False, False, False, True),
        AbuseWorkerFailureModeContract("db_failure", "emit_db_failure_report_and_skip", False, False, True, True),
        AbuseWorkerFailureModeContract("firewall_failure", "emit_firewall_failure_report_and_skip", False, False, True, True),
        AbuseWorkerFailureModeContract("lock_contention", "emit_lock_contention_explicit_skip_report", False, False, True, False),
        AbuseWorkerFailureModeContract("no_work", "emit_no_work_explicit_skip_report", False, False, False, False),
    ]
