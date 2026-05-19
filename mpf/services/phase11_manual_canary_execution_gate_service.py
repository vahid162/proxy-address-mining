from __future__ import annotations

from mpf.domain.production import ManualCanaryExecutionGateRequest

REQUIRED_FIELDS = (
    "require_farm5_0_1_147_evidence",
    "require_phase11d_package_evidence",
    "require_latest_main_sync_before_execution",
    "require_backup_reference",
    "require_restore_plan_reference",
    "require_rollback_plan",
    "require_no_customer_nat_baseline",
    "require_no_customer_firewall_baseline",
    "require_local_only_runtime_baseline",
    "require_firewall_plan_review",
    "require_abuse_coverage_check",
    "require_usage_visibility_check",
    "require_reject_visibility_check",
    "require_session_worker_visibility_check",
    "require_check_report_verdict",
)


def build_phase11_manual_canary_execution_gate_report(request: ManualCanaryExecutionGateRequest) -> dict[str, object]:
    validation_errors = request.validate()
    if any(not getattr(request, field) for field in REQUIRED_FIELDS):
        validation_errors.append("all execution gate requirement toggles must remain true")

    ready = not validation_errors and request.requested_action == "gate"
    return {
        "component": "phase11_manual_canary_execution_gate",
        "phase": "Phase 11D — Manual canary execution gate package",
        "final_decision": "READY_FOR_FARM5_SYNC_EVIDENCE" if ready else "BLOCKED",
        "authorization_status": "MANUAL_CANARY_EXECUTION_GATE_NON_AUTHORIZING",
        "execution_allowed": False,
        "actual_canary_execution_performed": False,
        "mutation_performed": False,
        "customer_db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "production_traffic_enabled": False,
        "request": request.as_dict(),
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
            "farm5_0_1_147_sync_evidence_recorded": True,
            "phase11a_evidence_recorded": True,
            "phase11b_evidence_recorded": True,
            "phase11c_evidence_recorded": True,
            "phase11d_package_evidence_recorded": True,
            "latest_main_sync_required_before_execution": True,
            "no_farm5_execution_evidence_claimed": True,
        },
        "future_execution_preflight": [
            "verify mpf --version", "verify mpf phase-status", "verify mpf config validate", "verify mpf doctor", "verify mpf db status", "verify mpf proxy doctor",
            "verify mpf production readiness --output json", "verify mpf production canary-plan --output json", "verify mpf production activation-harness --output json",
            "verify mpf production canary-acceptance --output json", "verify mpf production canary-execution-gate --output json", "verify no MPF/customer NAT redirects",
            "verify no MPF/customer firewall rules", "verify accepted listeners are local-only", "verify backup/restore/rollback plan before any future apply",
        ],
        "future_execution_plan_preview": [
            "would create/select one canary customer under later explicit execution run", "would generate/review firewall plan before apply", "would create restore point before apply",
            "would create iptables-save backup before apply", "would acquire lock before apply", "would apply only through accepted planner/apply service path", "would verify after apply",
            "would test canary connection", "would verify NAT hit", "would verify usage/reject visibility", "would verify session/worker visibility", "would verify abuse coverage",
            "would generate rollback/restore evidence", "would collect farm5 canary execution evidence", "would not permit limited real onboarding until canary evidence is accepted",
        ],
        "safety_flags": {k: False for k in (
            "production_traffic_authorized", "controlled_cli_canary_execution_authorized", "limited_customer_onboarding_authorized", "customer_db_mutation_authorized",
            "firewall_apply_authorized", "iptables_restore_authorized", "customer_nat_apply_authorized", "customer_firewall_rules_apply_authorized", "abuse_automation_authorized",
            "conntrack_flush_authorized", "worker_enforcement_authorized", "scheduler_authorized", "collector_authorized", "ui_authorized", "telegram_authorized",
        )},
        "operator_checklist": [
            "sync latest GitHub main to farm5", "run full server evidence commands", "review gate output",
            "do not execute canary until a separate operator-approved execution run", "collect all output for review",
        ],
        "blockers": [
            "farm5 sync/test evidence required after merge", "actual manual canary execution remains forbidden until later explicit execution run",
            "firewall apply remains forbidden in this PR", "customer NAT/customer firewall rules remain preview-only in this PR",
            "customer DB mutation remains forbidden in this PR", "production traffic remains none", "abuse automation remains forbidden",
            "limited real customer onboarding remains forbidden",
        ],
        "statements": [
            "Phase 11D execution is still not authorized by this PR.",
            "The actual canary execution requires a later farm5 execution run with operator approval.",
            "Farm5 must be synced to latest main before any future execution.",
            "The future canary execution must be one explicit canary only.",
            "No limited real customer onboarding is allowed before successful manual canary evidence.",
            "Phase 11 final acceptance is still later.",
        ],
        "validation_errors": validation_errors,
    }
