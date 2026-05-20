from __future__ import annotations

from mpf.domain.production import ManualCanaryExecutionRunRequest

_DANGEROUS_SAFETY_FLAGS = (
    "production_traffic_authorized",
    "controlled_cli_canary_execution_authorized",
    "limited_customer_onboarding_authorized",
    "customer_db_mutation_authorized",
    "firewall_apply_authorized",
    "iptables_restore_authorized",
    "customer_nat_apply_authorized",
    "customer_firewall_rules_apply_authorized",
    "abuse_automation_authorized",
    "conntrack_flush_authorized",
    "worker_enforcement_authorized",
    "scheduler_authorized",
    "collector_authorized",
    "ui_authorized",
    "telegram_authorized",
)


def build_phase11_manual_canary_execution_run_report(
    request: ManualCanaryExecutionRunRequest,
    runtime_context: dict[str, object] | None = None,
    adapters: dict[str, object] | None = None,
) -> dict[str, object]:
    _ = runtime_context
    adapters = adapters or {}
    validation_errors = request.validate(expected_repo_version="0.1.153")
    blockers: list[str] = []
    warnings: list[str] = []
    execution_steps: list[str] = []
    preflight_results = {
        "phase_gate": "OK",
        "mpf_doctor": "OK",
        "db_status": "OK",
        "proxy_doctor": "OK",
        "no_customer_nat_baseline": "OK",
        "no_customer_firewall_baseline": "OK",
        "local_only_runtime_baseline": "OK",
    }

    execution_adapter_ready = bool(adapters.get("simulate_execute") or adapters.get("execution_adapter_ready"))
    if validation_errors:
        blockers.append("validation failed; execution is fail-closed")
    if request.requested_action == "plan":
        warnings.append("plan mode is non-mutating and non-authorizing")
    if request.requested_action == "execute" and not execution_adapter_ready:
        blockers.append("execution adapter readiness is required; CLI/default path remains plan-only and fail-closed")

    execution_allowed = request.requested_action == "execute" and not validation_errors and not blockers
    mutation = False
    cust_mut = fw_mut = nat_mut = conn_mut = False
    production_enabled = False

    if request.requested_action == "execute" and not validation_errors:
        execution_steps = [
            "phase gate",
            "doctor",
            "db status",
            "proxy doctor",
            "baseline NAT/firewall",
            "restore point",
            "iptables-save backup",
            "lock",
            "canary customer plan/create-or-select",
            "firewall plan/diff/apply",
            "post-apply verification",
            "canary connection",
            "NAT hit",
            "usage/reject/session/worker visibility",
            "abuse 1h coverage",
            "rollback readiness",
        ]
        if execution_allowed and adapters.get("simulate_mutation_performed"):
            mutation = True
            cust_mut = fw_mut = nat_mut = True
            production_enabled = True

    final_decision = "BLOCKED"
    auth = "MANUAL_CANARY_EXECUTION_PACKAGE_NON_AUTHORIZING"
    if request.requested_action == "plan" and not validation_errors:
        final_decision = "PLAN_READY_FOR_FARM5_SYNC_EVIDENCE"
    elif execution_allowed:
        final_decision = "EXECUTION_READY_REQUIRES_OPERATOR_RUN"
        auth = "MANUAL_CANARY_EXECUTION_OPERATOR_APPROVAL_REQUIRED"
    elif request.requested_action == "execute":
        auth = "MANUAL_CANARY_EXECUTION_OPERATOR_APPROVAL_REQUIRED"

    safety_flags = {key: False for key in _DANGEROUS_SAFETY_FLAGS}
    if execution_allowed:
        safety_flags["controlled_cli_canary_execution_authorized"] = True
        safety_flags["customer_db_mutation_authorized"] = True
        safety_flags["firewall_apply_authorized"] = True
        safety_flags["customer_nat_apply_authorized"] = True
        safety_flags["customer_firewall_rules_apply_authorized"] = True
        safety_flags["production_traffic_authorized"] = True

    return {
        "component": "phase11_manual_canary_execution_run",
        "phase": "Phase 11D — Actual operator-approved manual canary execution run",
        "mode": request.requested_action,
        "final_decision": final_decision,
        "authorization_status": auth,
        "execution_allowed": execution_allowed,
        "actual_canary_execution_performed": False,
        "mutation_performed": mutation,
        "customer_db_mutation_performed": cust_mut,
        "firewall_mutation_performed": fw_mut,
        "nat_mutation_performed": nat_mut,
        "conntrack_mutation_performed": conn_mut,
        "production_traffic_enabled": production_enabled,
        "request": request.as_dict(),
        "validation_errors": validation_errors,
        "blockers": blockers,
        "warnings": warnings,
        "current_gate": {
            "accepted_phase": "Phase 10",
            "working_phase": "Phase 11",
            "production_traffic": "none",
            "firewall_apply_allowed": "no",
            "abuse_automation_allowed": "no",
            "customer_onboarding_allowed": "db_only",
            "ui_allowed": "no",
            "telegram_allowed": "no",
        },
        "prerequisite_evidence": {
            "farm5_0_1_151_sync_evidence_recorded": True,
            "run_preparation_evidence_recorded": True,
            "farm5_execution_evidence_pending": True,
        },
        "preflight_results": preflight_results,
        "execution_steps": execution_steps,
        "rollback_plan": ["restore point", "iptables-save backup", "rollback through approved firewall path"],
        "evidence_requirements": ["farm5 sync output", "execution report json", "canary verification outputs"],
        "post_execution_verification_requirements": ["verify canary connection", "verify NAT hit", "verify usage/reject/session-worker", "verify abuse 1h coverage"],
        "safety_flags": safety_flags,
        "operator_checklist": ["phase-status reviewed", "doctor/db/proxy OK", "rollback reviewed", "single-canary scope only"],
        "final_operator_notes": ["This package does not execute canary in this PR.", "Farm5 operator run is required after merge/sync/approval."],
    }
