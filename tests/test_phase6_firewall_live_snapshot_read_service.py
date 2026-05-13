from __future__ import annotations

from pathlib import Path

from mpf.config import load_config
from mpf.services.firewall_live_snapshot_read_service import build_live_snapshot_read_report
from tests.test_smoke import example_config_path


def _cfg():
    return load_config(example_config_path())


def test_live_snapshot_read_report_ready_but_not_executed() -> None:
    report = build_live_snapshot_read_report(_cfg())
    assert report["final_decision"] == "READY_FOR_READ_ONLY_SNAPSHOT"
    assert report["authorization_status"] == "AUTHORIZED_READ_ONLY"
    for key in (
        "live_firewall_read_allowed","live_firewall_read_executed","iptables_save_allowed","iptables_save_executed",
        "subprocess_allowed","subprocess_executed","filesystem_write_executed","firewall_mutation","db_mutation",
        "restore_point_written","lock_acquired","customer_nat_changed","customer_firewall_rules_changed",
        "production_traffic_changed","empty_snapshot_fallback_allowed","guessed_state_allowed",
    ):
        expected = False if key not in ("live_firewall_read_allowed", "iptables_save_allowed") else True
        assert report[key] is expected


def test_live_snapshot_read_blocks_on_current_state_mismatch(tmp_path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "PHASE_STATUS.md").write_text("## Current State\n```text\nproduction_traffic: some\n```\n", encoding="utf-8")
    report = build_live_snapshot_read_report(_cfg(), repo_root=tmp_path)
    assert any("Current State block does not match" in b for b in report["blockers"])


def test_live_snapshot_read_blocks_on_non_plan_only(monkeypatch) -> None:
    cfg = _cfg()
    monkeypatch.setattr(cfg.firewall, "apply_mode", "manual_apply")
    report = build_live_snapshot_read_report(cfg)
    assert "firewall.apply_mode is not plan_only" in report["blockers"]


def test_live_snapshot_read_blocks_on_runtime_activation(monkeypatch) -> None:
    cfg = _cfg()
    monkeypatch.setattr(cfg.proxy, "runtime_activation_allowed", True)
    report = build_live_snapshot_read_report(cfg)
    assert "proxy.runtime_activation_allowed is true" in report["blockers"]


def test_live_snapshot_read_service_has_no_forbidden_execution_calls() -> None:
    src = Path("mpf/services/firewall_live_snapshot_read_service.py").read_text(encoding="utf-8")
    assert "shell=True" not in src
    for forbidden in ("os.system", "iptables-restore", "nft", "docker", "systemctl", "conntrack"):
        assert forbidden not in src


def test_live_snapshot_read_current_state_preserved_is_true() -> None:
    report = build_live_snapshot_read_report(_cfg())
    assert report["current_state_preserved"] is True


def test_live_snapshot_read_missing_gate_is_not_authorized(tmp_path) -> None:
    report = _with_overrides(tmp_path)
    assert report["authorization_status"] == "NOT_AUTHORIZED"
    assert report["final_decision"] == "BLOCKED"


def _with_overrides(tmp_path, **overrides):
    docs = tmp_path / "docs"
    docs.mkdir()
    state = {
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
    state.update(overrides)
    body = "\n".join(f"{k}: {v}" for k, v in state.items())
    (docs / "PHASE_STATUS.md").write_text(f"## Current State\n```text\n{body}\n```\n", encoding="utf-8")
    return build_live_snapshot_read_report(_cfg(), repo_root=tmp_path)


def test_live_snapshot_read_blocks_when_ui_allowed_yes(tmp_path) -> None:
    report = _with_overrides(tmp_path, ui_allowed="yes")
    assert "ui_allowed is not no" in report["blockers"]


def test_live_snapshot_read_blocks_when_telegram_allowed_yes(tmp_path) -> None:
    report = _with_overrides(tmp_path, telegram_allowed="yes")
    assert "telegram_allowed is not no" in report["blockers"]


def test_live_snapshot_read_blocks_when_proxy_data_plane_changed(tmp_path) -> None:
    report = _with_overrides(tmp_path, proxy_data_plane_allowed="runtime_full")
    assert "proxy_data_plane_allowed is not limited_runtime_local_only" in report["blockers"]
