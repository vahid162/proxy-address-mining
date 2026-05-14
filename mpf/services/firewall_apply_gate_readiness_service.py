from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services import firewall_no_customer_apply_acceptance_gate_service, firewall_no_customer_apply_execution_gate_service, firewall_no_customer_apply_scaffold_service, firewall_restore_lock_record_acceptance_gate_service, firewall_restore_lock_record_execution_gate_service, firewall_restore_lock_record_gate_service, firewall_restore_lock_record_readiness_service

_EXPECTED_CURRENT_STATE = {
    "current_accepted_phase": "Phase 5 — Customer CRUD in DB Only accepted on farm5",
    "current_working_phase": "Phase 6 — Firewall Planner",
    "server_state": "farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active",
    "production_traffic": "none",
    "firewall_apply_allowed": "no",
    "abuse_automation_allowed": "no",
    "customer_onboarding_allowed": "db_only",
    "proxy_data_plane_allowed": "limited_runtime_local_only",
    "ui_allowed": "no",
    "telegram_allowed": "no",
}


def _parse_current_state_block(text: str) -> dict[str, str] | None:
    marker = "## Current State"
    start = text.find(marker)
    if start < 0:
        return None
    code_start = text.find("```text", start)
    if code_start < 0:
        return None
    code_end = text.find("```", code_start + 7)
    if code_end < 0:
        return None
    lines = text[code_start + 7 : code_end].strip().splitlines()
    parsed: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed if parsed else None


