from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config, validate_config
from mpf.interfaces.cli import app

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_example_config_validates() -> None:
    ok, message = validate_config(example_config_path())
    assert ok, message


def test_example_config_keeps_phase1_plan_only() -> None:
    config = load_config(example_config_path())
    assert config.firewall.apply_mode == "plan_only"
    assert config.lanes["btc"].backend_port == 60010
    assert config.abuse.threshold_sec == 3600


def test_cli_help_works() -> None:
    result = RUNNER.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Safe smoke commands only" in result.output


def test_cli_phase_status_is_safe() -> None:
    result = RUNNER.invoke(app, ["phase-status"])
    assert result.exit_code == 0
    assert "firewall_apply_allowed: no" in result.output
    assert "abuse_automation_allowed: no" in result.output


def test_cli_config_validate_example() -> None:
    result = RUNNER.invoke(app, ["config", "validate", "--config", str(example_config_path())])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_cli_doctor_reports_no_traffic_changes() -> None:
    result = RUNNER.invoke(app, ["doctor", "--config", str(example_config_path())])
    assert result.exit_code == 0
    assert "traffic_changes: none" in result.output
    assert "firewall_mutation: disabled" in result.output
