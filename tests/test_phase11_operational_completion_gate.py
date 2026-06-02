from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_operational_completion_gap_inventory_service import (
    build_phase11_operational_completion_gap_inventory_report,
)

RUNNER = CliRunner()


def test_docs_define_phase11_operational_completion_gate() -> None:
    paths = (
        "README.md",
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/AI_PHASE_11_OPERATIONAL_COMPLETION_TASK.md",
        "docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md",
    )
    for path in paths:
        assert "Phase 11 operational completion" in Path(path).read_text(encoding="utf-8")


def test_phase_status_blocks_phase12_and_later_interfaces() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    current = text.split("## Current State", 1)[1].split("```text", 1)[1].split("```", 1)[0]
    for expected in (
        "current_working_phase: Phase 11 operational completion",
        "phase12_start_allowed: no",
        "worker_enforcement_allowed: no",
        "ui_allowed: no",
        "telegram_allowed: no",
    ):
        assert expected in current


def test_runtime_forward_pr_rule_is_recorded() -> None:
    for path in ("AGENTS.md", "docs/AI_CODING_RULES.md"):
        text = Path(path).read_text(encoding="utf-8")
        assert "Runtime-forward PR rule" in text
        assert "No two consecutive PRs in the same active phase/subphase may be report-only" in text


def test_gap_inventory_service_is_fail_closed_and_read_only() -> None:
    report = build_phase11_operational_completion_gap_inventory_report()
    assert report["final_decision"] == "PHASE11_OPERATIONAL_COMPLETION_REQUIRED"
    assert report["phase12_start_allowed"] is False
    for key in (
        "mutation_performed",
        "db_mutation_performed",
        "firewall_apply_performed",
        "conntrack_flush_performed",
        "docker_restart_performed",
        "systemd_restart_performed",
    ):
        assert report[key] is False


def test_gap_inventory_cli_returns_fail_closed_json() -> None:
    result = RUNNER.invoke(app, ["production", "phase11-operational-completion-gap-inventory", "--output", "json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["repository_version"] == "0.1.238"
    assert report["final_decision"] == "PHASE11_OPERATIONAL_COMPLETION_REQUIRED"
    assert report["phase12_start_allowed"] is False
    assert report["mutation_performed"] is False
