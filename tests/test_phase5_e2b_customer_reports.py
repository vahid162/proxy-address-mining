from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.repositories import customer_repo
from mpf.services import customer_read_service

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")


class Row:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_customer_next_port_cli_prints_safety_flags(monkeypatch):
    from mpf.interfaces import cli

    class R:
        ok = True
        message = "OK"
        suggestion = Row(lane="btc", lane_enabled=True, suggested_port=20002, checked_range="20000-59999", occupied_count=3, skipped_reserved_count=4)

    monkeypatch.setattr(cli.customer_read_service, "suggest_next_customer_port", lambda *a, **k: R())
    res = RUNNER.invoke(app, ["customer", "next-port", "--config", str(CONFIG_PATH), "--lane", "btc"])
    assert res.exit_code == 0
    assert "suggested_port: 20002" in res.output
    assert "runtime_change: no" in res.output


def test_customer_expiring_cli_empty_ok(monkeypatch):
    from mpf.interfaces import cli

    class R:
        ok = True
        message = "OK"
        rows = []

    monkeypatch.setattr(cli.customer_read_service, "report_expiring_customers", lambda *a, **k: R())
    res = RUNNER.invoke(app, ["customer", "expiring", "--config", str(CONFIG_PATH)])
    assert res.exit_code == 0
    assert "no expiring customers in window" in res.output


def test_customer_expired_include_deleted_passed(monkeypatch):
    from mpf.interfaces import cli

    captured = {}

    class R:
        ok = True
        message = "OK"
        rows = []

    def fake(*a, **k):
        captured.update(k)
        return R()

    monkeypatch.setattr(cli.customer_read_service, "report_expired_customers", fake)
    res = RUNNER.invoke(app, ["customer", "expired", "--config", str(CONFIG_PATH), "--include-deleted"])
    assert res.exit_code == 0
    assert captured["include_deleted"] is True


def test_customer_delete_eligible_cli_safety_flags(monkeypatch):
    from mpf.interfaces import cli

    class R:
        ok = True
        message = "OK"
        rows = [Row(customer_key="c1", lane="btc", name="a", port=20001, status="active", expires_at=None, delete_eligible_at="2026")]

    monkeypatch.setattr(cli.customer_read_service, "report_delete_eligible_customers", lambda *a, **k: R())
    res = RUNNER.invoke(app, ["customer", "delete-eligible", "--config", str(CONFIG_PATH)])
    assert res.exit_code == 0
    assert "firewall_change: no" in res.output


def test_service_validation_and_clamp():
    bad = customer_read_service.report_expiring_customers(type("C", (), {})(), within_days=-1)
    assert bad.ok is False


def test_repo_queries_are_select_with(monkeypatch):
    calls = []

    def fake(config, sql, params=()):
        calls.append(sql.strip().lower())
        if "from lanes where name" in sql:
            return type("R", (), {"ok": True, "rows": [{"name": "btc", "enabled": True, "backend_port": 60010}], "message": "OK"})()
        return type("R", (), {"ok": True, "rows": [], "message": "OK"})()

    monkeypatch.setattr(customer_repo, "query_database_params", fake)
    customer_repo.suggest_next_port(type("C", (), {})(), lane="btc", start=20000, end=20001)
    customer_repo.list_expiring_customers(type("C", (), {})(), within_days=7, include_paused=False, limit=10)
    customer_repo.list_expired_customers(type("C", (), {})(), include_deleted=False, limit=10)
    customer_repo.list_delete_eligible_customers(type("C", (), {})(), limit=10)
    assert all(s.startswith(("select", "with")) for s in calls)
