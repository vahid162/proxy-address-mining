from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import historical_phase_status_path, read_historical_phase_status

from mpf.config import MPFConfig
from mpf.services import firewall_manual_canary_customer_acceptance_readiness_service, firewall_manual_canary_customer_proposal_service, firewall_manual_canary_customer_server_evidence_service, firewall_no_customer_apply_acceptance_gate_service, phase6_final_acceptance_readiness_service, phase6_final_acceptance_review_service, phase6_operator_acceptance_decision_service, firewall_no_customer_apply_execution_acceptance_service, firewall_no_customer_apply_execution_gate_service, firewall_no_customer_apply_package_service, firewall_no_customer_apply_scaffold_service, firewall_no_customer_runtime_execution_approval_service, firewall_no_customer_runtime_execution_evidence_service, firewall_restore_lock_record_acceptance_gate_service, firewall_restore_lock_record_execution_gate_service, firewall_restore_lock_record_gate_service, firewall_restore_lock_record_readiness_service

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


def build_apply_gate_readiness_report(cfg: MPFConfig, repo_root: Path | None = None, include_runtime_approval_summary: bool = True, include_runtime_evidence_summary: bool = True, include_manual_canary_summary: bool = True, include_manual_canary_server_evidence_summary: bool = False, include_phase6_final_acceptance_summary: bool = False, include_phase6_final_acceptance_review_summary: bool = False, include_phase6_operator_acceptance_decision_summary: bool = False) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = historical_phase_status_path(root)
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
    no_customer_apply_package_report = firewall_no_customer_apply_package_service.build_no_customer_apply_package_report(cfg, repo_root=root)
    no_customer_apply_execution_acceptance_report = firewall_no_customer_apply_execution_acceptance_service.build_no_customer_apply_execution_acceptance_report(cfg, repo_root=root)

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
        "no_customer_apply_package_summary": {
            "no_customer_apply_package_present": True,
            "no_customer_apply_package_final_decision": no_customer_apply_package_report["final_decision"],
            "no_customer_apply_package_authorization_status": no_customer_apply_package_report["authorization_status"],
            "no_customer_apply_package_execution_allowed": no_customer_apply_package_report["execution_allowed"],
            "no_customer_apply_package_customer_safe": True,
        },
        "no_customer_apply_execution_acceptance_summary": {
            "no_customer_apply_execution_acceptance_present": True,
            "no_customer_apply_execution_acceptance_final_decision": no_customer_apply_execution_acceptance_report["final_decision"],
            "no_customer_apply_execution_acceptance_authorization_status": no_customer_apply_execution_acceptance_report["authorization_status"],
            "no_customer_apply_execution_acceptance_execution_allowed": no_customer_apply_execution_acceptance_report["execution_allowed"],
            "no_customer_apply_execution_acceptance_apply_decision": no_customer_apply_execution_acceptance_report["apply_decision"],
            "no_customer_apply_execution_acceptance_verify_decision": no_customer_apply_execution_acceptance_report["verify_decision"],
            "no_customer_apply_execution_acceptance_rollback_decision": no_customer_apply_execution_acceptance_report["rollback_decision"],
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


    if include_manual_canary_summary:
        proposal = firewall_manual_canary_customer_proposal_service.build_manual_canary_customer_proposal_report(cfg, repo_root=root)
        acceptance = firewall_manual_canary_customer_acceptance_readiness_service.build_manual_canary_customer_acceptance_readiness_report(cfg, repo_root=root)
        report["manual_canary_customer_proposal_summary"] = {
            "manual_canary_customer_proposal_present": True,
            "manual_canary_customer_proposal_final_decision": proposal["final_decision"],
            "manual_canary_customer_proposal_authorization_status": proposal["authorization_status"],
            "manual_canary_customer_proposal_execution_allowed": proposal["execution_allowed"],
            "manual_canary_customer_proposal_customer_nat_authorized": proposal["customer_nat_authorized"],
            "manual_canary_customer_proposal_customer_firewall_rules_authorized": proposal["customer_firewall_rules_authorized"],
            "manual_canary_customer_proposal_fresh_farm5_canary_evidence_required": proposal["fresh_farm5_canary_evidence_required"],
        }
        report["manual_canary_customer_acceptance_readiness_summary"] = {
            "manual_canary_customer_acceptance_readiness_present": True,
            "manual_canary_customer_acceptance_readiness_final_decision": acceptance["final_decision"],
            "manual_canary_customer_acceptance_readiness_authorization_status": acceptance["authorization_status"],
            "manual_canary_customer_acceptance_readiness_execution_allowed": acceptance["execution_allowed"],
            "manual_canary_customer_acceptance_readiness_customer_nat_authorized": acceptance["customer_nat_authorized"],
            "manual_canary_customer_acceptance_readiness_customer_firewall_rules_authorized": acceptance["customer_firewall_rules_authorized"],
            "manual_canary_customer_acceptance_readiness_fresh_farm5_canary_evidence_required": acceptance["fresh_farm5_canary_evidence_required"],
        }

    if include_runtime_evidence_summary:
        evidence = firewall_no_customer_runtime_execution_evidence_service.build_no_customer_runtime_execution_evidence_report(cfg, repo_root=root)
        report["no_customer_runtime_execution_evidence_summary"] = {
            "no_customer_runtime_execution_evidence_present": True,
            "no_customer_runtime_execution_evidence_final_decision": evidence["final_decision"],
            "no_customer_runtime_execution_evidence_authorization_status": evidence["authorization_status"],
            "no_customer_runtime_execution_evidence_execution_allowed": evidence["execution_allowed"],
            "no_customer_runtime_execution_evidence_fresh_farm5_runtime_execution_evidence_required": evidence["fresh_farm5_runtime_execution_evidence_required"],
        }
    if include_runtime_approval_summary:
        runtime = firewall_no_customer_runtime_execution_approval_service.build_no_customer_runtime_execution_approval_report(cfg, repo_root=root)
        report["no_customer_runtime_execution_approval_summary"] = {
            "no_customer_runtime_execution_approval_present": True,
            "no_customer_runtime_execution_approval_final_decision": runtime["final_decision"],
            "no_customer_runtime_execution_approval_authorization_status": runtime["authorization_status"],
            "no_customer_runtime_execution_approval_execution_allowed": runtime["execution_allowed"],
            "no_customer_runtime_execution_approval_operator_approval_required": runtime["operator_approval_required"],
            "no_customer_runtime_execution_approval_fresh_farm5_runtime_execution_evidence_required": runtime["fresh_farm5_runtime_execution_evidence_required"],
            "no_customer_runtime_execution_approval_separate_runtime_execution_pr_required": runtime["separate_runtime_execution_pr_required"],
        }

    if include_manual_canary_server_evidence_summary:
        canary_server = firewall_manual_canary_customer_server_evidence_service.build_manual_canary_customer_server_evidence_report(cfg, repo_root=root)
        report["manual_canary_customer_server_evidence_summary"] = {
            "manual_canary_customer_server_evidence_present": True,
            "manual_canary_customer_server_evidence_final_decision": canary_server.get("final_decision", "BLOCKED"),
            "manual_canary_customer_server_evidence_authorization_status": canary_server.get("authorization_status", "MANUAL_CANARY_SERVER_EVIDENCE_NOT_ACCEPTED"),
            "manual_canary_customer_server_evidence_execution_allowed": bool(canary_server.get("execution_allowed", False)),
            "manual_canary_customer_server_evidence_customer_nat_authorized": bool(canary_server.get("customer_nat_authorized", False)),
            "manual_canary_customer_server_evidence_customer_firewall_rules_authorized": bool(canary_server.get("customer_firewall_rules_authorized", False)),
            "manual_canary_customer_server_evidence_fresh_farm5_canary_execution_evidence_required": bool(canary_server.get("fresh_farm5_canary_execution_evidence_required", True)),
        }
    if include_phase6_final_acceptance_summary:
        phase6 = phase6_final_acceptance_readiness_service.build_phase6_final_acceptance_readiness_report(cfg, repo_root=root)
        report["phase6_final_acceptance_readiness_summary"] = {
            "phase6_final_acceptance_readiness_present": True,
            "phase6_final_acceptance_readiness_final_decision": phase6.get("final_decision", "BLOCKED"),
            "phase6_final_acceptance_readiness_acceptance_status": phase6.get("acceptance_status", "PHASE6_NOT_ACCEPTED"),
            "phase6_final_acceptance_readiness_phase6_acceptance_allowed": bool(phase6.get("phase6_acceptance_allowed", False)),
            "phase6_final_acceptance_readiness_execution_allowed": bool(phase6.get("execution_allowed", False)),
            "phase6_final_acceptance_readiness_fresh_farm5_final_acceptance_evidence_required": bool(phase6.get("fresh_farm5_final_acceptance_evidence_required", True)),
        }

    if include_phase6_final_acceptance_review_summary:
        phase6r = phase6_final_acceptance_review_service.build_phase6_final_acceptance_review_report(cfg, repo_root=root)
        report["phase6_final_acceptance_review_summary"] = {
            "phase6_final_acceptance_review_present": True,
            "phase6_final_acceptance_review_final_decision": phase6r.get("final_decision", "BLOCKED"),
            "phase6_final_acceptance_review_review_status": phase6r.get("review_status", "READY_FOR_OPERATOR_REVIEW_BUT_NOT_ACCEPTED"),
            "phase6_final_acceptance_review_acceptance_status": phase6r.get("acceptance_status", "PHASE6_NOT_ACCEPTED"),
            "phase6_final_acceptance_review_phase6_acceptance_allowed": bool(phase6r.get("phase6_acceptance_allowed", False)),
            "phase6_final_acceptance_review_execution_allowed": bool(phase6r.get("execution_allowed", False)),
            "phase6_final_acceptance_review_phase7_start_allowed": bool(phase6r.get("phase7_start_allowed", False)),
            "phase6_final_acceptance_review_phase8_start_allowed": bool(phase6r.get("phase8_start_allowed", False)),
            "phase6_final_acceptance_review_fresh_farm5_0_1_99_sync_evidence_required": bool(phase6r.get("fresh_farm5_0_1_99_sync_evidence_required", True)),
        }


    if include_phase6_operator_acceptance_decision_summary:
        phase6d = phase6_operator_acceptance_decision_service.build_phase6_operator_acceptance_decision_report(cfg, repo_root=root)
        report["phase6_operator_acceptance_decision_summary"] = {
            "phase6_operator_acceptance_decision_present": True,
            "phase6_operator_acceptance_decision_final_decision": phase6d.get("final_decision", "BLOCKED"),
            "phase6_operator_acceptance_decision_acceptance_status": phase6d.get("acceptance_status", "PHASE6_NOT_ACCEPTED"),
            "phase6_operator_acceptance_decision_phase6_accepted": bool(phase6d.get("phase6_accepted", False)),
            "phase6_operator_acceptance_decision_phase7_start_allowed": bool(phase6d.get("phase7_start_allowed", False)),
            "phase6_operator_acceptance_decision_phase8_start_allowed": bool(phase6d.get("phase8_start_allowed", False)),
            "phase6_operator_acceptance_decision_runtime_gates_closed": bool(phase6d.get("phase6_runtime_gates_closed", False)),
            "phase6_operator_acceptance_decision_execution_allowed": bool(phase6d.get("execution_allowed", False)),
        }
    return report
