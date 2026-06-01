from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_common import (
    base_report, load_hashed_json, validate_artifact_gate, validate_confirmations,
    validate_current_phase_gate, validate_expected_version, validate_operator,
    validate_rollback_package_scope, validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_review_only", "i_understand_no_db_mutation",
    "i_understand_no_firewall_apply", "i_understand_no_runtime_change",
    "i_understand_no_production_traffic_expansion", "i_understand_no_miner_traffic_expansion",
    "i_understand_no_abuse_automation", "i_understand_phase11_not_accepted",
    "i_understand_limited_acceptance_is_not_phase11_final",
)
FORBIDDEN_TRUE_FIELDS = (
    "mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed",
    "docker_restart_performed", "systemd_restart_performed", "production_traffic_enabled",
    "miner_traffic_allowed", "abuse_automation_enabled", "ui_allowed", "telegram_allowed", "phase11_accepted",
)


def _require_decision(payload: dict[str, object] | None, expected: str, blocker: str, blockers: list[str]) -> bool:
    ok = payload is not None and payload.get("final_decision") == expected
    if not ok: blockers.append(blocker)
    return ok


def build_phase11e_limited_activation_acceptance_review_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers)
    validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    execution = load_hashed_json(kwargs, "activation_execution_json", "activation_execution_json_sha256", blockers)
    post = load_hashed_json(kwargs, "post_activation_evidence_json", "post_activation_evidence_json_sha256", blockers)
    observation = load_hashed_json(kwargs, "observation_json", "observation_json_sha256", blockers)
    rollback = load_hashed_json(kwargs, "limited_activation_rollback_package_json", "limited_activation_rollback_package_json_sha256", blockers)
    artifact = load_hashed_json(kwargs, "artifact_gate_json", "artifact_gate_json_sha256", blockers)
    for payload, tag in ((execution, "activation_execution"), (post, "post_activation_evidence"), (observation, "observation")):
        validate_scope(payload, blockers, tag)
    validate_rollback_package_scope(rollback, blockers)
    validate_artifact_gate(artifact, blockers)
    before_gate = len(blockers)
    validate_current_phase_gate(blockers)
    current_phase_gate_ok = len(blockers) == before_gate
    execution_ok = _require_decision(execution, "PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE", "activation_execution_not_ready", blockers)
    post_ok = _require_decision(post, "PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY", "post_activation_evidence_not_ready", blockers)
    observation_ok = _require_decision(observation, "PHASE11E_LIMITED_ACTIVATION_OBSERVATION_READY", "observation_not_ready", blockers)
    rollback_ok = _require_decision(rollback, "PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY", "rollback_package_not_ready", blockers)
    if observation is not None:
        for field in FORBIDDEN_TRUE_FIELDS:
            if observation.get(field) is not False: blockers.append(f"observation_unsafe:{field}")
    artifact_passed = artifact is not None and not any(x in blockers for x in ("artifact_gate_not_passed", "unknown_mpf_artifacts", "forbidden_public_runtime_exposure", "production_gates_not_closed"))
    ready = not blockers
    report = base_report("phase11e_limited_activation_acceptance_review", expected_version)
    report.update({
        "activation_execution_accepted": execution_ok, "post_activation_evidence_accepted": post_ok,
        "observation_accepted": observation_ok, "rollback_ready": rollback_ok, "artifact_gate_passed": artifact_passed,
        "current_phase_gate_ok": current_phase_gate_ok, "limited_activation_review_ready": ready,
        "phase11_final_acceptance_allowed": False, "production_expansion_allowed": False,
        "miner_traffic_expansion_allowed": False, "abuse_automation_allowed": False, "ui_allowed": False, "telegram_allowed": False,
        "blockers": sorted(set(blockers)), "warnings": [],
        "next_required_step": "phase11e_limited_customer_observation_window_or_phase11_final_readiness_planning" if ready else "fix_blockers_and_rerun_review",
        "final_decision": "PHASE11E_LIMITED_ACTIVATION_ACCEPTANCE_REVIEW_READY" if ready else "BLOCKED",
    })
    return report
