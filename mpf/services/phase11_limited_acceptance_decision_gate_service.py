from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_common import (
    base_report, load_hashed_json, validate_artifact_gate, validate_confirmations,
    validate_current_phase_gate, validate_expected_version, validate_operator,
    validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_limited_acceptance_decision_only", "i_understand_no_current_state_change",
    "i_understand_no_phase11_final_acceptance", "i_understand_no_production_expansion",
    "i_understand_no_miner_traffic_expansion", "i_understand_no_abuse_automation",
    "i_understand_no_db_mutation", "i_understand_no_firewall_apply", "i_understand_no_runtime_change",
    "i_understand_no_ui_telegram",
)


def _validate_observation_window(payload: dict[str, object] | None, blockers: list[str]) -> bool:
    if payload is None:
        return False
    requirements = {
        "final_decision": "PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY",
        "limited_customer_status": "active", "canary_customer_status": "active", "canary_preserved": True,
        "db_ok": True, "proxy_ok": True, "artifact_gate_passed": True, "current_phase_gate_ok": True,
        "production_gates_remain_closed": True, "unknown_mpf_artifacts": [],
        "forbidden_public_runtime_exposure": False, "blockers": [],
    }
    for key, expected in requirements.items():
        if payload.get(key) != expected:
            blockers.append(f"observation_window_invalid:{key}")
    samples = payload.get("samples_collected")
    if not isinstance(samples, int) or isinstance(samples, bool) or samples < 3:
        blockers.append("observation_window_insufficient_samples")
    return not any(item.startswith("observation_window_") for item in blockers)


def _validate_final_readiness(payload: dict[str, object] | None, blockers: list[str]) -> bool:
    if payload is None:
        return False
    requirements = {
        "final_decision": "PHASE11_FINAL_ACCEPTANCE_READINESS_PLANNING_READY",
        "phase11_final_acceptance_pr_ready": True, "phase11_final_acceptance_allowed": False,
        "production_expansion_allowed": False, "miner_traffic_expansion_allowed": False,
        "abuse_automation_allowed": False, "ui_allowed": False, "telegram_allowed": False, "blockers": [],
    }
    for key, expected in requirements.items():
        if payload.get(key) != expected:
            blockers.append(f"final_readiness_planning_invalid:{key}")
    return not any(item.startswith("final_readiness_planning_") for item in blockers)


def build_phase11_limited_acceptance_decision_gate_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers); validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    window = load_hashed_json(kwargs, "observation_window_json", "observation_window_json_sha256", blockers)
    readiness = load_hashed_json(kwargs, "final_readiness_planning_json", "final_readiness_planning_json_sha256", blockers)
    artifact = load_hashed_json(kwargs, "artifact_gate_json", "artifact_gate_json_sha256", blockers)
    validate_scope(window, blockers, "observation_window"); validate_scope(readiness, blockers, "final_readiness_planning")
    window_ready = _validate_observation_window(window, blockers)
    readiness_ready = _validate_final_readiness(readiness, blockers)
    before_artifact = len(blockers); validate_artifact_gate(artifact, blockers); artifact_passed = artifact is not None and len(blockers) == before_artifact
    before_gate = len(blockers); validate_current_phase_gate(blockers); current_phase_gate_ok = len(blockers) == before_gate
    ready = not blockers
    report = base_report("phase11_limited_acceptance_decision_gate", expected_version)
    report.update({"observation_window_ready": window_ready, "final_readiness_planning_ready": readiness_ready,
        "artifact_gate_passed": artifact_passed, "current_phase_gate_ok": current_phase_gate_ok,
        "limited_acceptance_decision_ready": ready, "controlled_boundary_package_pr_ready": ready,
        "phase11_final_acceptance_allowed": False, "production_expansion_allowed": False,
        "miner_traffic_expansion_allowed": False, "abuse_automation_allowed": False, "ui_allowed": False,
        "telegram_allowed": False, "blockers": sorted(set(blockers)), "warnings": [],
        "next_required_step": "phase11_controlled_boundary_acceptance_package_pr" if ready else "fix_blockers_and_rerun_limited_acceptance_decision_gate",
        "final_decision": "PHASE11_LIMITED_ACCEPTANCE_DECISION_GATE_READY" if ready else "BLOCKED"})
    return report
