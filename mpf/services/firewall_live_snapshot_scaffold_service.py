from __future__ import annotations

from dataclasses import asdict, dataclass
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


@dataclass(frozen=True)
class LiveSnapshotScaffoldBlocker:
    reason: str


@dataclass(frozen=True)
class LiveSnapshotScaffoldReport:
    component: str
    final_decision: str
    authorization_status: str
    live_firewall_read_executed: bool
    iptables_save_executed: bool
    subprocess_executed: bool
    firewall_mutation: bool
    db_mutation: bool
    restore_point_written: bool
    lock_acquired: bool
    customer_nat_changed: bool
    customer_firewall_rules_changed: bool
    production_traffic_changed: bool
    allowed_future_operation: str
    failure_behavior: str
    empty_snapshot_fallback_allowed: bool
    guessed_state_allowed: bool
    apply_decision: str
    current_state_preserved: bool
    apply_mode_plan_only: bool
    runtime_activation_allowed: bool
    blockers: list[str]


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


def _build_blockers(cfg: MPFConfig, repo_root: Path) -> tuple[list[str], bool]:
    blockers: list[str] = []
    phase_status = repo_root / "docs" / "PHASE_STATUS.md"
    current_state_preserved = False
    if not phase_status.exists():
        blockers.append("docs/PHASE_STATUS.md is missing")
    else:
        parsed = _parse_current_state_block(phase_status.read_text(encoding="utf-8"))
        if parsed is None:
            blockers.append("Current State block missing or malformed in docs/PHASE_STATUS.md")
        else:
            current_state_preserved = all(parsed.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
            if not current_state_preserved:
                blockers.append("Current State block does not match required phase gate values")

    if cfg.firewall.apply_mode != "plan_only":
        blockers.append("firewall.apply_mode is not plan_only")

    if bool(cfg.proxy.runtime_activation_allowed):
        blockers.append("proxy.runtime_activation_allowed is not false")

    return blockers, current_state_preserved


def build_live_snapshot_scaffold_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    blockers, current_state_preserved = _build_blockers(cfg, root)
    report = LiveSnapshotScaffoldReport(
        component="firewall_live_snapshot_scaffold",
        final_decision="BLOCKED",
        authorization_status="NOT_AUTHORIZED",
        live_firewall_read_executed=False,
        iptables_save_executed=False,
        subprocess_executed=False,
        firewall_mutation=False,
        db_mutation=False,
        restore_point_written=False,
        lock_acquired=False,
        customer_nat_changed=False,
        customer_firewall_rules_changed=False,
        production_traffic_changed=False,
        allowed_future_operation="read-only live snapshot only after explicit docs/PHASE_STATUS.md acceptance",
        failure_behavior="fail_closed",
        empty_snapshot_fallback_allowed=False,
        guessed_state_allowed=False,
        apply_decision="BLOCKED",
        current_state_preserved=current_state_preserved,
        apply_mode_plan_only=cfg.firewall.apply_mode == "plan_only",
        runtime_activation_allowed=bool(cfg.proxy.runtime_activation_allowed),
        blockers=blockers,
    )
    return asdict(report)
