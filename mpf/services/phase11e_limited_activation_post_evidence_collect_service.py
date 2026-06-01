from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11e_limited_activation_common import (
    CANARY_KEY,
    SCOPE,
    base_report,
    load_hashed_json,
    validate_artifact_gate,
    validate_confirmations,
    validate_current_phase_gate,
    validate_expected_version,
    validate_operator,
    validate_scope,
    source_db_ok,
    source_proxy_ok,
)

CONFIRMATIONS = (
    "operator_confirmed",
    "i_understand_post_evidence_only",
    "i_understand_no_db_mutation",
    "i_understand_no_firewall_apply",
    "i_understand_no_production_traffic_expansion",
    "i_understand_no_miner_traffic_expansion",
    "i_understand_no_abuse_automation",
)
def build_phase11e_limited_activation_post_evidence_collect_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers)
    validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    execution = load_hashed_json(kwargs, "activation_execution_json", "activation_execution_json_sha256", blockers)
    artifact = load_hashed_json(kwargs, "artifact_gate_json", "artifact_gate_json_sha256", blockers)
    validate_scope(execution, blockers, "activation_execution")
    validate_artifact_gate(artifact, blockers)
    blockers_before_phase_gate = len(blockers)
    validate_current_phase_gate(blockers)
    current_phase_gate_ok = len(blockers) == blockers_before_phase_gate
    if execution is not None and execution.get("final_decision") != "PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE":
        blockers.append("activation_execution_not_ready")

    source = None
    if kwargs.get("source_evidence_json") or kwargs.get("source_evidence_json_sha256"):
        source = load_hashed_json(kwargs, "source_evidence_json", "source_evidence_json_sha256", blockers)
        if source is not None and source.get("changed_customers") not in (None, [SCOPE["candidate_customer_key"]]):
            blockers.append("unexpected_changed_customer")

    rows = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
    limited = None
    canary_preserved = False
    if not rows.ok:
        blockers.append("customer_state_read_failed")
    else:
        limited_rows = [row for row in rows.customers if row.customer_key == SCOPE["candidate_customer_key"]]
        canary_rows = [row for row in rows.customers if row.customer_key == CANARY_KEY]
        if len(limited_rows) != 1:
            blockers.append("limited_customer_missing_or_ambiguous")
        else:
            limited = limited_rows[0]
            if limited.status != "active":
                blockers.append("limited_customer_not_active")
            if limited.lane != SCOPE["lane"] or limited.port != SCOPE["public_port"]:
                blockers.append("limited_customer_scope_mismatch")
        canary_preserved = len(canary_rows) == 1 and canary_rows[0].status == "active"
        if not canary_preserved:
            blockers.append("canary_missing_or_not_active")

    db_ok = None if source is None else source_db_ok(source)
    proxy_ok = None if source is None else source_proxy_ok(source)
    if source is None:
        warnings.append("source_evidence_not_provided_db_proxy_checks_unavailable")
    elif db_ok is not True or proxy_ok is not True:
        blockers.append("source_evidence_db_or_proxy_not_ok")

    report = base_report("phase11e_limited_activation_post_evidence_collect", expected_version)
    report.update({
        "limited_customer_status": None if limited is None else limited.status,
        "canary_preserved": canary_preserved,
        "artifact_gate_final_decision": None if artifact is None else artifact.get("final_decision"),
        "unknown_mpf_artifacts": None if artifact is None else artifact.get("unknown_mpf_artifacts"),
        "forbidden_public_runtime_exposure": None if artifact is None else artifact.get("forbidden_public_runtime_exposure"),
        "production_gates_remain_closed": None if artifact is None else artifact.get("production_gates_remain_closed"),
        "current_phase_gate_ok": current_phase_gate_ok,
        "db_ok": db_ok,
        "proxy_ok": proxy_ok,
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "next_required_step": "operator_review_phase11e_limited_activation_evidence" if not blockers else "fix_blockers_and_recollect",
        "final_decision": "PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY" if not blockers else "BLOCKED",
    })
    return report
