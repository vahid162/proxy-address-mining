from __future__ import annotations

import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

_REQUIRED_NEXT_EXECUTION_CHECKLIST = [
    "create or validate exactly one limited real customer candidate",
    "ensure no collision with canary port 20001",
    "ensure no collision with existing customer ports",
    "generate DB-only customer staging plan",
    "generate firewall plan/diff only",
    "require restore point and lock before any future apply",
    "require rollback/restore-plan artifact",
    "require restart/container-order evidence",
    "require live Stratum transcript evidence for the limited customer",
    "require runtime-path evidence for the limited customer",
    "require visibility bundle evidence",
    "require abuse 1h coverage evidence for active customers in enabled lanes",
    "require operator approval before future execution",
]


def build_phase11_limited_onboarding_execution_gate_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    warnings: list[str] = []

    expected_version = str(kwargs.get("expected_version", __version__))
    farm5_baseline_version = str(kwargs.get("farm5_baseline_version", "0.1.168"))
    gate_json = Path(str(kwargs.get("limited_onboarding_gate_json", "")))
    candidate_customer_key = str(kwargs.get("candidate_customer_key", "")).strip()
    candidate_lane = str(kwargs.get("candidate_lane", "")).strip().lower()
    candidate_public_port = kwargs.get("candidate_public_port")
    candidate_backend_target = str(kwargs.get("candidate_backend_target", "")).strip()
    candidate_description = str(kwargs.get("candidate_description", "")).strip()
    operator = str(kwargs.get("operator", "")).strip()
    reason = str(kwargs.get("reason", "")).strip()

    data: dict[str, object] | None = None
    if not gate_json.exists() or not gate_json.is_file():
        blockers.append("limited_onboarding_gate_json_missing")
    else:
        try:
            data = json.loads(gate_json.read_text(encoding="utf-8"))
        except Exception:
            blockers.append("limited_onboarding_gate_json_invalid")

    if data is not None:
        required_scope = {
            "component": "phase11_limited_onboarding_gate",
            "expected_version": "0.1.198",
            "repository_version": "0.1.198",
            "phase11d_canary_accepted": True,
            "phase11e_gate_ready": True,
            "phase11e_execution_allowed": False,
            "final_decision": "PHASE11E_LIMITED_ONBOARDING_GATE_READY",
            "next_required_step": "phase11e_limited_onboarding_execution_gate_pr",
        }
        if any(data.get(k) != v for k, v in required_scope.items()) or data.get("blockers") != [] or data.get("warnings") != []:
            blockers.append("limited_onboarding_gate_not_ready")

        if any(data.get(k) is not False for k in ("phase11_accepted", "limited_onboarding_allowed", "production_traffic_enabled")) or data.get("no_onboarding_authorized") is not True:
            blockers.append("limited_onboarding_gate_safety_boundary_open")

        if any(data.get(k) is True for k in ("mutation_performed", "firewall_mutation_performed", "nat_mutation_performed", "conntrack_mutation_performed", "docker_mutation_performed", "db_mutation_performed")):
            blockers.append("limited_onboarding_gate_mutation_flag_detected")

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")
    if farm5_baseline_version != "0.1.168":
        blockers.append("farm5_baseline_version_mismatch")

    if not candidate_customer_key.startswith("limited-btc-"):
        blockers.append("candidate_customer_key_invalid")
    if candidate_lane != "btc":
        blockers.append("candidate_lane_not_allowed")
    if not isinstance(candidate_public_port, int):
        blockers.append("candidate_public_port_invalid")
    else:
        if candidate_public_port == 20001:
            blockers.append("candidate_public_port_collides_with_canary")
        if candidate_public_port < 20101 or candidate_public_port > 20120:
            blockers.append("candidate_public_port_out_of_range")
    if candidate_backend_target != "172.18.0.3:60010":
        blockers.append("candidate_backend_target_invalid")
    if not candidate_description:
        blockers.append("candidate_description_missing")

    if not operator or not reason or kwargs.get("operator_confirmed") is not True:
        blockers.append("operator_not_confirmed")
    if kwargs.get("i_understand_this_does_not_onboard_customer") is not True:
        blockers.append("no_customer_onboarding_boundary_not_confirmed")
    if kwargs.get("i_understand_no_firewall_apply_yet") is not True:
        blockers.append("no_firewall_apply_boundary_not_confirmed")
    if kwargs.get("i_understand_no_production_traffic_yet") is not True:
        blockers.append("no_production_traffic_boundary_not_confirmed")
    if kwargs.get("i_understand_next_pr_must_execute_controlled_single_customer") is not True:
        blockers.append("next_pr_execution_boundary_not_confirmed")
    if kwargs.get("i_confirm_rollback_plan_required") is not True:
        blockers.append("rollback_plan_requirement_not_confirmed")
    if kwargs.get("i_confirm_restart_test_required") is not True:
        blockers.append("restart_test_requirement_not_confirmed")
    if kwargs.get("i_confirm_abuse_1h_coverage_required") is not True:
        blockers.append("abuse_1h_requirement_not_confirmed")

    blockers = sorted(set(blockers))
    ready = not blockers

    return {
        "component": "phase11_limited_onboarding_execution_gate",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": candidate_customer_key,
        "candidate_lane": candidate_lane,
        "candidate_public_port": candidate_public_port,
        "candidate_backend_target": candidate_backend_target,
        "phase11e_execution_gate_ready": ready,
        "phase11e_execution_allowed": False,
        "customer_created": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "mutation_performed": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "production_traffic_enabled": False,
        "no_onboarding_authorized": True,
        "required_next_execution_checklist": _REQUIRED_NEXT_EXECUTION_CHECKLIST,
        "blockers": blockers,
        "warnings": warnings,
        "next_required_step": "phase11e_single_customer_execution_pr" if ready else "none",
        "final_decision": "PHASE11E_LIMITED_ONBOARDING_EXECUTION_GATE_READY" if ready else "BLOCKED",
    }
