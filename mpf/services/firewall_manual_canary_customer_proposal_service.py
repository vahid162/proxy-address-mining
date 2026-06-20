from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig
from mpf.services import firewall_apply_gate_readiness_service, firewall_no_customer_runtime_execution_approval_service, firewall_no_customer_runtime_execution_evidence_service

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
    "live_snapshot_read_allowed": "iptables_save_read_only",
    "restore_lock_record_execution_allowed": "controlled_boundary_only",
}

def _parse_current_state_block(text: str) -> dict[str, str] | None:
    start = text.find("## Current State")
    if start < 0:
        return None
    code_start = text.find("```text", start)
    code_end = text.find("```", code_start + 7) if code_start >= 0 else -1
    if code_start < 0 or code_end < 0:
        return None
    parsed: dict[str, str] = {}
    for line in text[code_start + 7 : code_end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            parsed[k.strip()] = v.strip()
    return parsed or None

def build_manual_canary_customer_proposal_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"
    blockers: list[str] = []

    text = ""
    if not phase_status.exists():
        blockers.append("docs/PHASE_STATUS.md missing")
    else:
        text = phase_status.read_text(encoding="utf-8")

    state = _parse_current_state_block(text) if text else None
    current_state_preserved = bool(state) and all(state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
    if not current_state_preserved:
        blockers.append("Current State missing or changed")

    farm5_0_1_95_sync_evidence_present = "farm5 synced to 0.1.95" in text and "mpf --version: 0.1.95" in text
    if not farm5_0_1_95_sync_evidence_present:
        blockers.append("farm5 0.1.95 sync evidence missing")

    controlled = firewall_no_customer_runtime_execution_evidence_service.build_no_customer_runtime_execution_evidence_report(cfg, repo_root=root)
    runtime = firewall_no_customer_runtime_execution_approval_service.build_no_customer_runtime_execution_approval_report(cfg, repo_root=root)
    readiness = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg, repo_root=root, include_runtime_approval_summary=False, include_runtime_evidence_summary=False, include_manual_canary_summary=False)

    controlled_present = bool(controlled)
    controlled_blocked = controlled.get("final_decision") == "BLOCKED"
    controlled_execution_disallowed = not bool(controlled.get("execution_allowed", False))
    runtime_present = bool(runtime)
    runtime_blocked = runtime.get("final_decision") == "BLOCKED"
    runtime_execution_disallowed = not bool(runtime.get("execution_allowed", False))
    readiness_present = bool(readiness)
    readiness_blocked = readiness.get("final_decision") == "BLOCKED"
    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    runtime_activation_disabled = not bool(cfg.proxy.runtime_activation_allowed)
    phase_gate_firewall_apply_disallowed = bool(state) and state.get("firewall_apply_allowed") == "no"
    phase_gate_production_traffic_none = bool(state) and state.get("production_traffic") == "none"
    phase_gate_abuse_automation_disallowed = bool(state) and state.get("abuse_automation_allowed") == "no"

    checks = [
        (controlled_present, "controlled no-customer runtime evidence missing"),
        (controlled_blocked, "controlled no-customer runtime evidence not BLOCKED"),
        (controlled_execution_disallowed, "controlled no-customer runtime evidence execution_allowed true"),
        (runtime_present, "runtime approval report missing"),
        (runtime_blocked, "runtime approval report not BLOCKED"),
        (runtime_execution_disallowed, "runtime approval execution_allowed true"),
        (readiness_present, "apply-gate-readiness missing"),
        (readiness_blocked, "apply-gate-readiness not BLOCKED"),
        (apply_mode_plan_only, "firewall.apply_mode is not plan_only"),
        (runtime_activation_disabled, "proxy.runtime_activation_allowed is true"),
        (phase_gate_firewall_apply_disallowed, "phase_gate_firewall_apply_disallowed is false"),
        (phase_gate_production_traffic_none, "phase_gate_production_traffic_none is false"),
        (phase_gate_abuse_automation_disallowed, "phase_gate_abuse_automation_disallowed is false"),
    ]
    for ok, msg in checks:
        if not ok:
            blockers.append(msg)

    report = {
        "component": "firewall_manual_canary_customer_proposal", "phase": "Phase 6 — Firewall Planner", "gate_type": "manual_canary_customer_nat_firewall_proposal",
        "final_decision": "BLOCKED", "authorization_status": "MANUAL_CANARY_PROPOSAL_DEFINED_NOT_AUTHORIZED", "proposal_status": "REVIEW_ONLY",
        "inspection_only": True, "report_only": True, "preflight_only": True, "dry_run": True, "execution_allowed": False,
        "customer_nat_authorized": False, "customer_firewall_rules_authorized": False, "production_traffic_authorized": False,
        "operator_approval_required": True, "separate_canary_acceptance_pr_required": True, "fresh_farm5_canary_evidence_required": True,
        "apply_decision": "BLOCKED", "verify_decision": "BLOCKED", "rollback_decision": "BLOCKED",
        "current_state_preserved": current_state_preserved, "farm5_0_1_95_sync_evidence_present": farm5_0_1_95_sync_evidence_present,
        "controlled_no_customer_runtime_evidence_present": controlled_present, "controlled_no_customer_runtime_evidence_blocked": controlled_blocked,
        "controlled_no_customer_runtime_evidence_execution_disallowed": controlled_execution_disallowed,
        "runtime_approval_report_present": runtime_present, "runtime_approval_report_blocked": runtime_blocked, "runtime_approval_execution_disallowed": runtime_execution_disallowed,
        "apply_gate_readiness_present": readiness_present, "apply_gate_readiness_blocked": readiness_blocked,
        "apply_mode_plan_only": apply_mode_plan_only, "runtime_activation_disabled": runtime_activation_disabled,
        "phase_gate_firewall_apply_disallowed": phase_gate_firewall_apply_disallowed, "phase_gate_production_traffic_none": phase_gate_production_traffic_none,
        "phase_gate_abuse_automation_disallowed": phase_gate_abuse_automation_disallowed,
        "customer_nat_disallowed": True, "customer_firewall_rules_disallowed": True, "production_traffic_none": True, "usage_automation_disallowed": True, "abuse_automation_disallowed": True,
        "live_firewall_write_allowed": False, "live_firewall_apply_allowed": False, "live_firewall_verify_allowed": False, "live_firewall_rollback_allowed": False,
        "iptables_restore_allowed": False, "iptables_restore_executed": False, "subprocess_firewall_calls_allowed": False, "subprocess_firewall_calls_executed": False,
        "real_adapter_allowed": False, "real_adapter_executed": False, "db_mutation": False, "db_apply_record_write_allowed": False, "db_apply_record_written": False,
        "filesystem_write_executed": False, "restore_point_write_allowed": False, "restore_point_written": False, "lock_acquisition_allowed": False, "lock_acquired": False,
        "customer_nat_allowed": False, "customer_nat_changed": False, "customer_firewall_rules_allowed": False, "customer_firewall_rules_changed": False,
        "production_traffic_changed": False, "usage_automation_allowed": False, "abuse_automation_allowed_runtime": False, "ui_allowed_runtime": False, "telegram_allowed_runtime": False,
        "future_manual_canary_customer_proposal": {"candidate_customer_required": True, "current_non_deleted_customer_required_for_execution": True, "current_server_has_no_non_deleted_customers": True if "no non-deleted customers" in text else "unknown", "canary_scope": "one manually selected customer only", "lane_scope": "one lane only", "production_traffic_authorized": False, "customer_nat_authorized": False, "customer_firewall_rules_authorized": False, "rollback_required_before_apply": True, "verify_required_after_apply": True, "explicit_operator_approval_required": True, "separate_server_evidence_required": True},
    }
    report["manual_canary_customer_proposal_checklist"] = []
    report["blockers"] = blockers
    report["errors"] = []
    return report
