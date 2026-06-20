from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig
from mpf.services import firewall_apply_gate_readiness_service, firewall_no_customer_apply_execution_acceptance_service, firewall_no_customer_apply_execution_gate_service, firewall_no_customer_apply_package_service

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
    marker = "## Current State"
    start = text.find(marker)
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


def build_no_customer_runtime_execution_approval_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"
    blockers: list[str] = []
    errors: list[str] = []

    current_state_preserved = False
    farm5_0_1_93_sync_evidence_present = False
    gate_review_json_evidence_present = False
    gate_review_json_non_crashing_evidence_present = False
    gate_review_json_blocked = False
    gate_review_json_non_applyable = False
    gate_review_json_live_apply_disallowed = False
    phase_gate_firewall_apply_disallowed = False
    phase_gate_production_traffic_none = False
    phase_gate_abuse_automation_disallowed = False

    if not phase_status.exists():
        blockers.append("docs/PHASE_STATUS.md missing")
    else:
        text = phase_status.read_text(encoding="utf-8")
        state = _parse_current_state_block(text)
        if state is None:
            blockers.append("Current State missing or changed")
        else:
            current_state_preserved = all(state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
            if not current_state_preserved:
                blockers.append("Current State missing or changed")
            phase_gate_firewall_apply_disallowed = state.get("firewall_apply_allowed") == "no"
            phase_gate_production_traffic_none = state.get("production_traffic") == "none"
            phase_gate_abuse_automation_disallowed = state.get("abuse_automation_allowed") == "no"
        farm5_0_1_93_sync_evidence_present = "farm5 synced to 0.1.93" in text and "mpf --version: 0.1.93" in text
        gate_review_json_evidence_present = "PR #100 gate-review JSON serialization fix validated on farm5" in text
        gate_review_json_non_crashing_evidence_present = "completed without traceback" in text
        gate_review_json_blocked = "final_decision: BLOCKED" in text
        gate_review_json_non_applyable = "applyable: false" in text
        gate_review_json_live_apply_disallowed = "live_apply_allowed: false" in text

    if not farm5_0_1_93_sync_evidence_present:
        blockers.append("farm5 0.1.93 sync evidence missing")
    if not gate_review_json_evidence_present:
        blockers.append("gate-review JSON evidence missing")
    if not (gate_review_json_blocked and gate_review_json_non_applyable and gate_review_json_live_apply_disallowed):
        blockers.append("gate-review JSON evidence missing BLOCKED/non-applyable/live_apply_allowed=false")

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    runtime_activation_disabled = not bool(cfg.proxy.runtime_activation_allowed)
    if not apply_mode_plan_only:
        blockers.append("firewall.apply_mode is not plan_only")
    if not runtime_activation_disabled:
        blockers.append("proxy.runtime_activation_allowed is true")

    package = firewall_no_customer_apply_package_service.build_no_customer_apply_package_report(cfg, repo_root=root)
    acceptance = firewall_no_customer_apply_execution_acceptance_service.build_no_customer_apply_execution_acceptance_report(cfg, repo_root=root)
    execution_gate = firewall_no_customer_apply_execution_gate_service.build_no_customer_apply_execution_gate_report(cfg, repo_root=root)
    readiness = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg, repo_root=root, include_runtime_approval_summary=False, include_runtime_evidence_summary=False, include_manual_canary_summary=False)

    no_customer_apply_package_present = bool(package)
    no_customer_apply_package_blocked = package.get("final_decision") == "BLOCKED"
    no_customer_apply_package_execution_disallowed = not bool(package.get("execution_allowed", False))
    no_customer_apply_package_customer_safe = not any(package.get(k, False) for k in ("payload_contains_customer_nat", "payload_contains_customer_firewall_rules", "payload_contains_production_traffic", "payload_contains_iptables_restore"))

    no_customer_execution_acceptance_present = bool(acceptance)
    no_customer_execution_acceptance_blocked = acceptance.get("final_decision") == "BLOCKED"
    no_customer_execution_acceptance_execution_disallowed = not bool(acceptance.get("execution_allowed", False))

    no_customer_execution_gate_present = bool(execution_gate)
    no_customer_execution_gate_blocked = execution_gate.get("final_decision") == "BLOCKED"
    no_customer_execution_gate_execution_disallowed = not bool(execution_gate.get("execution_allowed", False))

    apply_gate_readiness_present = bool(readiness)
    apply_gate_readiness_blocked = readiness.get("final_decision") == "BLOCKED"

    for cond, msg in [
        (no_customer_apply_package_present, "no-customer package report missing"),
        (no_customer_apply_package_blocked, "no-customer package report not BLOCKED"),
        (no_customer_apply_package_execution_disallowed, "no-customer package report execution_allowed true"),
        (no_customer_apply_package_customer_safe, "no-customer package report customer_safe false"),
        (no_customer_execution_acceptance_present, "no-customer execution acceptance report missing"),
        (no_customer_execution_acceptance_blocked, "no-customer execution acceptance report not BLOCKED"),
        (no_customer_execution_acceptance_execution_disallowed, "no-customer execution acceptance execution_allowed true"),
        (no_customer_execution_gate_present, "no-customer execution gate report missing"),
        (no_customer_execution_gate_blocked, "no-customer execution gate not BLOCKED"),
        (no_customer_execution_gate_execution_disallowed, "no-customer execution gate execution_allowed true"),
        (apply_gate_readiness_present, "apply-gate-readiness missing"),
        (apply_gate_readiness_blocked, "apply-gate-readiness not BLOCKED"),
    ]:
        if not cond:
            blockers.append(msg)

    checklist = [
        ("current_state_preserved", current_state_preserved, "docs/PHASE_STATUS.md Current State matches required gate"),
        ("farm5_0_1_93_sync_evidence_present", farm5_0_1_93_sync_evidence_present, "farm5 sync 0.1.93 evidence recorded"),
        ("gate_review_json_evidence_present", gate_review_json_evidence_present, "PR #100 gate-review JSON evidence exists"),
        ("gate_review_json_blocked", gate_review_json_blocked, "gate-review JSON final_decision is BLOCKED"),
        ("gate_review_json_non_applyable", gate_review_json_non_applyable, "gate-review JSON applyable is false"),
        ("gate_review_json_live_apply_disallowed", gate_review_json_live_apply_disallowed, "gate-review JSON live_apply_allowed is false"),
        ("config_apply_mode_plan_only", apply_mode_plan_only, "firewall.apply_mode=plan_only"),
        ("proxy_runtime_activation_disabled", runtime_activation_disabled, "proxy.runtime_activation_allowed=false"),
        ("no_customer_apply_package_present", no_customer_apply_package_present, "no-customer apply package report exists"),
        ("no_customer_apply_package_customer_safe", no_customer_apply_package_customer_safe, "no customer NAT/rules/traffic/iptables_restore payload"),
        ("no_customer_apply_package_execution_disallowed", no_customer_apply_package_execution_disallowed, "package execution_allowed=false"),
        ("no_customer_execution_acceptance_present", no_customer_execution_acceptance_present, "execution acceptance report exists"),
        ("no_customer_execution_acceptance_execution_disallowed", no_customer_execution_acceptance_execution_disallowed, "execution acceptance execution_allowed=false"),
        ("no_customer_execution_gate_present", no_customer_execution_gate_present, "execution gate report exists"),
        ("no_customer_execution_gate_execution_disallowed", no_customer_execution_gate_execution_disallowed, "execution gate execution_allowed=false"),
        ("apply_gate_readiness_blocked", apply_gate_readiness_blocked, "apply-gate-readiness final_decision=BLOCKED"),
        ("no_customer_nat", True, "customer_nat_allowed remains false"),
        ("no_customer_firewall_rules", True, "customer_firewall_rules_allowed remains false"),
        ("no_production_traffic", True, "production_traffic remains none"),
        ("no_usage_automation", True, "usage automation remains disallowed"),
        ("no_abuse_automation", True, "abuse automation remains disallowed"),
        ("separate_operator_runtime_execution_approval_required", True, "operator approval is explicitly required"),
        ("fresh_farm5_runtime_execution_evidence_required", True, "fresh farm5 runtime evidence required"),
        ("separate_runtime_execution_pr_required", True, "separate runtime execution PR required"),
        ("explicit_verify_evidence_required", True, "verify evidence must be collected in a future PR"),
        ("explicit_rollback_evidence_required", True, "rollback evidence must be collected in a future PR"),
    ]

    report = {
        "component": "firewall_no_customer_runtime_execution_approval", "phase": "Phase 6 — Firewall Planner",
        "gate_type": "no_customer_runtime_execution_approval_readiness", "final_decision": "BLOCKED",
        "authorization_status": "RUNTIME_EXECUTION_APPROVAL_READY_BUT_NOT_GRANTED", "gate_status": "OPERATOR_APPROVAL_REQUIRED",
        "inspection_only": True, "report_only": True, "preflight_only": True, "dry_run": True,
        "execution_allowed": False, "operator_approval_required": True, "fresh_farm5_runtime_execution_evidence_required": True,
        "separate_runtime_execution_pr_required": True, "apply_decision": "BLOCKED", "verify_decision": "BLOCKED", "rollback_decision": "BLOCKED",
        "current_state_preserved": current_state_preserved, "farm5_0_1_93_sync_evidence_present": farm5_0_1_93_sync_evidence_present,
        "gate_review_json_evidence_present": gate_review_json_evidence_present, "gate_review_json_non_crashing_evidence_present": gate_review_json_non_crashing_evidence_present,
        "gate_review_json_blocked": gate_review_json_blocked, "gate_review_json_non_applyable": gate_review_json_non_applyable,
        "gate_review_json_live_apply_disallowed": gate_review_json_live_apply_disallowed, "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_disabled": runtime_activation_disabled, "no_customer_apply_package_present": no_customer_apply_package_present,
        "no_customer_apply_package_blocked": no_customer_apply_package_blocked, "no_customer_apply_package_execution_disallowed": no_customer_apply_package_execution_disallowed,
        "no_customer_apply_package_customer_safe": no_customer_apply_package_customer_safe, "no_customer_execution_acceptance_present": no_customer_execution_acceptance_present,
        "no_customer_execution_acceptance_blocked": no_customer_execution_acceptance_blocked, "no_customer_execution_acceptance_execution_disallowed": no_customer_execution_acceptance_execution_disallowed,
        "no_customer_execution_gate_present": no_customer_execution_gate_present, "no_customer_execution_gate_blocked": no_customer_execution_gate_blocked,
        "no_customer_execution_gate_execution_disallowed": no_customer_execution_gate_execution_disallowed, "apply_gate_readiness_present": apply_gate_readiness_present,
        "apply_gate_readiness_blocked": apply_gate_readiness_blocked, "phase_gate_firewall_apply_disallowed": phase_gate_firewall_apply_disallowed,
        "phase_gate_production_traffic_none": phase_gate_production_traffic_none, "phase_gate_abuse_automation_disallowed": phase_gate_abuse_automation_disallowed,
        "live_firewall_write_allowed": False, "live_firewall_apply_allowed": False, "live_firewall_verify_allowed": False, "live_firewall_rollback_allowed": False,
        "iptables_restore_allowed": False, "iptables_restore_executed": False, "iptables_save_executed": False, "subprocess_firewall_calls_allowed": False,
        "subprocess_firewall_calls_executed": False, "real_adapter_allowed": False, "real_adapter_executed": False, "db_mutation": False,
        "db_apply_record_write_allowed": False, "db_apply_record_written": False, "filesystem_write_executed": False, "restore_point_write_allowed": False,
        "restore_point_written": False, "lock_acquisition_allowed": False, "lock_acquired": False, "customer_nat_allowed": False,
        "customer_nat_changed": False, "customer_firewall_rules_allowed": False, "customer_firewall_rules_changed": False, "production_traffic_changed": False,
        "usage_automation_allowed": False, "abuse_automation_allowed_runtime": False, "ui_allowed_runtime": False, "telegram_allowed_runtime": False,
        "runtime_execution_approval_checklist": [{"item": i, "status": "PASS" if ok else "BLOCKED", "evidence": ev} for i, ok, ev in checklist],
        "future_operator_runtime_execution_runbook": {
            "title": "Future controlled no-customer runtime execution evidence collection (informational only)",
            "steps": [{"item": s, "executable": False, "executed": False} for s in [
                "confirm GitHub main and farm5 are synced", "confirm mpf --version", "run mpf config validate", "run mpf doctor", "run mpf db status",
                "run mpf proxy doctor", "run mpf firewall no-customer-apply-package --output json", "run mpf firewall no-customer-apply-execution-acceptance --output json",
                "run mpf firewall no-customer-runtime-execution-approval --output json", "run mpf firewall apply-gate-readiness --output json",
                "run mpf firewall gate-review --source config-only --output json", "confirm final_decision remains BLOCKED before any separate runtime execution PR",
                "collect no-customer apply/verify/rollback evidence in a future PR only after explicit operator approval",
            ]],
        },
        "blockers": blockers,
        "errors": errors,
    }
    return report
