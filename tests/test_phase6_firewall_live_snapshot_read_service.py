from __future__ import annotations

from pathlib import Path

from mpf.config import load_config
from mpf.services.firewall_live_snapshot_read_service import build_live_snapshot_read_report
from tests.test_smoke import example_config_path


def _cfg():
    return load_config(example_config_path())


def test_live_snapshot_read_report_blocked_and_not_authorized() -> None:
    report = build_live_snapshot_read_report(_cfg())
    assert report["final_decision"] == "BLOCKED"
    assert report["authorization_status"] == "NOT_AUTHORIZED"
    for key in (
        "live_firewall_read_allowed","live_firewall_read_executed","iptables_save_allowed","iptables_save_executed",
        "subprocess_allowed","subprocess_executed","filesystem_write_executed","firewall_mutation","db_mutation",
        "restore_point_written","lock_acquired","customer_nat_changed","customer_firewall_rules_changed",
        "production_traffic_changed","empty_snapshot_fallback_allowed","guessed_state_allowed",
    ):
        assert report[key] is False


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
    for forbidden in ("import subprocess", "os.system", "iptables-save", "iptables-restore"):
        assert forbidden not in src
