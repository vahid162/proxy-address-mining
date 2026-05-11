from __future__ import annotations

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from tests.test_smoke import example_config_path

RUNNER = CliRunner()


def test_firewall_plan_and_diff_are_dry_run() -> None:
    for cmd in (["firewall", "plan"], ["firewall", "diff"]):
        res = RUNNER.invoke(app, [*cmd, "--config", str(example_config_path())])
        assert res.exit_code == 0
        assert "dry-run" in res.output
        assert "firewall_change: planned_only" in res.output
        assert "nat_change: planned_only" in res.output
        assert "runtime_change: no" in res.output
        assert "planner_customer_source: config_only" in res.output
        assert "db_customer_input_loaded: false" in res.output


def test_firewall_plan_json_has_customer_source_warning_flags() -> None:
    res = RUNNER.invoke(app, ["firewall", "plan", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"planner_customer_source": "config_only"' in res.output
    assert '"db_customer_input_loaded": false' in res.output
    assert '"code": "planner_customer_source"' in res.output
