from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase9_final_verdict_diagnostics_service import build_phase9_final_verdict_diagnostics_report


def test_phase9_final_verdict_service_report_only_and_safe_flags() -> None:
    cfg = load_config(Path("configs/mpf.example.yaml"))
    r = build_phase9_final_verdict_diagnostics_report(cfg)
    assert r["component"] == "phase9_final_verdict_diagnostics"
    assert r["execution_allowed"] is False
    assert r["report_only"] is True
    assert r["all_dangerous_authorization_flags_false"] is True
    for key in [
        "firewall_apply_authorized",
        "iptables_restore_authorized",
        "customer_nat_authorized",
        "customer_firewall_rules_authorized",
        "abuse_runner_authorized",
        "production_db_execution_authorized",
        "hard_block_authorized",
        "soft_block_authorized",
        "pause_automation_authorized",
        "production_traffic_authorized",
        "ui_authorized",
        "telegram_authorized",
    ]:
        assert r[key] is False


def test_phase9_final_verdict_cli_json() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["phase9", "final-verdict", "--config", "configs/mpf.example.yaml", "--output", "json"])
    assert result.exit_code == 0
    assert '"component": "phase9_final_verdict_diagnostics"' in result.output
    assert '"execution_allowed": false' in result.output
