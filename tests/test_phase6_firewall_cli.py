from __future__ import annotations

from typer.testing import CliRunner

from mpf.domain.firewall import FirewallPlanMessage, FirewallPlanResult
from mpf.interfaces.cli import app
from mpf.services import firewall_planner_service
from tests.test_smoke import example_config_path

RUNNER = CliRunner()


def _db_plan() -> FirewallPlanResult:
    p = FirewallPlanResult(planner_customer_source="db_readonly", db_customer_input_loaded=True)
    p.finalize()
    return p


def _config_plan() -> FirewallPlanResult:
    p = FirewallPlanResult(planner_customer_source="config_only", db_customer_input_loaded=False)
    p.warnings.append(FirewallPlanMessage(code="planner_customer_source", message="explicit config-only source requested", severity="warning"))
    p.finalize()
    return p


def test_firewall_plan_and_diff_default_to_db_readonly(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    for cmd in (["firewall", "plan"], ["firewall", "diff"]):
        res = RUNNER.invoke(app, [*cmd, "--config", str(example_config_path())])
        assert res.exit_code == 0
        assert "planner_customer_source: db_readonly" in res.output
        assert "db_customer_input_loaded: true" in res.output
        assert "firewall_change: planned_only" in res.output


def test_firewall_plan_json_reports_db_source(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "plan", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"planner_customer_source": "db_readonly"' in res.output
    assert '"db_customer_input_loaded": true' in res.output


def test_firewall_plan_config_only_is_explicit(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "plan", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "planner_customer_source: config_only" in res.output
    assert "db_customer_input_loaded: false" in res.output
    assert "WARNING" in res.output


def test_firewall_plan_db_failure_exits_nonzero(monkeypatch) -> None:
    def raise_fail(cfg):
        raise RuntimeError("failed to load lanes: db down")

    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", raise_fail)
    res = RUNNER.invoke(app, ["firewall", "plan", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output


def test_firewall_diff_json_with_offline_live_snapshot_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db_with_live_snapshot", lambda cfg, snapshot: _db_plan())
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "diff", "--config", str(example_config_path()), "--output", "json", "--live-snapshot-file", str(snapshot)])
    assert res.exit_code == 0
    assert '"planner_customer_source": "db_readonly"' in res.output
