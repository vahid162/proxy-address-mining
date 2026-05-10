from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.repositories.job_repo import JobRunRecord
from mpf.repositories.lane_repo import LaneRecord

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")


def test_lanes_list_uses_service_layer(monkeypatch) -> None:
    from mpf.interfaces import cli

    class FakeLaneList:
        ok = True
        message = "OK"
        lanes = [LaneRecord("btc", True, 60010, "MPFBTC", "stratum", "db")]

    monkeypatch.setattr(cli.lane_service, "list_lane_status", lambda config: FakeLaneList())
    result = RUNNER.invoke(app, ["lanes", "list", "--config", str(CONFIG_PATH)])
    assert result.exit_code == 0
    assert "btc" in result.output
    assert "backend_port=60010" in result.output


def test_customer_list_uses_read_service(monkeypatch) -> None:
    from mpf.interfaces import cli

    class FakeCustomerList:
        ok = True
        message = "OK"
        customers = [CustomerRecord(1, "btc", "alice", 23138, "active", None)]

    monkeypatch.setattr(cli.customer_read_service, "list_customer_status", lambda config, limit=100: FakeCustomerList())
    result = RUNNER.invoke(app, ["customer", "list", "--config", str(CONFIG_PATH)])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "port=23138" in result.output


def test_jobs_status_uses_job_service(monkeypatch) -> None:
    from mpf.interfaces import cli

    class FakeJobList:
        ok = True
        message = "OK"
        jobs = [JobRunRecord(1, "phase3_check", "succeeded", "2026-05-07", None, 12)]

    monkeypatch.setattr(cli.job_service, "list_job_status", lambda config, limit=20: FakeJobList())
    result = RUNNER.invoke(app, ["jobs", "status", "--config", str(CONFIG_PATH)])
    assert result.exit_code == 0
    assert "phase3_check" in result.output
    assert "status=succeeded" in result.output


def test_db_status_uses_db_service(monkeypatch) -> None:
    from mpf.interfaces import cli
    from mpf.services.db_service import DatabaseStatus

    monkeypatch.setattr(
        cli.db_service,
        "status",
        lambda config: DatabaseStatus(
            ok=True,
            message="OK",
            alembic_version="0001_phase2_initial_schema",
            public_table_count=64,
            lanes=0,
            customers=0,
            job_runs=0,
            firewall_applies=0,
            abuse_states=0,
        ),
    )
    result = RUNNER.invoke(app, ["db", "status", "--config", str(CONFIG_PATH)])
    assert result.exit_code == 0
    assert "database: OK" in result.output
    assert "public_table_count: 64" in result.output


def test_lane_repo_falls_back_to_config_lanes_when_db_is_empty(monkeypatch) -> None:
    from mpf.repositories import lane_repo

    class QueryResult:
        ok = True
        rows = []
        message = "OK"

    monkeypatch.setattr(lane_repo, "query_database", lambda config, sql: QueryResult())
    ok, records, message = lane_repo.list_lanes(load_config(CONFIG_PATH))
    assert ok is True
    assert "config lanes" in message
    assert {record.name for record in records} >= {"btc", "zec", "ltc"}


def test_query_database_rejects_mutating_sql() -> None:
    from mpf.config import load_config
    from mpf.db import query_database

    result = query_database(load_config(CONFIG_PATH), "delete from customers")
    assert result.ok is False
    assert "read-only" in result.message


def test_lanes_sync_config_uses_service_layer(monkeypatch) -> None:
    from mpf.interfaces import cli

    class FakeResult:
        ok = True
        firewall_change = "no"
        nat_change = "no"
        runtime_change = "no"
        would_create_lanes = 1
        would_update_lanes = 0
        stale_db_lanes = 0
        created_lanes = ["btc"]
        updated_lanes = []
        stale_lanes = []

    monkeypatch.setattr(cli.lane_sync_service, "sync_lane_config_db_only", lambda config, dry_run=True, yes=False, command_hint="": FakeResult())
    result = RUNNER.invoke(app, ["lanes", "sync-config", "--config", str(CONFIG_PATH)])
    assert result.exit_code == 0
    assert "would_create_lanes: 1" in result.output
