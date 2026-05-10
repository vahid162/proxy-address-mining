from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.repositories import customer_repo
from mpf.services import customer_read_service

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")


def test_customer_policies_cli_by_key(monkeypatch):
    from mpf.interfaces import cli

    class R:
        ok = True
        message = "OK"
        rows = [{"customer_id": 1, "customer_key": "cust_a", "lane": "btc", "port": 20001, "policy_id": 10, "version": 2, "is_current": True, "miners": 1, "farms": 1, "maxconn": 1, "rate_per_min": 1, "burst": 1, "ips_mode": "any", "abuse_exempt": False, "abuse_exempt_reason": None, "abuse_exempt_until": None, "abuse_exempt_by": None, "created_at": "2026", "created_by": "op", "reason": "r"}]

    monkeypatch.setattr(cli.customer_read_service, "customer_policy_history", lambda *a, **k: R())
    res = RUNNER.invoke(app, ["customer", "policies", "--config", str(CONFIG_PATH), "--customer-key", "cust_a"])
    assert res.exit_code == 0
    assert "policy_id: 10" in res.output
    assert "firewall_change: no" in res.output


def test_customer_policies_reject_target_errors():
    r1 = RUNNER.invoke(app, ["customer", "policies", "--config", str(CONFIG_PATH)])
    r2 = RUNNER.invoke(app, ["customer", "policies", "--config", str(CONFIG_PATH), "--id", "1", "--port", "20001"])
    assert r1.exit_code == 1
    assert r2.exit_code == 1


def test_customer_events_and_audit_cli(monkeypatch):
    from mpf.interfaces import cli

    class RE:
        ok = True
        message = "OK"
        rows = [{"id": 3, "event_type": "x", "severity": "info", "subject_type": "customer", "subject_id": 1, "message": "m", "data_json": "{}", "created_at": "2026", "created_by": "op", "correlation_id": "c"}]

    class RA:
        ok = True
        message = "OK"
        rows = [{"id": 5, "actor_type": "operator", "actor_id": "op", "action": "u", "resource_type": "customer", "resource_id": 1, "before_json": "{}", "after_json": "{}", "reason": "r", "created_at": "2026", "correlation_id": "c"}]

    monkeypatch.setattr(cli.customer_read_service, "customer_events_history", lambda *a, **k: RE())
    monkeypatch.setattr(cli.customer_read_service, "customer_audit_history", lambda *a, **k: RA())
    e = RUNNER.invoke(app, ["customer", "events", "--config", str(CONFIG_PATH), "--id", "1"])
    a = RUNNER.invoke(app, ["customer", "audit", "--config", str(CONFIG_PATH), "--port", "20001"])
    assert e.exit_code == 0 and "event_type: x" in e.output
    assert a.exit_code == 0 and "action: u" in a.output


def test_events_latest_cli_and_invalid_severity(monkeypatch):
    from mpf.interfaces import cli

    class R:
        ok = True
        message = "OK"
        rows = [{"id": 1, "event_type": "x", "severity": "info", "subject_type": "customer", "subject_id": 1, "message": "m", "created_at": "2026", "created_by": "op", "correlation_id": "c"}]

    monkeypatch.setattr(cli.customer_read_service, "latest_events", lambda *a, **k: R())
    ok = RUNNER.invoke(app, ["events", "latest", "--config", str(CONFIG_PATH)])
    assert ok.exit_code == 0 and "runtime_change: no" in ok.output

    bad = customer_repo.list_latest_events(type("C", (), {})(), limit=20, severity="bad")
    assert bad[0] is False
    assert "invalid severity" in bad[2]


def test_history_empty_and_not_found(monkeypatch):
    from mpf.interfaces import cli

    class E:
        ok = True
        message = "OK"
        rows = []

    class NF:
        ok = False
        message = "customer not found"
        rows = []

    monkeypatch.setattr(cli.customer_read_service, "customer_events_history", lambda *a, **k: E())
    monkeypatch.setattr(cli.customer_read_service, "customer_policy_history", lambda *a, **k: NF())
    e = RUNNER.invoke(app, ["customer", "events", "--config", str(CONFIG_PATH), "--id", "1"])
    nf = RUNNER.invoke(app, ["customer", "policies", "--config", str(CONFIG_PATH), "--id", "9"])
    assert e.exit_code == 0 and "no customer events" in e.output
    assert nf.exit_code == 1 and "customer not found" in nf.output


def test_repo_readonly_and_parameterized(monkeypatch):
    calls = []

    def fake(config, sql, params=()):
        calls.append((sql.strip().lower(), params))
        return type("R", (), {"ok": True, "rows": [{"id": 1, "customer_key": "c", "lane": "btc", "port": 1}], "message": "OK"})()

    monkeypatch.setattr(customer_repo, "query_database_params", fake)
    customer_repo.resolve_customer_target(type("C", (), {})(), customer_id=1)
    customer_repo.list_customer_policy_history(type("C", (), {})(), customer_id=1, limit=5000)
    customer_repo.list_customer_events(type("C", (), {})(), customer_id=1, limit=0)
    customer_repo.list_customer_audit(type("C", (), {})(), customer_id=1, limit=1)
    customer_repo.list_latest_events(type("C", (), {})(), limit=20, subject_type="customer", severity="info")
    assert all(s.startswith(("select", "with")) for s, _ in calls)
    assert all("%s" in s for s, _ in calls)
    assert all("insert" not in s and "update" not in s and "delete" not in s for s, _ in calls)
