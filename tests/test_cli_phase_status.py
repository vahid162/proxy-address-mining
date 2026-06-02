from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app


def _current_state_block() -> str:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    marker = "## Current State"
    idx = text.find(marker)
    assert idx != -1
    section = text[idx + len(marker):]
    start = section.find("```text")
    assert start != -1
    start += len("```text")
    end = section.find("```", start)
    assert end != -1
    return section[start:end].strip()


def test_phase_status_matches_current_state_block_exactly() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["phase-status"])

    assert result.exit_code == 0
    assert result.stdout.strip() == _current_state_block()


def test_phase_status_gate_alignment_and_safety_lines() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["phase-status"])

    assert result.exit_code == 0
    assert "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5" in result.stdout
    assert "current_working_phase: Phase 12 — Worker Policy Enforcement" in result.stdout

    assert "current_accepted_phase: Phase 4 Runtime Activation" not in result.stdout
    assert "current_working_phase: Phase 5 — Customer CRUD in DB Only" not in result.stdout

    assert "production_traffic: controlled_cli_limited" in result.stdout
    assert "firewall_apply_allowed: controlled" in result.stdout
    assert "abuse_automation_allowed: controlled" in result.stdout
    assert "proxy_data_plane_allowed: limited_runtime_local_only" in result.stdout
    assert "ui_allowed: no" in result.stdout
    assert "telegram_allowed: no" in result.stdout
