from __future__ import annotations

from typer.testing import CliRunner

from mpf.interfaces.cli import app


def test_phase_status_matches_current_phase_guard() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["phase-status"])

    assert result.exit_code == 0
    assert "current_accepted_phase: Phase 2" in result.stdout
    assert "current_working_phase: Phase 3" in result.stdout
    assert "server_state: farm5 phase 2 schema migration completed and verified" in result.stdout
    assert "firewall_apply_allowed: no" in result.stdout
    assert "abuse_automation_allowed: no" in result.stdout
    assert "customer_onboarding_allowed: no" in result.stdout
    assert "Phase 0" not in result.stdout
    assert "Repository Bootstrap Skeleton" not in result.stdout
