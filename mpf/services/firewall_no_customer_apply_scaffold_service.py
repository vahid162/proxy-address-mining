from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig

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
    lines = text[code_start + 7 : code_end].strip().splitlines()
    parsed: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed if parsed else None


def build_no_customer_apply_scaffold_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"

    blockers: list[str] = []
    errors: list[str] = []

    current_state_preserved = False
    dedicated_apply_gate_proposal_present = False
    read_only_snapshot_evidence_present = False
    controlled_restore_lock_record_evidence_present = False

    if not phase_status.exists():
        blockers.append("docs/PHASE_STATUS.md is missing")
    else:
        text = phase_status.read_text(encoding="utf-8")
        current_state = _parse_current_state_block(text)
        if current_state is None:
            blockers.append("Current State block missing or malformed in docs/PHASE_STATUS.md")
        else:
            current_state_preserved = all(current_state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
            if not current_state_preserved:
                blockers.append("Current State block does not match required phase gate values")

        dedicated_apply_gate_proposal_present = "### Phase 6 Dedicated Apply Gate — Proposal Review" in text
        if not dedicated_apply_gate_proposal_present:
            blockers.append("missing Phase 6 Dedicated Apply Gate — Proposal Review section")

        read_only_snapshot_evidence_present = "### Phase 6 Read-Only iptables-save Snapshot — Server Evidence" in text
        if not read_only_snapshot_evidence_present:
            blockers.append("missing Phase 6 Read-Only iptables-save Snapshot — Server Evidence section")

        controlled_restore_lock_record_evidence_present = "### Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence" in text
        if not controlled_restore_lock_record_evidence_present:
            blockers.append("missing Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence section")

        if "CONTROLLED_BOUNDARY_EXECUTED" not in text:
            blockers.append("missing CONTROLLED_BOUNDARY_EXECUTED evidence")
        if "restore_point_id=1" not in text:
            blockers.append("missing restore_point_id=1 evidence")
        if "firewall_apply_id=1" not in text:
            blockers.append("missing firewall_apply_id=1 evidence")

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    if not apply_mode_plan_only:
        blockers.append("firewall.apply_mode is not plan_only")

    runtime_activation_allowed = bool(cfg.proxy.runtime_activation_allowed)
    if runtime_activation_allowed:
        blockers.append("proxy.runtime_activation_allowed is not false")

    future_sequence = [
        "load current state",
        "use read-only snapshot evidence",
        "use restore point + scoped lock + DB apply record boundary evidence",
        "prepare no-customer-safe payload",
        "apply no-customer-safe payload",
        "verify no-customer result",
        "rollback no-customer result",
        "record evidence",
    ]

    report: dict[str, object] = {
        "component": "firewall_no_customer_apply_scaffold",
        "phase": "Phase 6 — Firewall Planner",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_AUTHORIZED_FOR_APPLY",
        "gate_status": "SCAFFOLD_ONLY",
        "inspection_only": True,
        "report_only": True,
        "preflight_only": True,
        "dry_run": True,
        "execution_allowed": False,
        "apply_decision": "BLOCKED",
        "verify_decision": "BLOCKED",
        "rollback_decision": "BLOCKED",
        "current_state_preserved": current_state_preserved,
        "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_allowed": runtime_activation_allowed,
        "production_traffic": "none",
        "firewall_apply_allowed": "no",
        "abuse_automation_allowed": "no",
        "live_snapshot_read_allowed": "iptables_save_read_only",
        "restore_lock_record_execution_allowed": "controlled_boundary_only",
        "read_only_snapshot_evidence_present": read_only_snapshot_evidence_present,
        "controlled_restore_lock_record_evidence_present": controlled_restore_lock_record_evidence_present,
        "dedicated_apply_gate_proposal_present": dedicated_apply_gate_proposal_present,
        "future_sequence_modeled": [{"step": s, "executed": False} for s in future_sequence],
        "live_firewall_write_allowed": False,
        "live_firewall_apply_allowed": False,
        "live_firewall_verify_allowed": False,
        "live_firewall_rollback_allowed": False,
        "iptables_restore_allowed": False,
        "iptables_restore_executed": False,
        "subprocess_firewall_calls_allowed": False,
        "subprocess_firewall_calls_executed": False,
        "real_adapter_allowed": False,
        "real_adapter_executed": False,
        "restore_point_write_allowed": False,
        "restore_point_written": False,
        "lock_acquisition_allowed": False,
        "lock_acquired": False,
        "db_apply_record_write_allowed": False,
        "db_apply_record_written": False,
        "db_mutation": False,
        "filesystem_write_executed": False,
        "customer_nat_allowed": False,
        "customer_nat_changed": False,
        "customer_firewall_rules_allowed": False,
        "customer_firewall_rules_changed": False,
        "production_traffic_changed": False,
        "usage_automation_allowed": False,
        "abuse_automation_allowed_runtime": False,
        "ui_allowed_runtime": False,
        "telegram_allowed_runtime": False,
        "blockers": blockers,
        "errors": errors,
    }
    return report
