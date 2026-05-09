from __future__ import annotations

from typer.testing import CliRunner

from mpf.interfaces.cli import app


def test_phase_status_matches_current_phase_guard() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["phase-status"])

    assert result.exit_code == 0
    assert "current_accepted_phase: Phase 4 Runtime Activation" in result.stdout
    assert "current_working_phase: Phase 5" in result.stdout
    assert "server_state: farm5 limited Phase 4 proxy runtime is running and accepted" in result.stdout
    assert "firewall_apply_allowed: no" in result.stdout
    assert "abuse_automation_allowed: no" in result.stdout
    assert "customer_onboarding_allowed: db_only_after_phase5_gate" in result.stdout
    assert "proxy_data_plane_allowed: limited_runtime_local_only" in result.stdout
    assert "ui_allowed: no" in result.stdout
    assert "telegram_allowed: no" in result.stdout
    assert "compatibility_previous_current_accepted_phase: Phase 4.2" in result.stdout
    assert "compatibility_previous_current_working_phase: Phase 4 Runtime Activation Execution Review" in result.stdout
    assert "Phase 0" not in result.stdout
    assert "Repository Bootstrap Skeleton" not in result.stdout
