from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig
from mpf.services import firewall_no_customer_apply_scaffold_service

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
    if code_start < 0:
        return None
    code_end = text.find("```", code_start + 7)
    if code_end < 0:
        return None
    parsed: dict[str, str] = {}
    for line in text[code_start + 7 : code_end].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed if parsed else None


def build_no_customer_apply_acceptance_gate_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"
    blockers: list[str] = []
    errors: list[str] = []

    current_state_preserved = False
    read_only_snapshot_evidence_present = False
    controlled_restore_lock_record_evidence_present = False
    dedicated_apply_gate_proposal_present = False
    no_customer_apply_scaffold_section_present = False

    if not phase_status.exists():
        blockers.append("historical phase-status archive is missing")
        text = ""
    else:
        text = phase_status.read_text(encoding="utf-8")
        current_state = _parse_current_state_block(text)
        if current_state is None:
            blockers.append("Current State block missing or malformed in docs/PHASE_STATUS.md")
        else:
            current_state_preserved = all(current_state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
            if not current_state_preserved:
                blockers.append("Current State block does not match required phase gate values")

        read_only_snapshot_evidence_present = "### Phase 6 Read-Only iptables-save Snapshot — Server Evidence" in text
        controlled_restore_lock_record_evidence_present = "### Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence" in text
        dedicated_apply_gate_proposal_present = "### Phase 6 Dedicated Apply Gate — Proposal Review" in text
        no_customer_apply_scaffold_section_present = "### Phase 6 No-Customer Apply/Verify/Rollback Scaffold — Report-Only" in text

        if not read_only_snapshot_evidence_present:
            blockers.append("missing Phase 6 Read-Only iptables-save Snapshot — Server Evidence section")
        if not controlled_restore_lock_record_evidence_present:
            blockers.append("missing Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence section")
        if "CONTROLLED_BOUNDARY_EXECUTED" not in text:
            blockers.append("missing CONTROLLED_BOUNDARY_EXECUTED evidence")
        if "restore_point_id=1" not in text:
            blockers.append("missing restore_point_id=1 evidence")
        if "firewall_apply_id=1" not in text:
            blockers.append("missing firewall_apply_id=1 evidence")
        if not dedicated_apply_gate_proposal_present:
            blockers.append("missing Phase 6 Dedicated Apply Gate — Proposal Review section")
        if not no_customer_apply_scaffold_section_present:
            blockers.append("missing Phase 6 No-Customer Apply/Verify/Rollback Scaffold — Report-Only section")

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    runtime_activation_allowed = bool(cfg.proxy.runtime_activation_allowed)
    if not apply_mode_plan_only:
        blockers.append("firewall.apply_mode is not plan_only")
    if runtime_activation_allowed:
        blockers.append("proxy.runtime_activation_allowed is true")

    scaffold = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report(cfg, repo_root=root)
    no_customer_apply_scaffold_report_present = bool(scaffold)
    no_customer_apply_scaffold_blocked = scaffold.get("final_decision") == "BLOCKED"
    no_customer_apply_scaffold_execution_disallowed = scaffold.get("execution_allowed") is False
    no_customer_apply_scaffold_mutation_flags_false = all(
        scaffold.get(k) is False
        for k in (
            "live_firewall_write_allowed", "live_firewall_apply_allowed", "live_firewall_verify_allowed", "live_firewall_rollback_allowed",
            "iptables_restore_allowed", "subprocess_firewall_calls_allowed", "real_adapter_allowed", "restore_point_write_allowed",
            "lock_acquisition_allowed", "db_apply_record_write_allowed", "db_mutation", "filesystem_write_executed",
            "customer_nat_allowed", "customer_firewall_rules_allowed", "production_traffic_changed",
        )
    )
    if not no_customer_apply_scaffold_report_present:
        blockers.append("no-customer scaffold report missing")
    if not no_customer_apply_scaffold_blocked:
        blockers.append("no-customer scaffold report is not BLOCKED")
    if not no_customer_apply_scaffold_execution_disallowed:
        blockers.append("no-customer scaffold execution_allowed is not false")
    if not no_customer_apply_scaffold_mutation_flags_false:
        blockers.append("no-customer scaffold mutation safety flags are not all false")

    checklist_ids = [
        "current_state_preserved","config_apply_mode_plan_only","proxy_runtime_activation_disabled",
        "read_only_snapshot_evidence_present","controlled_restore_lock_record_evidence_present","dedicated_apply_gate_proposal_present",
        "no_customer_apply_scaffold_present","no_customer_apply_scaffold_blocked","no_customer_apply_scaffold_execution_disallowed",
        "no_customer_apply_scaffold_mutation_flags_false","no_customer_nat","no_customer_firewall_rules","no_production_traffic",
        "no_usage_automation","no_abuse_automation","operator_approval_required_for_future_execution",
        "fresh_farm5_evidence_required_for_future_execution","rollback_plan_required_for_future_execution","verify_plan_required_for_future_execution",
    ]
    status_map = {
        "current_state_preserved": current_state_preserved,
        "config_apply_mode_plan_only": apply_mode_plan_only,
        "proxy_runtime_activation_disabled": not runtime_activation_allowed,
        "read_only_snapshot_evidence_present": read_only_snapshot_evidence_present,
        "controlled_restore_lock_record_evidence_present": controlled_restore_lock_record_evidence_present,
        "dedicated_apply_gate_proposal_present": dedicated_apply_gate_proposal_present,
        "no_customer_apply_scaffold_present": no_customer_apply_scaffold_report_present,
        "no_customer_apply_scaffold_blocked": no_customer_apply_scaffold_blocked,
        "no_customer_apply_scaffold_execution_disallowed": no_customer_apply_scaffold_execution_disallowed,
        "no_customer_apply_scaffold_mutation_flags_false": no_customer_apply_scaffold_mutation_flags_false,
        "no_customer_nat": True, "no_customer_firewall_rules": True, "no_production_traffic": True,
        "no_usage_automation": True, "no_abuse_automation": True,
        "operator_approval_required_for_future_execution": False,
        "fresh_farm5_evidence_required_for_future_execution": False,
        "rollback_plan_required_for_future_execution": False,
        "verify_plan_required_for_future_execution": False,
    }
    acceptance_checklist = [{"item": i, "status": "PASS" if status_map[i] else "BLOCKED"} for i in checklist_ids]

    return {
        "component": "firewall_no_customer_apply_acceptance_gate",
        "phase": "Phase 6 — Firewall Planner",
        "gate_type": "no_customer_apply_verify_rollback_explicit_acceptance",
        "final_decision": "BLOCKED",
        "authorization_status": "ACCEPTANCE_GATE_DEFINED_NOT_EXECUTABLE",
        "gate_status": "ACCEPTANCE_REPORT_ONLY",
        "inspection_only": True, "report_only": True, "preflight_only": True, "dry_run": True,
        "execution_allowed": False, "apply_decision": "BLOCKED", "verify_decision": "BLOCKED", "rollback_decision": "BLOCKED",
        "current_state_preserved": current_state_preserved, "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_allowed": runtime_activation_allowed,
        "read_only_snapshot_evidence_present": read_only_snapshot_evidence_present,
        "controlled_restore_lock_record_evidence_present": controlled_restore_lock_record_evidence_present,
        "dedicated_apply_gate_proposal_present": dedicated_apply_gate_proposal_present,
        "no_customer_apply_scaffold_section_present": no_customer_apply_scaffold_section_present,
        "no_customer_apply_scaffold_report_present": no_customer_apply_scaffold_report_present,
        "no_customer_apply_scaffold_blocked": no_customer_apply_scaffold_blocked,
        "no_customer_apply_scaffold_execution_disallowed": no_customer_apply_scaffold_execution_disallowed,
        "no_customer_apply_scaffold_mutation_flags_false": no_customer_apply_scaffold_mutation_flags_false,
        "production_traffic": "none", "firewall_apply_allowed": "no", "abuse_automation_allowed": "no",
        "live_snapshot_read_allowed": "iptables_save_read_only", "restore_lock_record_execution_allowed": "controlled_boundary_only",
        "acceptance_checklist": acceptance_checklist,
        "live_firewall_write_allowed": False, "live_firewall_apply_allowed": False, "live_firewall_verify_allowed": False,
        "live_firewall_rollback_allowed": False, "iptables_restore_allowed": False, "iptables_restore_executed": False,
        "subprocess_firewall_calls_allowed": False, "subprocess_firewall_calls_executed": False,
        "real_adapter_allowed": False, "real_adapter_executed": False,
        "restore_point_write_allowed": False, "restore_point_written": False,
        "lock_acquisition_allowed": False, "lock_acquired": False,
        "db_apply_record_write_allowed": False, "db_apply_record_written": False, "db_mutation": False,
        "filesystem_write_executed": False,
        "customer_nat_allowed": False, "customer_nat_changed": False,
        "customer_firewall_rules_allowed": False, "customer_firewall_rules_changed": False,
        "production_traffic_changed": False, "usage_automation_allowed": False,
        "abuse_automation_allowed_runtime": False, "ui_allowed_runtime": False, "telegram_allowed_runtime": False,
        "blockers": blockers, "errors": errors,
    }
