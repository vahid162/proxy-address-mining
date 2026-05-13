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


def build_live_snapshot_read_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"
    blockers: list[str] = []

    current_state_preserved = False
    if not phase_status.exists():
        blockers.append("docs/PHASE_STATUS.md is missing")
    else:
        current_state = _parse_current_state_block(phase_status.read_text(encoding="utf-8"))
        if current_state is None:
            blockers.append("Current State block missing or malformed in docs/PHASE_STATUS.md")
        else:
            current_state_preserved = all(current_state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
            if not current_state_preserved:
                blockers.append("Current State block does not match required phase gate values")
            if current_state.get("production_traffic") != "none":
                blockers.append("production_traffic is not none")
            if current_state.get("firewall_apply_allowed") != "no":
                blockers.append("firewall_apply_allowed is not no")
            if current_state.get("abuse_automation_allowed") != "no":
                blockers.append("abuse_automation_allowed is not no")
            if current_state.get("customer_onboarding_allowed") != "db_only":
                blockers.append("customer_onboarding_allowed is not db_only")
            if current_state.get("proxy_data_plane_allowed") != "limited_runtime_local_only":
                blockers.append("proxy_data_plane_allowed is not limited_runtime_local_only")
            if current_state.get("ui_allowed") != "no":
                blockers.append("ui_allowed is not no")
            if current_state.get("telegram_allowed") != "no":
                blockers.append("telegram_allowed is not no")

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    if not apply_mode_plan_only:
        blockers.append("firewall.apply_mode is not plan_only")

    runtime_activation_allowed = bool(cfg.proxy.runtime_activation_allowed)
    if runtime_activation_allowed:
        blockers.append("proxy.runtime_activation_allowed is true")

    return {
        "component": "firewall_live_snapshot_read",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_AUTHORIZED",
        "live_firewall_read_allowed": False,
        "live_firewall_read_executed": False,
        "iptables_save_allowed": False,
        "iptables_save_executed": False,
        "subprocess_allowed": False,
        "subprocess_executed": False,
        "filesystem_write_allowed": False,
        "filesystem_write_executed": False,
        "firewall_mutation": False,
        "db_mutation": False,
        "restore_point_written": False,
        "lock_acquired": False,
        "customer_nat_changed": False,
        "customer_firewall_rules_changed": False,
        "production_traffic_changed": False,
        "empty_snapshot_fallback_allowed": False,
        "guessed_state_allowed": False,
        "parser_input_source": "none",
        "snapshot_rule_count": 0,
        "snapshot_chain_count": 0,
        "snapshot_table_count": 0,
        "current_state_preserved": current_state_preserved,
        "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_allowed": runtime_activation_allowed,
        "blockers": blockers,
        "next_required_gate": "explicit docs/PHASE_STATUS.md acceptance plus farm5 evidence",
    }
