from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services.phase11_controlled_boundary_acceptance_decision_service import validate_controlled_boundary_package
from mpf.services.phase11e_limited_activation_common import (
    base_report,
    load_hashed_json,
    validate_confirmations,
    validate_current_phase_gate,
    validate_expected_version,
    validate_operator,
    validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_final_acceptance_readiness_only", "i_understand_no_current_state_change",
    "i_understand_phase11_not_accepted_by_this_command", "i_understand_no_production_expansion",
    "i_understand_no_miner_traffic_expansion", "i_understand_no_db_mutation", "i_understand_no_firewall_apply",
    "i_understand_no_runtime_change", "i_understand_no_ui_telegram",
)

DECISION_REQUIREMENTS = {
    "final_decision": "PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_DECISION_READY",
    "controlled_boundary_package_ready": True,
    "controlled_boundary_acceptance_decision_ready": True,
    "phase11_final_acceptance_pr_readiness_allowed": True,
    "phase11_final_acceptance_allowed": False,
    "production_expansion_allowed": False,
    "miner_traffic_expansion_allowed": False,
    "abuse_automation_allowed": False,
    "ui_allowed": False,
    "telegram_allowed": False,
    "mutation_performed": False,
    "db_mutation_performed": False,
    "firewall_apply_performed": False,
    "conntrack_flush_performed": False,
    "docker_restart_performed": False,
    "systemd_restart_performed": False,
    "phase11_accepted": False,
    "blockers": [],
    "warnings": [],
}


def _validate_decision(payload: dict[str, object] | None, blockers: list[str]) -> bool:
    if payload is None:
        return False
    for key, expected in DECISION_REQUIREMENTS.items():
        if payload.get(key) != expected:
            blockers.append(f"controlled_boundary_decision_invalid:{key}")
    return not any(item.startswith("controlled_boundary_decision_invalid:") for item in blockers)


def build_phase11_final_acceptance_pr_readiness_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers)
    validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    decision = load_hashed_json(kwargs, "controlled_boundary_decision_json", "controlled_boundary_decision_json_sha256", blockers)
    package = load_hashed_json(kwargs, "controlled_boundary_package_json", "controlled_boundary_package_json_sha256", blockers)
    validate_scope(decision, blockers, "controlled_boundary_decision")
    validate_scope(package, blockers, "controlled_boundary_package")
    decision_ready = _validate_decision(decision, blockers)
    package_ready = validate_controlled_boundary_package(package, blockers)
    before_gate = len(blockers)
    validate_current_phase_gate(blockers)
    current_phase_gate_ok = len(blockers) == before_gate
    ready = not blockers
    report = base_report("phase11_final_acceptance_pr_readiness", expected_version)
    report.update({
        "controlled_boundary_decision_ready": decision_ready,
        "controlled_boundary_package_ready": package_ready,
        "final_acceptance_pr_ready": ready,
        "proposed_next_current_accepted_phase": "Phase 11 — Production / Customer Activation Gate accepted on farm5",
        "proposed_next_current_working_phase": "Phase 11 operational completion",
        "proposed_next_production_traffic": "controlled_cli_limited",
        "proposed_next_firewall_apply_allowed": "controlled",
        "proposed_next_abuse_automation_allowed": "controlled_operator_gated",
        "proposed_next_customer_onboarding_allowed": "controlled_cli_limited",
        "proposed_next_worker_enforcement_allowed": "no",
        "proposed_next_ui_allowed": "no",
        "proposed_next_telegram_allowed": "no",
        "proposed_next_phase12_start_allowed": "no",
        "phase11_accepted": False,
        "current_state_changed": False,
        "current_phase_gate_ok": current_phase_gate_ok,
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "next_required_step": "phase11_final_acceptance_pr" if ready else "fix_blockers_and_rerun_phase11_final_acceptance_pr_readiness",
        "final_decision": "PHASE11_FINAL_ACCEPTANCE_PR_READINESS_READY" if ready else "BLOCKED",
    })
    return report
