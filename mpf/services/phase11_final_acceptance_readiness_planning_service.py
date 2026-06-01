from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_common import (
    base_report, load_hashed_json, validate_artifact_gate, validate_confirmations,
    validate_current_phase_gate, validate_expected_version, validate_operator,
    validate_rollback_package_scope, validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_readiness_planning_only", "i_understand_no_current_state_change",
    "i_understand_no_production_expansion", "i_understand_no_miner_traffic_expansion",
    "i_understand_no_abuse_automation", "i_understand_no_ui_telegram", "i_understand_phase11_not_accepted",
)


def build_phase11_final_acceptance_readiness_planning_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers); validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    window = load_hashed_json(kwargs, "observation_window_json", "observation_window_json_sha256", blockers)
    review = load_hashed_json(kwargs, "acceptance_review_json", "acceptance_review_json_sha256", blockers)
    rollback = load_hashed_json(kwargs, "rollback_package_json", "rollback_package_json_sha256", blockers)
    artifact = load_hashed_json(kwargs, "artifact_gate_json", "artifact_gate_json_sha256", blockers)
    validate_scope(window, blockers, "observation_window"); validate_scope(review, blockers, "acceptance_review")
    validate_rollback_package_scope(rollback, blockers); validate_artifact_gate(artifact, blockers)
    before_gate = len(blockers); validate_current_phase_gate(blockers); current_phase_gate_ok = len(blockers) == before_gate
    window_ready = window is not None and window.get("final_decision") == "PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY"
    review_ready = review is not None and review.get("final_decision") == "PHASE11E_LIMITED_ACTIVATION_ACCEPTANCE_REVIEW_READY"
    rollback_ready = rollback is not None and rollback.get("final_decision") == "PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY"
    if not window_ready: blockers.append("limited_customer_observation_window_not_ready")
    if not review_ready: blockers.append("limited_activation_acceptance_review_not_ready")
    if not rollback_ready: blockers.append("rollback_package_not_ready")
    artifact_passed = artifact is not None and not any(x in blockers for x in ("artifact_gate_not_passed", "unknown_mpf_artifacts", "forbidden_public_runtime_exposure", "production_gates_not_closed"))
    ready = not blockers
    report = base_report("phase11_final_acceptance_readiness_planning", expected_version)
    report.update({"limited_customer_observation_window_ready": window_ready, "limited_activation_review_ready": review_ready,
        "rollback_ready": rollback_ready, "artifact_gate_passed": artifact_passed, "current_phase_gate_ok": current_phase_gate_ok,
        "phase11_final_acceptance_pr_ready": ready, "phase11_final_acceptance_allowed": False, "production_expansion_allowed": False,
        "miner_traffic_expansion_allowed": False, "abuse_automation_allowed": False, "ui_allowed": False, "telegram_allowed": False,
        "blockers": sorted(set(blockers)), "warnings": [],
        "next_required_step": "explicit_phase11_limited_acceptance_decision_pr" if ready else "fix_blockers_and_rerun_final_readiness_planning",
        "final_decision": "PHASE11_FINAL_ACCEPTANCE_READINESS_PLANNING_READY" if ready else "BLOCKED"})
    return report
