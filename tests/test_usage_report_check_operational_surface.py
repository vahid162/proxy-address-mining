from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from mpf.config import MPFConfig
from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.repositories.job_repo import JobRunRecord
from mpf.repositories.lane_repo import LaneRecord
from mpf.services import usage_report_check_operational_surface_service as surface_service

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")


def cfg() -> MPFConfig:
    return MPFConfig.model_validate({"server": {"name": "test"}, "database": {"url": "postgresql://test/mpf"}, "lanes": {"btc": {"enabled": True, "backend_port": 60010, "chain_prefix": "BTC"}}})


def _mock_safe_reads(monkeypatch) -> list[str]:
    calls: list[str] = []

    def db_status(_config):
        calls.append("db_status")
        return SimpleNamespace(ok=True, message="OK", alembic_version="0002", public_table_count=20, lanes=1, customers=1, job_runs=1, firewall_applies=0, abuse_states=1)

    def lanes(_config):
        calls.append("lane_list")
        return SimpleNamespace(ok=True, message="OK", lanes=[LaneRecord("btc", True, 60010, "BTC", "stratum", "db")])

    def customers(_config, **kwargs):
        calls.append("active_customer_list")
        assert kwargs == {"status": "active", "include_deleted": False, "limit": 1000}
        return SimpleNamespace(ok=True, message="OK", customers=[CustomerRecord(1, "btc-1", "btc", "alice", 20001, "active", "immediate", None, None)])

    def jobs(_config, *, limit):
        calls.append("job_runs")
        assert limit == 20
        return SimpleNamespace(ok=True, message="OK", jobs=[JobRunRecord(1, "abuse_operational", "ok", "2026-06-02T00:00:00Z", None, None)])

    def abuse(_repo):
        calls.append("abuse_status")
        return {"status": "OK", "blockers": [], "states": [{"customer_key": "btc-1", "status": "normal"}]}

    monkeypatch.setattr(surface_service.db_service, "status", db_status)
    monkeypatch.setattr(surface_service.lane_service, "list_lane_status", lanes)
    monkeypatch.setattr(surface_service.customer_read_service, "list_customer_status", customers)
    monkeypatch.setattr(surface_service.job_service, "list_job_status", jobs)
    monkeypatch.setattr(surface_service.abuse_operational_service, "status_report", abuse)
    return calls


def test_usage_report_check_operational_surface_returns_ready_without_mutation(monkeypatch) -> None:
    calls = _mock_safe_reads(monkeypatch)
    report = surface_service.build_usage_report_check_operational_surface_report(cfg())
    assert report["component"] == "controlled_usage_report_check_operational_surface"
    assert report["status"] == "READY"
    assert report["blockers"] == []
    assert report["db_schema_runtime_status"] == "available"
    assert report["lanes_visible_from_db"] == ["btc"]
    assert report["active_customers_visible_from_db"] == ["btc-1"]
    assert report["active_customer_key_lane_port_visibility"] == [{"customer_key": "btc-1", "lane": "btc", "port": 20001}]
    assert report["job_runs_visibility"] == "available"
    assert report["abuse_state_visibility"] == "available"
    assert report["customer_lifecycle_visibility"] == "available"
    assert report["final_decision"] == "USAGE_REPORT_CHECK_SURFACE_READY"
    assert report["next_required_step"] == "implement_controlled_firewall_apply_rollback_workflow"
    assert calls == ["db_status", "lane_list", "active_customer_list", "job_runs", "abuse_status"]
    for key in ("mutation_performed", "db_mutation_performed", "firewall_apply_performed", "docker_action_performed", "systemd_action_performed", "conntrack_action_performed", "worker_enforcement_enabled", "ui_enabled", "telegram_enabled", "phase12_start_allowed"):
        assert report[key] is False
    assert report["firewall_change"] == report["nat_change"] == report["runtime_change"] == "no"


def test_usage_report_check_surface_reports_missing_runtime_evidence_honestly(monkeypatch) -> None:
    _mock_safe_reads(monkeypatch)
    report = surface_service.build_usage_report_check_operational_surface_report(cfg())
    assert report["status"] == "READY"
    assert report["usage_evidence_source"] == "unavailable"
    assert report["reject_counter_visibility"] == "unavailable"
    assert report["session_evidence_visibility"] == "unavailable"
    assert report["worker_evidence_visibility"] == "not_applicable"
    assert report["runtime_evidence"] == {
        "usage_counters": {"status": "unavailable", "source": None, "detail": "no read-only runtime counter source configured"},
        "reject_counters": {"status": "unavailable", "source": None, "detail": "no read-only reject counter source configured"},
        "sessions": {"status": "unavailable", "source": None, "detail": "no read-only session source configured"},
        "workers": {"status": "not_applicable", "source": None, "detail": "worker enforcement remains disabled before Phase 12"},
    }
    assert "usage_runtime_evidence_unavailable" in report["warnings"]
    assert "worker_evidence_not_applicable_worker_enforcement_disabled" in report["warnings"]
    assert {item["input"]: item["visibility"] for item in report["diagnostics_inputs_checked"]}["live_conntrack"] == "not_available"


def test_usage_report_check_surface_blocks_on_db_read_failure(monkeypatch) -> None:
    monkeypatch.setattr(surface_service.db_service, "status", lambda _config: SimpleNamespace(ok=False, message="down"))
    report = surface_service.build_usage_report_check_operational_surface_report(cfg())
    assert report["status"] == "BLOCKED"
    assert report["blockers"] == ["database_read_failed"]
    assert report["usage_report_check_surface_ready"] is False
    assert report["final_decision"] == "USAGE_REPORT_CHECK_SURFACE_BLOCKED"
    assert report["mutation_performed"] is False


def test_usage_report_check_cli_is_thin_and_calls_service(monkeypatch) -> None:
    from mpf.interfaces import cli

    expected = {"component": "controlled_usage_report_check_operational_surface", "status": "READY", "mutation_performed": False}
    monkeypatch.setattr(cli, "_load", lambda _path: cfg())
    monkeypatch.setattr(cli.usage_report_check_operational_surface_service, "build_usage_report_check_operational_surface_report", lambda config: expected)
    result = RUNNER.invoke(app, ["production", "usage-report-check-operational-surface", "--config", str(CONFIG_PATH), "--output", "json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == expected
    source = inspect.getsource(cli.production_usage_report_check_operational_surface)
    assert "build_usage_report_check_operational_surface_report" in source
    for forbidden in ("query_database", "execute(", "iptables", "conntrack", "docker", "systemctl", "subprocess"):
        assert forbidden not in source.lower()


def test_usage_report_check_cli_fails_closed_without_traceback_when_config_load_fails(monkeypatch) -> None:
    from mpf.interfaces import cli

    monkeypatch.setattr(cli, "_load", lambda _path: (_ for _ in ()).throw(FileNotFoundError("missing config")))
    result = RUNNER.invoke(app, ["production", "usage-report-check-operational-surface", "--output", "json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["status"] == "BLOCKED"
    assert report["blockers"] == ["configuration_load_failed"]
    assert report["mutation_performed"] is False
    assert report["db_mutation_performed"] is False
    assert report["firewall_apply_performed"] is False
    assert "Traceback" not in result.output
