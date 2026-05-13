from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import firewall_live_snapshot_scaffold_service

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_service_report_is_blocked_and_non_authorized() -> None:
    cfg = load_config(example_config_path())
    report = firewall_live_snapshot_scaffold_service.build_live_snapshot_scaffold_report(cfg)
    assert report["final_decision"] == "BLOCKED"
    assert report["authorization_status"] == "NOT_AUTHORIZED"
    assert report["apply_decision"] == "BLOCKED"


def test_service_safety_flags_are_all_false() -> None:
    cfg = load_config(example_config_path())
    report = firewall_live_snapshot_scaffold_service.build_live_snapshot_scaffold_report(cfg)
    for key in (
        "live_firewall_read_executed",
        "iptables_save_executed",
        "subprocess_executed",
        "firewall_mutation",
        "db_mutation",
        "restore_point_written",
        "lock_acquired",
        "customer_nat_changed",
        "customer_firewall_rules_changed",
        "production_traffic_changed",
        "empty_snapshot_fallback_allowed",
        "guessed_state_allowed",
    ):
        assert report[key] is False


def test_service_blocks_on_current_state_mismatch(tmp_path: Path) -> None:
    cfg = load_config(example_config_path())
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "PHASE_STATUS.md").write_text("## Current State\n\n```text\nproduction_traffic: yes\n```\n", encoding="utf-8")
    report = firewall_live_snapshot_scaffold_service.build_live_snapshot_scaffold_report(cfg, repo_root=tmp_path)
    assert report["final_decision"] == "BLOCKED"
    assert "Current State block does not match required phase gate values" in report["blockers"]


def test_service_blocks_if_apply_mode_not_plan_only() -> None:
    cfg = load_config(example_config_path())
    cfg.firewall.apply_mode = "apply"
    report = firewall_live_snapshot_scaffold_service.build_live_snapshot_scaffold_report(cfg)
    assert "firewall.apply_mode is not plan_only" in report["blockers"]


def test_cli_human_output_and_no_root_requirement() -> None:
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-scaffold", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "final_decision: BLOCKED" in res.output
    assert "authorization_status: NOT_AUTHORIZED" in res.output


def test_cli_json_output_stable_fields() -> None:
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-scaffold", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"component": "firewall_live_snapshot_scaffold"' in res.output
    assert '"final_decision": "BLOCKED"' in res.output
    assert '"live_firewall_read_executed": false' in res.output
    assert '"iptables_save_executed": false' in res.output
