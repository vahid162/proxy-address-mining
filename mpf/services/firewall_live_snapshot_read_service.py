from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from mpf.config import MPFConfig
from mpf.services import firewall_snapshot_parser

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


def build_live_snapshot_read_report(cfg: MPFConfig, repo_root: Path | None = None, *, execute: bool = False) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"
    blockers: list[str] = []

    current_state_preserved = False
    gate_authorized = False
    if not phase_status.exists():
        blockers.append("docs/PHASE_STATUS.md is missing")
    else:
        current_state = _parse_current_state_block(phase_status.read_text(encoding="utf-8"))
        if current_state is None:
            blockers.append("Current State block missing or malformed in docs/PHASE_STATUS.md")
        else:
            current_state_preserved = all(current_state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
            gate_authorized = current_state.get("live_snapshot_read_allowed") == "iptables_save_read_only"
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
            if not gate_authorized:
                blockers.append("live_snapshot_read_allowed is not iptables_save_read_only")

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    if not apply_mode_plan_only:
        blockers.append("firewall.apply_mode is not plan_only")

    runtime_activation_allowed = bool(cfg.proxy.runtime_activation_allowed)
    if runtime_activation_allowed:
        blockers.append("proxy.runtime_activation_allowed is true")

    authorized = current_state_preserved and apply_mode_plan_only and (not runtime_activation_allowed) and gate_authorized
    report: dict[str, object] = {
        "component": "firewall_live_snapshot_read",
        "final_decision": "READY_FOR_READ_ONLY_SNAPSHOT" if authorized else "BLOCKED",
        "authorization_status": "AUTHORIZED_READ_ONLY" if authorized else "NOT_AUTHORIZED",
        "live_firewall_read_allowed": authorized,
        "live_firewall_read_executed": False,
        "iptables_save_allowed": authorized,
        "iptables_save_executed": False,
        "subprocess_allowed": authorized and execute,
        "subprocess_executed": False,
        "subprocess_args": [],
        "subprocess_returncode": None,
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
        "source_snapshot_sha256": None,
        "stdout_line_count": 0,
        "stderr_summary": "",
        "current_state_preserved": current_state_preserved,
        "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_allowed": runtime_activation_allowed,
        "blockers": blockers,
        "errors": [],
        "apply_decision": "BLOCKED",
        "next_required_gate": "explicit docs/PHASE_STATUS.md acceptance plus farm5 evidence",
    }
    if not execute:
        return report
    if not authorized:
        report["final_decision"] = "BLOCKED"
        report["errors"] = ["read-only execution requested but gate is not authorized"]
        return report
    cmd = ["iptables-save"]
    report["subprocess_args"] = cmd
    report["subprocess_executed"] = True
    report["iptables_save_executed"] = True
    report["live_firewall_read_executed"] = True
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        report["subprocess_returncode"] = proc.returncode
        report["stderr_summary"] = (proc.stderr or "").strip()[:500]
        if proc.returncode != 0:
            report["final_decision"] = "FAILED_READ_ONLY_SNAPSHOT"
            report["errors"] = ["iptables-save exited non-zero"]
            return report
        stdout = proc.stdout or ""
        if not stdout.strip():
            report["final_decision"] = "FAILED_READ_ONLY_SNAPSHOT"
            report["errors"] = ["iptables-save stdout is empty"]
            return report
        snap = firewall_snapshot_parser.parse_iptables_save_text(stdout)
        report["parser_input_source"] = "iptables-save stdout"
        report["snapshot_rule_count"] = len(snap.rules)
        report["snapshot_chain_count"] = len(snap.chains)
        report["snapshot_table_count"] = len({t for t, _ in snap.chains})
        report["stdout_line_count"] = len(stdout.splitlines())
        report["source_snapshot_sha256"] = hashlib.sha256(stdout.encode("utf-8")).hexdigest()
        report["final_decision"] = "READ_ONLY_SNAPSHOT_COLLECTED"
        return report
    except subprocess.TimeoutExpired:
        report["final_decision"] = "FAILED_READ_ONLY_SNAPSHOT"
        report["errors"] = ["iptables-save timed out"]
        report["stderr_summary"] = "timeout"
        return report
