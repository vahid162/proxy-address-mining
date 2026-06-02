from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from mpf.config import MPFConfig
from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.repositories.lane_repo import LaneRecord
from mpf.services import customer_lifecycle_operational_surface_service as surface_service

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")


def cfg() -> MPFConfig:
    return MPFConfig.model_validate({"server": {"name": "test"}, "database": {"url": "postgresql://test/mpf"}, "lanes": {"btc": {"enabled": True, "backend_port": 60010, "chain_prefix": "BTC"}}})


def _mock_safe_reads(monkeypatch) -> list[str]:
    calls: list[str] = []

    def db_status(_config):
        calls.append("db_status")
        return SimpleNamespace(ok=True, message="OK")

    def lanes(_config):
        calls.append("lane_list")
        return SimpleNamespace(ok=True, message="OK", lanes=[LaneRecord("btc", True, 60010, "BTC", "stratum", "db")])

    def customers(_config, **kwargs):
        calls.append("active_customer_list")
        assert kwargs == {"status": "active", "include_deleted": False, "limit": 1000}
        return SimpleNamespace(ok=True, message="OK", customers=[CustomerRecord(1, "btc-1", "btc", "alice", 20001, "active", "immediate", None, None)])

    monkeypatch.setattr(surface_service.db_service, "status", db_status)
    monkeypatch.setattr(surface_service.lane_service, "list_lane_status", lanes)
    monkeypatch.setattr(surface_service.customer_read_service, "list_customer_status", customers)
    return calls


def test_customer_lifecycle_operational_surface_returns_ready_without_mutation(monkeypatch) -> None:
    calls = _mock_safe_reads(monkeypatch)
    report = surface_service.build_customer_lifecycle_operational_surface_report(cfg())
    assert report["component"] == "controlled_customer_lifecycle_operational_surface"
    assert report["status"] == "READY"
    assert report["blockers"] == []
    assert report["lanes_visible_from_db"] == ["btc"]
    assert report["active_customers_visible_from_db"] == ["btc-1"]
    assert report["final_decision"] == "CUSTOMER_LIFECYCLE_SURFACE_READY"
    assert calls == ["db_status", "lane_list", "active_customer_list"]
    for key in ("mutation_performed", "db_mutation_performed", "firewall_apply_performed", "docker_action_performed", "systemd_action_performed", "conntrack_action_performed"):
        assert report[key] is False
    assert report["firewall_change"] == report["nat_change"] == report["runtime_change"] == "no"


def test_customer_lifecycle_operational_surface_blocks_on_db_read_failure(monkeypatch) -> None:
    monkeypatch.setattr(surface_service.db_service, "status", lambda _config: SimpleNamespace(ok=False, message="down"))
    monkeypatch.setattr(surface_service.lane_service, "list_lane_status", lambda _config: (_ for _ in ()).throw(AssertionError("must not continue after DB failure")))
    monkeypatch.setattr(surface_service.customer_read_service, "list_customer_status", lambda _config, **_kwargs: (_ for _ in ()).throw(AssertionError("must not continue after DB failure")))
    report = surface_service.build_customer_lifecycle_operational_surface_report(cfg())
    assert report["status"] == "BLOCKED"
    assert report["blockers"] == ["database_read_failed"]
    assert report["final_decision"] == "CUSTOMER_LIFECYCLE_SURFACE_BLOCKED"
    assert report["mutation_performed"] is False


def test_customer_lifecycle_operational_surface_checks_required_gated_commands(monkeypatch) -> None:
    _mock_safe_reads(monkeypatch)
    report = surface_service.build_customer_lifecycle_operational_surface_report(cfg())
    assert report["customer_read_commands_available"] == [
        "customer list", "customer show", "customer next-port", "customer expiring", "customer expired",
        "customer delete-eligible", "customer policies", "customer events", "customer audit",
    ]
    assert report["customer_mutation_commands_available_and_gated"] == [
        "customer add", "customer update", "customer renew", "customer disable", "customer delete", "customer set-ips",
    ]
    assert report["default_dry_run_no_yes_safe"] is True
    assert report["yes_required_for_db_mutation"] is True
    assert report["root_local_peer_postgresql_write_guard_active_for_actual_writes"] is True
    assert report["direct_db_writes_from_cli_handlers"] is False
    assert report["customer_lifecycle_service_layer_boundary_preserved"] is True
    assert report["customer_lifecycle_firewall_runtime_action"] is False


def test_customer_lifecycle_doctor_cli_is_thin_and_calls_service(monkeypatch) -> None:
    from mpf.interfaces import cli

    expected = {"component": "controlled_customer_lifecycle_operational_surface", "status": "READY", "mutation_performed": False}
    captured = {}
    monkeypatch.setattr(cli, "_load", lambda _path: cfg())
    monkeypatch.setattr(cli.customer_lifecycle_operational_surface_service, "build_customer_lifecycle_operational_surface_report", lambda config: captured.setdefault("report", expected))
    result = RUNNER.invoke(app, ["customer", "lifecycle-doctor", "--config", str(CONFIG_PATH), "--output", "json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == expected
    assert captured["report"] == expected
    source = inspect.getsource(cli.customer_lifecycle_doctor)
    assert "build_customer_lifecycle_operational_surface_report" in source
    for forbidden in ("query_database", "execute(", "iptables", "conntrack", "docker", "systemctl"):
        assert forbidden not in source.lower()


def test_customer_lifecycle_doctor_cli_fails_closed_without_traceback_when_config_load_fails(monkeypatch) -> None:
    from mpf.interfaces import cli

    monkeypatch.setattr(cli, "_load", lambda _path: (_ for _ in ()).throw(FileNotFoundError("missing config")))
    result = RUNNER.invoke(app, ["customer", "lifecycle-doctor", "--output", "json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["status"] == "BLOCKED"
    assert report["blockers"] == ["configuration_load_failed"]
    assert report["mutation_performed"] is False
    assert "Traceback" not in result.output
