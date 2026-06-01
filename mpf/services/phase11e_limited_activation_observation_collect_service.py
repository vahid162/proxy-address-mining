from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11e_limited_activation_common import (
    CANARY_KEY, SCOPE, base_report, load_hashed_json, source_db_ok, source_proxy_ok,
    validate_artifact_gate, validate_confirmations, validate_current_phase_gate,
    validate_expected_version, validate_operator, validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_observation_only", "i_understand_no_db_mutation",
    "i_understand_no_firewall_apply", "i_understand_no_runtime_change",
    "i_understand_no_production_traffic_expansion", "i_understand_no_miner_traffic_expansion",
    "i_understand_no_abuse_automation", "i_understand_phase11_not_accepted",
)


def build_phase11e_limited_activation_observation_collect_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers)
    validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    execution = load_hashed_json(kwargs, "activation_execution_json", "activation_execution_json_sha256", blockers)
    post = load_hashed_json(kwargs, "post_activation_evidence_json", "post_activation_evidence_json_sha256", blockers)
    source = load_hashed_json(kwargs, "source_evidence_json", "source_evidence_json_sha256", blockers)
    artifact = load_hashed_json(kwargs, "artifact_gate_json", "artifact_gate_json_sha256", blockers)
    validate_scope(execution, blockers, "activation_execution")
    validate_scope(post, blockers, "post_activation_evidence")
    validate_artifact_gate(artifact, blockers)
    before_gate = len(blockers)
    validate_current_phase_gate(blockers)
    current_phase_gate_ok = len(blockers) == before_gate
    activation_ready = execution is not None and execution.get("final_decision") == "PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE"
    post_ready = post is not None and post.get("final_decision") == "PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY"
    if not activation_ready: blockers.append("activation_execution_not_ready")
    if not post_ready: blockers.append("post_activation_evidence_not_ready")
    db_ok = source is not None and source_db_ok(source)
    proxy_ok = source is not None and source_proxy_ok(source)
    if not db_ok or not proxy_ok: blockers.append("source_evidence_db_or_proxy_not_ok")

    limited = canary = None
    rows = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
    if not rows.ok:
        blockers.append("customer_state_read_failed")
    else:
        limited_rows = [r for r in rows.customers if r.customer_key == SCOPE["candidate_customer_key"]]
        canary_rows = [r for r in rows.customers if r.customer_key == CANARY_KEY]
        if len(limited_rows) != 1: blockers.append("limited_customer_missing_or_ambiguous")
        else:
            limited = limited_rows[0]
            if limited.status != "active": blockers.append("limited_customer_not_active")
            if limited.lane != SCOPE["lane"] or limited.port != SCOPE["public_port"]: blockers.append("limited_customer_scope_mismatch")
        if len(canary_rows) != 1: blockers.append("canary_missing_or_ambiguous")
        else:
            canary = canary_rows[0]
            if canary.status != "active": blockers.append("canary_missing_or_not_active")
    artifact_passed = artifact is not None and not any(x in blockers for x in ("artifact_gate_not_passed", "unknown_mpf_artifacts", "forbidden_public_runtime_exposure", "production_gates_not_closed"))
    ready = not blockers
    report = base_report("phase11e_limited_activation_observation_collect", expected_version)
    report.update({
        "activation_execution_ready": activation_ready, "post_activation_evidence_ready": post_ready,
        "source_evidence_ready": db_ok and proxy_ok, "artifact_gate_passed": artifact_passed,
        "limited_customer_status": None if limited is None else limited.status,
        "canary_customer_status": None if canary is None else canary.status,
        "canary_preserved": canary is not None and canary.status == "active", "db_ok": db_ok, "proxy_ok": proxy_ok,
        "ui_allowed": False, "telegram_allowed": False,
        "current_phase_gate_ok": current_phase_gate_ok,
        "unknown_mpf_artifacts": None if artifact is None else artifact.get("unknown_mpf_artifacts"),
        "forbidden_public_runtime_exposure": None if artifact is None else artifact.get("forbidden_public_runtime_exposure"),
        "production_gates_remain_closed": None if artifact is None else artifact.get("production_gates_remain_closed"),
        "blockers": sorted(set(blockers)), "warnings": [],
        "next_required_step": "phase11e_limited_activation_acceptance_review" if ready else "fix_blockers_and_recollect",
        "final_decision": "PHASE11E_LIMITED_ACTIVATION_OBSERVATION_READY" if ready else "BLOCKED",
    })
    return report
