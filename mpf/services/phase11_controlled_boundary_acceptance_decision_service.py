from __future__ import annotations

from mpf.config import MPFConfig
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
    "operator_confirmed", "i_understand_controlled_boundary_decision_only", "i_understand_no_current_state_change",
    "i_understand_no_phase11_final_acceptance", "i_understand_no_production_expansion",
    "i_understand_no_miner_traffic_expansion", "i_understand_no_abuse_automation_enable",
    "i_understand_no_db_mutation", "i_understand_no_firewall_apply", "i_understand_no_runtime_change",
    "i_understand_no_ui_telegram",
)

PACKAGE_REQUIREMENTS = {
    "final_decision": "PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY",
    "limited_acceptance_decision_ready": True,
    "source_evidence_ready": True,
    "artifact_gate_passed": True,
    "abuse_readiness_ready": True,
    "restart_container_order_ready": True,
    "current_phase_gate_ok": True,
    "controlled_boundary_acceptance_package_ready": True,
    "controlled_boundary_acceptance_decision_pr_ready": True,
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


def validate_controlled_boundary_package(payload: dict[str, object] | None, blockers: list[str]) -> bool:
    if payload is None:
        return False
    for key, expected in PACKAGE_REQUIREMENTS.items():
        if payload.get(key) != expected:
            blockers.append(f"controlled_boundary_package_invalid:{key}")
    return not any(item.startswith("controlled_boundary_package_invalid:") for item in blockers)


def build_phase11_controlled_boundary_acceptance_decision_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers)
    validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    package = load_hashed_json(kwargs, "controlled_boundary_package_json", "controlled_boundary_package_json_sha256", blockers)
    validate_scope(package, blockers, "controlled_boundary_package")
    package_ready = validate_controlled_boundary_package(package, blockers)
    before_gate = len(blockers)
    validate_current_phase_gate(blockers)
    current_phase_gate_ok = len(blockers) == before_gate
    ready = not blockers
    report = base_report("phase11_controlled_boundary_acceptance_decision", expected_version)
    report.update({
        "controlled_boundary_package_ready": package_ready,
        "controlled_boundary_acceptance_decision_ready": ready,
        "phase11_final_acceptance_pr_readiness_allowed": ready,
        "phase11_final_acceptance_allowed": False,
        "production_expansion_allowed": False,
        "miner_traffic_expansion_allowed": False,
        "abuse_automation_allowed": False,
        "ui_allowed": False,
        "telegram_allowed": False,
        "current_phase_gate_ok": current_phase_gate_ok,
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "next_required_step": "phase11_final_acceptance_pr_readiness" if ready else "fix_blockers_and_rerun_controlled_boundary_acceptance_decision",
        "final_decision": "PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_DECISION_READY" if ready else "BLOCKED",
    })
    return report