def build_apply_gate_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"
    dedicated_doc = root / "docs" / "PHASE_6_DEDICATED_APPLY_GATE_PROPOSAL_REVIEW.md"

    blockers: list[str] = []
    missing_requirements: list[str] = []

    documentation_boundary_present = dedicated_doc.exists()
    if not documentation_boundary_present:
        missing_requirements.append("missing docs/PHASE_6_DEDICATED_APPLY_GATE_PROPOSAL_REVIEW.md")

    farm5_sync_evidence_present = False
    current_state_preserved = False

    if not phase_status.exists():
        blockers.append("docs/PHASE_STATUS.md is missing")
    else:
        text = phase_status.read_text(encoding="utf-8")
        farm5_sync_evidence_present = "version accepted on farm5: 0.1.88" in text and "Phase 6 Apply Gate Proposal Review — Documentation Sync" in text
        current_state = _parse_current_state_block(text)
        if current_state is None:
            blockers.append("Current State block missing or malformed in docs/PHASE_STATUS.md")
        else:
            current_state_preserved = all(current_state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
            if not current_state_preserved:
                blockers.append("Current State block does not match required phase gate values")

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    if not apply_mode_plan_only:
        blockers.append("firewall.apply_mode is not plan_only")

    if not farm5_sync_evidence_present:
        missing_requirements.append("missing farm5 0.1.88 sync evidence in docs/PHASE_STATUS.md")

    runtime_activation_allowed = bool(cfg.proxy.runtime_activation_allowed)
    if runtime_activation_allowed:
        blockers.append("proxy.runtime_activation_allowed is not false")

    restore_gate_report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(cfg, repo_root=root)
    restore_readiness_report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(cfg, repo_root=root)
    restore_acceptance_report = firewall_restore_lock_record_acceptance_gate_service.build_restore_lock_record_acceptance_gate_report(cfg, repo_root=root)
    restore_execution_report = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(cfg, repo_root=root)
    no_customer_apply_scaffold_report = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report(cfg, repo_root=root)
    no_customer_apply_acceptance_gate_report = firewall_no_customer_apply_acceptance_gate_service.build_no_customer_apply_acceptance_gate_report(cfg, repo_root=root)
    no_customer_apply_execution_gate_report = firewall_no_customer_apply_execution_gate_service.build_no_customer_apply_execution_gate_report(cfg, repo_root=root)

    report = {
        "component": "firewall_apply_gate_readiness",
        "final_decision": "BLOCKED",
        "phase": "Phase 6 — Firewall Planner",
        "current_accepted_phase": _EXPECTED_CURRENT_STATE["current_accepted_phase"],
        "future_gate": "Future Dedicated Phase 6 Apply Gate Proposal/Review",
        "documentation_boundary_present": documentation_boundary_present,
        "farm5_0_1_88_sync_evidence_present": farm5_sync_evidence_present,
        "current_state_preserved": current_state_preserved,
        "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_allowed": runtime_activation_allowed,
        "production_traffic": _EXPECTED_CURRENT_STATE["production_traffic"],
        "firewall_apply_allowed": _EXPECTED_CURRENT_STATE["firewall_apply_allowed"],
        "abuse_automation_allowed": _EXPECTED_CURRENT_STATE["abuse_automation_allowed"],
        "live_firewall_read_allowed": False,
        "live_firewall_write_allowed": False,
        "iptables_save_allowed": False,
        "iptables_restore_allowed": False,
        "real_adapter_allowed": False,
        "subprocess_firewall_calls_allowed": False,
        "restore_point_write_allowed": False,
        "lock_acquisition_allowed": False,
        "db_apply_write_allowed": False,
        "migrations_allowed": False,
        "live_snapshot_read_service_present": True,
        "live_snapshot_scaffold_present": True,
        "live_snapshot_authorization_status": "NOT_AUTHORIZED",
        "live_snapshot_final_decision": "BLOCKED",
        "live_snapshot_read_authorization_status": "NOT_AUTHORIZED",
        "live_snapshot_read_final_decision": "BLOCKED",
        "customer_nat_allowed": False,
        "customer_firewall_rules_allowed": False,
        "usage_automation_allowed": False,
        "abuse_automation_allowed_runtime": False,
        "ui_allowed_runtime": False,
        "telegram_allowed_runtime": False,
        "restore_lock_record_readiness_present": True,
        "restore_lock_record_readiness_authorization_status": restore_readiness_report["authorization_status"],
        "restore_lock_record_readiness_final_decision": restore_readiness_report["final_decision"],
        "restore_lock_record_gate_present": True,
        "restore_lock_record_gate_authorization_status": restore_gate_report["authorization_status"],
        "restore_lock_record_gate_final_decision": restore_gate_report["final_decision"],
        "restore_lock_record_acceptance_gate_present": True,
        "restore_lock_record_acceptance_gate_authorization_status": restore_acceptance_report["authorization_status"],
        "restore_lock_record_acceptance_gate_final_decision": restore_acceptance_report["final_decision"],
        "restore_lock_record_execution_gate_present": True,
        "restore_lock_record_execution_gate_authorization_status": restore_execution_report["authorization_status"],
        "restore_lock_record_execution_gate_final_decision": restore_execution_report["final_decision"],
        "restore_lock_record_execution_gate_execution_allowed": restore_execution_report["execution_allowed"],
        "no_customer_apply_scaffold_summary": {
            "no_customer_apply_scaffold_present": True,
            "no_customer_apply_scaffold_final_decision": no_customer_apply_scaffold_report["final_decision"],
            "no_customer_apply_scaffold_authorization_status": no_customer_apply_scaffold_report["authorization_status"],
            "no_customer_apply_scaffold_execution_allowed": no_customer_apply_scaffold_report["execution_allowed"],
            "no_customer_apply_scaffold_apply_decision": no_customer_apply_scaffold_report["apply_decision"],
            "no_customer_apply_scaffold_verify_decision": no_customer_apply_scaffold_report["verify_decision"],
            "no_customer_apply_scaffold_rollback_decision": no_customer_apply_scaffold_report["rollback_decision"],
        },
        "no_customer_apply_acceptance_gate_summary": {
            "no_customer_apply_acceptance_gate_present": True,
            "no_customer_apply_acceptance_gate_final_decision": no_customer_apply_acceptance_gate_report["final_decision"],
            "no_customer_apply_acceptance_gate_authorization_status": no_customer_apply_acceptance_gate_report["authorization_status"],
            "no_customer_apply_acceptance_gate_execution_allowed": no_customer_apply_acceptance_gate_report["execution_allowed"],
            "no_customer_apply_acceptance_gate_apply_decision": no_customer_apply_acceptance_gate_report["apply_decision"],
            "no_customer_apply_acceptance_gate_verify_decision": no_customer_apply_acceptance_gate_report["verify_decision"],
            "no_customer_apply_acceptance_gate_rollback_decision": no_customer_apply_acceptance_gate_report["rollback_decision"],
        },
        "no_customer_apply_execution_gate_summary": {
            "no_customer_apply_execution_gate_present": True,
            "no_customer_apply_execution_gate_final_decision": no_customer_apply_execution_gate_report["final_decision"],
            "no_customer_apply_execution_gate_authorization_status": no_customer_apply_execution_gate_report["authorization_status"],
            "no_customer_apply_execution_gate_execution_allowed": no_customer_apply_execution_gate_report["execution_allowed"],
            "no_customer_apply_execution_gate_apply_decision": no_customer_apply_execution_gate_report["apply_decision"],
            "no_customer_apply_execution_gate_verify_decision": no_customer_apply_execution_gate_report["verify_decision"],
            "no_customer_apply_execution_gate_rollback_decision": no_customer_apply_execution_gate_report["rollback_decision"],
        },
        "missing_requirements": missing_requirements,
        "blockers": blockers,
        "next_operator_action": "prepare separate explicit gate-opening proposal only after operator approval and required evidence; no runtime action is authorized now",
    }
    return report
