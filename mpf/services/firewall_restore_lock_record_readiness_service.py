from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import historical_phase_status_path, read_historical_phase_status

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
}

_EVIDENCE_HEADER = "Phase 6 Read-Only iptables-save Snapshot — Server Evidence"


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


def build_restore_lock_record_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = historical_phase_status_path(root)

    blockers: list[str] = []
    warnings = [
        "time_sync_required_before_future_write_gate: true",
        "farm5 time synchronization must be fixed and evidenced before any future restore point, lock, DB apply-write, production traffic, usage automation, or abuse automation gate.",
    ]
    errors: list[str] = []

    current_state_preserved = False
    read_only_snapshot_gate_authorized = False
    read_only_snapshot_evidence_present = False
    current_state: dict[str, str] | None = None

    if not phase_status.exists():
        blockers.append("docs/PHASE_STATUS.md is missing")
    else:
        text = phase_status.read_text(encoding="utf-8")
        current_state = _parse_current_state_block(text)
        if current_state is None:
            blockers.append("Current State block is missing or malformed")
        else:
            current_state_preserved = all(current_state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
            if not current_state_preserved:
                blockers.append("Current State does not match required gate")
            read_only_snapshot_gate_authorized = current_state.get("live_snapshot_read_allowed") == "iptables_save_read_only"
            if not read_only_snapshot_gate_authorized:
                blockers.append("live_snapshot_read_allowed is not iptables_save_read_only")
        read_only_snapshot_evidence_present = _EVIDENCE_HEADER in text
        if not read_only_snapshot_evidence_present:
            blockers.append("PR #79 read-only snapshot evidence section is missing")

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    if not apply_mode_plan_only:
        blockers.append("firewall.apply_mode is not plan_only")

    runtime_activation_allowed = bool(cfg.proxy.runtime_activation_allowed)
    if runtime_activation_allowed:
        blockers.append("proxy.runtime_activation_allowed is true")

    return {
        "component": "firewall_restore_lock_record_readiness",
        "phase": "Phase 6 — Firewall Planner",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_AUTHORIZED_FOR_WRITES",
        "inspection_only": True,
        "report_only": True,
        "current_state_preserved": current_state_preserved,
        "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_allowed": runtime_activation_allowed,
        "production_traffic": "none",
        "firewall_apply_allowed": "no",
        "abuse_automation_allowed": "no",
        "live_snapshot_read_allowed": "iptables_save_read_only",
        "read_only_snapshot_gate_authorized": read_only_snapshot_gate_authorized,
        "read_only_snapshot_evidence_present": read_only_snapshot_evidence_present,
        "restore_point_write_allowed": False,
        "restore_point_written": False,
        "firewall_snapshot_write_allowed": False,
        "firewall_snapshot_written": False,
        "lock_acquisition_allowed": False,
        "lock_acquired": False,
        "lock_file_write_allowed": False,
        "lock_file_written": False,
        "scheduler_lock_write_allowed": False,
        "scheduler_lock_written": False,
        "db_apply_record_write_allowed": False,
        "db_apply_record_written": False,
        "db_mutation": False,
        "migration_allowed": False,
        "migration_executed": False,
        "live_firewall_write_allowed": False,
        "live_firewall_apply_allowed": False,
        "live_firewall_rollback_allowed": False,
        "live_firewall_verify_allowed": False,
        "iptables_restore_allowed": False,
        "iptables_restore_executed": False,
        "customer_nat_allowed": False,
        "customer_nat_changed": False,
        "customer_firewall_rules_allowed": False,
        "customer_firewall_rules_changed": False,
        "production_traffic_changed": False,
        "usage_automation_allowed": False,
        "abuse_automation_allowed_runtime": False,
        "ui_allowed_runtime": False,
        "telegram_allowed_runtime": False,
        "time_sync_required_before_future_write_gate": True,
        "time_sync_note": "farm5 time synchronization must be fixed and evidenced before any future restore point, lock, DB apply-write, production traffic, usage automation, or abuse automation gate.",
        "apply_decision": "BLOCKED",
        "next_required_gate": "explicit restore point + lock + DB apply record gate acceptance with farm5 evidence",
        "blockers": blockers,
        "warnings": warnings,
        "errors": errors,
    }
