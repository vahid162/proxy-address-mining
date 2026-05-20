from __future__ import annotations

from mpf.domain.production import ManualCanaryExecutionRunPreparationRequest

REQUIRED_FIELDS = (
    "require_farm5_0_1_149_evidence",
    "require_execution_gate_evidence",
    "require_latest_main_sync_before_execution",
    "require_phase_gate_pass",
    "require_mpf_doctor_ok",
    "require_db_status_ok",
    "require_proxy_doctor_ok",
    "require_no_customer_nat_baseline",
    "require_no_customer_firewall_baseline",
    "require_local_only_runtime_baseline",
    "require_firewall_plan_review",
    "require_firewall_diff_review",
    "require_restore_point_before_apply",
    "require_iptables_save_backup_before_apply",
    "require_lock_before_apply",
    "require_verify_after_apply",
    "require_rollback_plan",
    "require_usage_visibility_check",
    "require_reject_visibility_check",
    "require_session_worker_visibility_check",
    "require_abuse_1h_coverage_check",
    "require_conntrack_scope_review",
    "require_post_execution_evidence_collection",
)


def build_phase11_manual_canary_execution_run_preparation_report(request: ManualCanaryExecutionRunPreparationRequest) -> dict[str, object]:
    validation_errors = request.validate()
    if any(not getattr(request, field) for field in REQUIRED_FIELDS):
        validation_errors.append("all preparation requirement toggles must remain true")

    ready = not validation_errors and request.requested_action == "prepare"
    return {
        "component": "phase11_manual_canary_execution_run_preparation",
        "phase": "Phase 11D — Operator-reviewed manual canary execution run preparation",
        "final_decision": "READY_FOR_FARM5_SYNC_EVIDENCE" if ready else "BLOCKED",
        "authorization_status": "MANUAL_CANARY_EXECUTION_RUN_PREPARATION_NON_AUTHORIZING",
        "execution_allowed": False,
        "actual_canary_execution_performed": False,
        "mutation_performed": False,
        "customer_db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "production_traffic_enabled": False,
        "request": request.as_dict(),
        "current_gate": {"accepted_phase": "Phase 10", "working_phase": "Phase 11", "production_traffic": "none", "firewall_apply_allowed": "no", "abuse_automation_allowed": "no", "customer_onboarding_allowed": "db_only", "ui_allowed": "no", "telegram_allowed": "no"},
        "prerequisite_evidence": {"farm5_0_1_149_sync_evidence_recorded": True, "phase11d_acceptance_package_evidence_recorded": True, "phase11d_execution_gate_evidence_recorded": True, "latest_main_sync_required_before_execution": True, "no_actual_canary_execution_evidence_claimed": True},
        "future_operator_run_preflight": [
            "mpf --version", "mpf phase-status", "mpf config validate", "mpf doctor", "mpf db status", "mpf proxy doctor", "mpf production readiness --output json", "mpf production canary-plan --output json", "mpf production activation-harness --output json", "mpf production canary-acceptance --output json", "mpf production canary-execution-gate --output json", "mpf production canary-execution-run-prep --output json", "bash scripts/verify_current_phase_gate.sh", "bash /opt/mpf-py-src/scripts/verify_current_phase_gate.sh from /root after 0.1.150 sync", "verify no MPF/customer NAT redirects", "verify no MPF/customer firewall rules", "verify accepted listeners are local-only",
        ],
        "future_operator_run_plan_preview": [
            "would select or create only canary-btc-001 under later explicit execution run", "would review customer DB mutation plan before any DB write", "would review firewall desired model before any apply", "would review firewall human diff and JSON diff before any apply", "would create restore point before any dangerous action", "would create iptables-save backup before any apply", "would acquire scheduler/apply lock before any apply", "would apply only through accepted firewall planner/service path after later execution approval", "would verify after apply", "would test one canary miner connection only", "would verify NAT hit visibility", "would verify usage visibility", "would verify reject visibility", "would verify session/worker visibility", "would verify abuse 1h coverage includes the canary customer", "would prepare rollback/restore command references", "would collect post-run farm5 evidence", "would not permit limited real customer onboarding before accepted canary evidence",
        ],
        "future_operator_run_evidence_requirements": ["before snapshot", "after snapshot", "customer row evidence", "firewall plan/diff evidence", "restore point reference", "iptables-save backup reference", "lock reference", "verification output", "canary miner connection proof", "NAT hit proof", "usage/reject/session/worker visibility proof", "abuse 1h coverage proof", "rollback/restore readiness proof", "final operator verdict"],
        "safety_flags": {k: False for k in ("production_traffic_authorized", "controlled_cli_canary_execution_authorized", "limited_customer_onboarding_authorized", "customer_db_mutation_authorized", "firewall_apply_authorized", "iptables_restore_authorized", "customer_nat_apply_authorized", "customer_firewall_rules_apply_authorized", "abuse_automation_authorized", "conntrack_flush_authorized", "worker_enforcement_authorized", "scheduler_authorized", "collector_authorized", "ui_authorized", "telegram_authorized")},
        "blockers": ["farm5 sync/test evidence required after merge", "actual manual canary execution remains forbidden until a later explicit operator-approved execution run", "firewall apply remains forbidden in this PR", "customer NAT/customer firewall rules remain preview-only in this PR", "customer DB mutation remains forbidden in this PR", "production traffic remains none", "abuse automation remains forbidden", "limited real customer onboarding remains forbidden"],
        "statements": [
            "This PR prepares the operator-reviewed execution run only.",
            "This PR does not execute canary traffic.",
            "This PR does not authorize Phase 11D actual execution.",
            "Actual execution requires a later farm5 run with explicit operator approval.",
            "Farm5 must sync latest main before actual execution.",
            "Actual execution must be one explicit canary only.",
            "Limited real customer onboarding remains forbidden until canary execution evidence is accepted.",
            "Phase 11 final acceptance remains later.",
        ],
        "validation_errors": validation_errors,
    }
