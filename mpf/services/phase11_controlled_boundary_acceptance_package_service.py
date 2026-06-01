from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_common import (
    CANARY_KEY,
    base_report,
    load_hashed_json,
    source_db_ok,
    source_proxy_ok,
    validate_artifact_gate,
    validate_confirmations,
    validate_current_phase_gate,
    validate_expected_version,
    validate_operator,
    validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_controlled_boundary_package_only", "i_understand_no_current_state_change",
    "i_understand_no_phase11_final_acceptance", "i_understand_no_production_expansion",
    "i_understand_no_miner_traffic_expansion", "i_understand_no_abuse_automation_enable",
    "i_understand_no_db_mutation", "i_understand_no_firewall_apply", "i_understand_no_runtime_change",
    "i_understand_no_ui_telegram",
)


def _validate_limited_decision(payload: dict[str, object] | None, blockers: list[str]) -> bool:
    if payload is None:
        return False
    requirements = {
        "final_decision": "PHASE11_LIMITED_ACCEPTANCE_DECISION_GATE_READY",
        "limited_acceptance_decision_ready": True, "controlled_boundary_package_pr_ready": True,
        "phase11_final_acceptance_allowed": False, "production_expansion_allowed": False,
        "miner_traffic_expansion_allowed": False, "abuse_automation_allowed": False,
        "ui_allowed": False, "telegram_allowed": False, "blockers": [],
    }
    for key, expected in requirements.items():
        if payload.get(key) != expected:
            blockers.append(f"limited_acceptance_decision_invalid:{key}")
    return not any(item.startswith("limited_acceptance_decision_invalid:") for item in blockers)


def _customer_active(source: dict[str, object], key: str) -> bool:
    direct = source.get(f"{key.replace('-', '_')}_status")
    if direct == "active":
        return True
    customers = source.get("customers")
    if isinstance(customers, list):
        for customer in customers:
            if isinstance(customer, dict) and customer.get("customer_key", customer.get("key")) == key:
                return customer.get("status") == "active"
    customer_statuses = source.get("customer_statuses")
    return isinstance(customer_statuses, dict) and customer_statuses.get(key) == "active"


def _validate_source(payload: dict[str, object] | None, blockers: list[str]) -> bool:
    if payload is None:
        return False
    if not source_db_ok(payload):
        blockers.append("source_evidence_db_not_ok")
    if not source_proxy_ok(payload):
        blockers.append("source_evidence_proxy_not_ok")
    if not _customer_active(payload, "limited-btc-001"):
        blockers.append("source_evidence_limited_btc_001_not_active")
    if not _customer_active(payload, CANARY_KEY):
        blockers.append("source_evidence_canary_btc_001_not_active")
    for key in ("required_containers_running", "required_listeners_local_only"):
        if key in payload and payload.get(key) is not True:
            blockers.append(f"source_evidence_invalid:{key}")
    if payload.get("forbidden_public_runtime_exposure") is True:
        blockers.append("source_evidence_forbidden_public_runtime_exposure")
    return not any(item.startswith("source_evidence_") for item in blockers)


def _validate_abuse(payload: dict[str, object] | None, blockers: list[str]) -> bool:
    if payload is None:
        return False
    requirements = {
        "final_decision": "PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY",
        "abuse_1h_coverage_ready": True, "abuse_state_machine_contract_ready": True,
        "hard_after_1h_contract_ready": True, "no_farms_only_hard_contract_ready": True,
        "no_worker_only_hard_contract_ready": True, "no_missing_stale_evidence_hard_contract_ready": True,
        "abuse_automation_enabled": False, "mutation_performed": False, "blockers": [],
    }
    for key, expected in requirements.items():
        value = payload.get(key)
        if value != expected:
            blockers.append(f"abuse_readiness_invalid:{key}")
    return not any(item.startswith("abuse_readiness_invalid:") for item in blockers)


def _validate_restart(payload: dict[str, object] | None, blockers: list[str]) -> bool:
    if payload is None:
        return False
    requirements = {
        "final_decision": "PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY",
        "restart_container_order_ready": True, "container_order_contract_ready": True,
        "local_only_runtime_ready": True, "backend_public_exposure_blocked": True,
        "backend_internal_reachability_ready": True, "production_traffic_enabled": False,
        "miner_traffic_allowed": False, "abuse_automation_enabled": False,
        "mutation_performed": False, "blockers": [],
    }
    for key, expected in requirements.items():
        if payload.get(key) != expected:
            blockers.append(f"restart_readiness_invalid:{key}")
    return not any(item.startswith("restart_readiness_invalid:") for item in blockers)


def build_phase11_controlled_boundary_acceptance_package_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers)
    validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    decision = load_hashed_json(kwargs, "limited_acceptance_decision_json", "limited_acceptance_decision_json_sha256", blockers)
    artifact = load_hashed_json(kwargs, "artifact_gate_json", "artifact_gate_json_sha256", blockers)
    source = load_hashed_json(kwargs, "source_evidence_json", "source_evidence_json_sha256", blockers)
    abuse = load_hashed_json(kwargs, "abuse_readiness_json", "abuse_readiness_json_sha256", blockers)
    restart = load_hashed_json(kwargs, "restart_readiness_json", "restart_readiness_json_sha256", blockers)
    for tag, payload in (("limited_acceptance_decision", decision), ("source_evidence", source), ("abuse_readiness", abuse), ("restart_readiness", restart)):
        validate_scope(payload, blockers, tag)
    decision_ready = _validate_limited_decision(decision, blockers)
    before_artifact = len(blockers)
    validate_artifact_gate(artifact, blockers)
    if artifact is not None and artifact.get("current_phase_gate_ok") is not True:
        blockers.append("artifact_gate_current_phase_gate_not_ok")
    artifact_passed = artifact is not None and len(blockers) == before_artifact
    source_ready = _validate_source(source, blockers)
    abuse_ready = _validate_abuse(abuse, blockers)
    restart_ready = _validate_restart(restart, blockers)
    before_gate = len(blockers)
    validate_current_phase_gate(blockers)
    current_phase_gate_ok = len(blockers) == before_gate
    ready = not blockers
    report = base_report("phase11_controlled_boundary_acceptance_package", expected_version)
    report.update({
        "limited_acceptance_decision_ready": decision_ready, "source_evidence_ready": source_ready,
        "artifact_gate_passed": artifact_passed, "abuse_readiness_ready": abuse_ready,
        "restart_container_order_ready": restart_ready, "current_phase_gate_ok": current_phase_gate_ok,
        "controlled_boundary_acceptance_package_ready": ready,
        "controlled_boundary_acceptance_decision_pr_ready": ready,
        "phase11_final_acceptance_allowed": False, "production_expansion_allowed": False,
        "miner_traffic_expansion_allowed": False, "abuse_automation_allowed": False,
        "ui_allowed": False, "telegram_allowed": False, "blockers": sorted(set(blockers)), "warnings": [],
        "next_required_step": "phase11_controlled_boundary_acceptance_decision_pr" if ready else "fix_blockers_and_rerun_controlled_boundary_acceptance_package",
        "final_decision": "PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY" if ready else "BLOCKED",
    })
    return report
