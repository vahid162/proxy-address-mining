from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mpf import __version__
from mpf.config import load_config, validate_config
from mpf.interfaces.cli import app

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_example_config_validates() -> None:
    ok, message = validate_config(example_config_path())
    assert ok, message


def test_example_config_keeps_plan_only_and_abuse_threshold() -> None:
    config = load_config(example_config_path())
    assert config.firewall.apply_mode == "plan_only"
    assert config.lanes["btc"].backend_port == 60010
    assert config.abuse.threshold_sec == 3600


def test_cli_help_works() -> None:
    result = RUNNER.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Phase-gated read-only foundation commands" in result.output


def test_cli_version_works_without_command() -> None:
    result = RUNNER.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert "Missing command" not in result.output


def test_cli_phase_status_matches_current_phase_guard() -> None:
    result = RUNNER.invoke(app, ["phase-status"])
    assert result.exit_code == 0
    assert "current_accepted_phase: Phase 4 Runtime Activation" in result.output
    assert "current_working_phase: Phase 5" in result.output
    assert "server_state: farm5 limited Phase 4 proxy runtime is running and accepted" in result.output
    assert "firewall_apply_allowed: no" in result.output
    assert "abuse_automation_allowed: no" in result.output
    assert "proxy_data_plane_allowed: limited_runtime_local_only" in result.output
    assert "customer_onboarding_allowed: db_only_after_phase5_gate" in result.output
    assert "compatibility_previous_current_accepted_phase: Phase 4.2" in result.output
    assert "compatibility_previous_current_working_phase: Phase 4 Runtime Activation Execution Review" in result.output


def test_cli_config_validate_example() -> None:
    result = RUNNER.invoke(app, ["config", "validate", "--config", str(example_config_path())])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_cli_doctor_reports_no_traffic_changes(monkeypatch) -> None:
    from mpf.interfaces import cli

    class FakeDoctorStatus:
        ok = True
        config_ok = True
        db_ok = True
        message = "OK"
        config_path = example_config_path()
        apply_mode = "plan_only"
        traffic_changes = "none"
        firewall_mutation = "disabled"
        abuse_automation = "disabled"

    monkeypatch.setattr(cli.doctor_service, "run", lambda path: FakeDoctorStatus())
    result = RUNNER.invoke(app, ["doctor", "--config", str(example_config_path())])
    assert result.exit_code == 0
    assert "traffic_changes: none" in result.output
    assert "firewall_mutation: disabled" in result.output
    assert "abuse_automation: disabled" in result.output
