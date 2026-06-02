from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services.phase11_controlled_boundary_acceptance_decision_service import validate_controlled_boundary_package
from mpf.services.phase11_final_acceptance_pr_readiness_service import _validate_decision
from mpf.services.phase11e_limited_activation_common import (
    PHASE11_POST_FINAL_ACCEPTANCE_GATE, SCOPE, load_hashed_json, validate_confirmations,
    validate_current_phase_gate, validate_expected_version, validate_operator, validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_phase11_final_acceptance", "i_understand_controlled_cli_limited_only",
    "i_understand_phase12_is_next", "i_understand_worker_enforcement_remains_disabled",
    "i_understand_ui_telegram_remain_disabled", "i_understand_no_unrestricted_production_expansion",
    "i_understand_no_db_mutation", "i_understand_no_firewall_apply", "i_understand_no_runtime_change",
)
READINESS_REQUIREMENTS = {
    "final_decision": "PHASE11_FINAL_ACCEPTANCE_PR_READINESS_READY", "controlled_boundary_decision_ready": True,
    "controlled_boundary_package_ready": True, "final_acceptance_pr_ready": True,
    "proposed_next_current_accepted_phase": PHASE11_POST_FINAL_ACCEPTANCE_GATE["current_accepted_phase"],
    "proposed_next_current_working_phase": PHASE11_POST_FINAL_ACCEPTANCE_GATE["current_working_phase"],
    "proposed_next_production_traffic": "controlled_cli_limited", "proposed_next_firewall_apply_allowed": "controlled",
    "proposed_next_abuse_automation_allowed": "controlled", "proposed_next_customer_onboarding_allowed": "controlled_cli_limited",
    "proposed_next_worker_enforcement_allowed": "no", "proposed_next_ui_allowed": "no", "proposed_next_telegram_allowed": "no",
    "blockers": [], "warnings": [],
}

def _validate(payload: dict[str, object] | None, requirements: dict[str, object], tag: str, blockers: list[str]) -> bool:
    if payload is None: return False
    for key, expected in requirements.items():
        if payload.get(key) != expected: blockers.append(f"{tag}_invalid:{key}")
    return not any(x.startswith(f"{tag}_invalid:") for x in blockers)

def build_phase11_final_acceptance_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers); validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    readiness = load_hashed_json(kwargs, "final_acceptance_pr_readiness_json", "final_acceptance_pr_readiness_json_sha256", blockers)
    decision = load_hashed_json(kwargs, "controlled_boundary_decision_json", "controlled_boundary_decision_json_sha256", blockers)
    package = load_hashed_json(kwargs, "controlled_boundary_package_json", "controlled_boundary_package_json_sha256", blockers)
    for payload, tag in ((readiness,"final_acceptance_pr_readiness"),(decision,"controlled_boundary_decision"),(package,"controlled_boundary_package")):
        validate_scope(payload, blockers, tag)
    readiness_ready = _validate(readiness, READINESS_REQUIREMENTS, "final_acceptance_pr_readiness", blockers)
    decision_ready = _validate_decision(decision, blockers)
    package_ready = validate_controlled_boundary_package(package, blockers)
    validate_current_phase_gate(blockers, requirements=PHASE11_POST_FINAL_ACCEPTANCE_GATE)
    ready = not blockers
    return {"component":"phase11_final_acceptance", "expected_version":expected_version, "repository_version":__import__('mpf').__version__,
        **SCOPE, "evidence_backend_target":SCOPE["backend_target"], "stable_runtime_backend":"127.0.0.1:60010",
        "controlled_boundary_decision_ready":decision_ready, "controlled_boundary_package_ready":package_ready,
        "final_acceptance_pr_readiness_ready":readiness_ready, "final_accepted_phase":PHASE11_POST_FINAL_ACCEPTANCE_GATE["current_accepted_phase"],
        "next_working_phase":PHASE11_POST_FINAL_ACCEPTANCE_GATE["current_working_phase"], "production_traffic":"controlled_cli_limited",
        "firewall_apply_allowed":"controlled", "abuse_automation_allowed":"controlled", "customer_onboarding_allowed":"controlled_cli_limited",
        "worker_enforcement_allowed":"no", "ui_allowed":"no", "telegram_allowed":"no", "phase11_accepted":ready, "phase12_accepted":False,
        "current_state_changed_by_command":False, "mutation_performed":False, "db_mutation_performed":False, "firewall_apply_performed":False,
        "conntrack_flush_performed":False, "docker_restart_performed":False, "systemd_restart_performed":False,
        "blockers":sorted(set(blockers)), "warnings":[], "next_required_step":"phase12_worker_evidence_mapping_readiness" if ready else "fix_blockers_and_rerun_phase11_final_acceptance",
        "final_decision":"PHASE11_FINAL_ACCEPTANCE_ACCEPTED" if ready else "BLOCKED"}
