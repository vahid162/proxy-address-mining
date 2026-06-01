from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services import customer_mutation_service, customer_read_service
from mpf.services.phase11e_limited_activation_common import (
    CANARY_KEY, SCOPE, base_report, load_hashed_json, validate_artifact_gate,
    validate_confirmations, validate_current_phase_gate, validate_expected_version, validate_operator, validate_rollback_package_scope, validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_this_mutates_limited_customer_db_state", "i_understand_limited_btc_001_only",
    "i_understand_canary_must_be_preserved", "i_understand_no_firewall_apply", "i_understand_no_unrestricted_production",
    "i_understand_no_miner_traffic_expansion", "i_understand_no_abuse_automation", "i_understand_phase11_not_accepted",
    "i_have_reviewed_rollback_package", "i_have_reviewed_post_evidence_command",
)


def _customers(config: MPFConfig, blockers: list[str]):
    result = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
    if not result.ok:
        blockers.append("customer_state_read_failed")
        return None, None
    limited = [r for r in result.customers if r.customer_key == SCOPE["candidate_customer_key"]]
    canary = [r for r in result.customers if r.customer_key == CANARY_KEY]
    if len(limited) != 1:
        blockers.append("limited_customer_missing_or_ambiguous")
    if len(canary) != 1 or canary[0].status != "active":
        blockers.append("canary_missing_or_not_active")
    limited_row = limited[0] if len(limited) == 1 else None
    if limited_row is not None:
        if limited_row.status != "paused": blockers.append("limited_customer_not_paused")
        if limited_row.lane != SCOPE["lane"] or limited_row.port != SCOPE["public_port"]: blockers.append("limited_customer_scope_mismatch")
    return limited_row, canary[0] if len(canary) == 1 else None


def build_phase11e_limited_activation_execute_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers)
    validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    decision = load_hashed_json(kwargs, "limited_activation_decision_json", "limited_activation_decision_json_sha256", blockers)
    execution = load_hashed_json(kwargs, "limited_activation_execution_package_json", "limited_activation_execution_package_json_sha256", blockers)
    rollback = load_hashed_json(kwargs, "limited_activation_rollback_package_json", "limited_activation_rollback_package_json_sha256", blockers)
    artifact = load_hashed_json(kwargs, "artifact_gate_json", "artifact_gate_json_sha256", blockers)
    for payload, tag, final_decision in (
        (decision, "decision", "PHASE11E_LIMITED_ACTIVATION_DECISION_READY"),
        (execution, "execution_package", "PHASE11E_LIMITED_ACTIVATION_EXECUTION_PACKAGE_READY"),
    ):
        validate_scope(payload, blockers, tag)
        if payload is not None and payload.get("final_decision") != final_decision:
            blockers.append(f"{tag}_not_ready")
    validate_rollback_package_scope(rollback, blockers)
    if rollback is not None and rollback.get("final_decision") != "PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY":
        blockers.append("rollback_package_not_ready")
    validate_artifact_gate(artifact, blockers)
    validate_current_phase_gate(blockers)
    before, _ = _customers(config, blockers)
    report = base_report("phase11e_limited_activation_execute", expected_version)
    report.update({
        "decision_sha256": kwargs.get("limited_activation_decision_json_sha256"),
        "execution_package_sha256": kwargs.get("limited_activation_execution_package_json_sha256"),
        "rollback_package_sha256": kwargs.get("limited_activation_rollback_package_json_sha256"),
        "artifact_gate_sha256": kwargs.get("artifact_gate_json_sha256"),
        "preflight_ready": not blockers, "activation_executed": False,
        "before_customer_status": None if before is None else before.status, "after_customer_status": None,
        "canary_preserved": False, "changed_customers": [], "event_audit_recorded": False,
    })
    if not blockers:
        result = customer_mutation_service.activate_phase11e_limited_customer(
            config, customer_key=SCOPE["candidate_customer_key"], lane=SCOPE["lane"], port=SCOPE["public_port"],
            operator=str(kwargs["operator"]), reason=str(kwargs["reason"]),
        )
        if not result.ok:
            blockers.append(f"activation_failed:{result.message}")
        else:
            report.update({"activation_executed": True, "mutation_performed": True, "db_mutation_performed": True,
                           "after_customer_status": "active", "canary_preserved": True,
                           "changed_customers": [SCOPE["candidate_customer_key"]], "event_audit_recorded": True})
    report.update({"blockers": sorted(set(blockers)), "warnings": warnings,
                   "next_required_step": "phase11e_limited_activation_post_evidence_collection" if report["activation_executed"] else "fix_blockers_and_retry",
                   "final_decision": "PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE" if report["activation_executed"] else "BLOCKED"})
    return report
