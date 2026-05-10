from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")


def _fake_result(ok: bool = True):
    class R:
        message = "DRY_RUN_OK"
        customer_id = 1
        customer_key = "cust_a"
        firewall_change = "no"
        nat_change = "no"
        runtime_change = "no"
        would_create_customer = True
        would_mutate_customer = True
        would_create_policy_version = True
        would_mutate_ip_pins = False
        would_create_event = True
        would_create_audit = True
        
    x = R()
    x.ok = ok
    return x


def test_customer_add_dry_run_default(monkeypatch):
    from mpf.interfaces import cli

    monkeypatch.setattr(cli.customer_mutation_service, "create_db_only_customer", lambda config, req, dry_run=True: _fake_result())
    res = RUNNER.invoke(app, ["customer", "add", "--config", str(CONFIG_PATH), "--lane", "btc", "--name", "n", "--customer-key", "cust_a", "--port", "23138", "--miners", "1", "--farms", "1", "--maxconn", "1", "--rate-per-min", "1", "--burst", "1"])
    assert res.exit_code == 0
    assert "firewall_change: no" in res.output and "runtime_change: no" in res.output


def test_customer_add_yes_requires_mpf_user_on_local_peer(monkeypatch):
    from mpf.interfaces import cli

    monkeypatch.setattr(cli, "_guard_customer_write_local_peer", lambda cfg, command_hint: (_ for _ in ()).throw(SystemExit(1)))
    res = RUNNER.invoke(app, ["customer", "add", "--config", str(CONFIG_PATH), "--lane", "btc", "--name", "n", "--customer-key", "cust_a", "--port", "23138", "--miners", "1", "--farms", "1", "--maxconn", "1", "--rate-per-min", "1", "--burst", "1", "--yes"])
    assert res.exit_code != 0


def test_customer_list_still_works(monkeypatch):
    from mpf.interfaces import cli
    from mpf.repositories.customer_repo import CustomerRecord

    class L:
        ok = True
        message = "OK"
        customers = [CustomerRecord(1, "btc", "a", 23138, "active", None)]

    monkeypatch.setattr(cli.customer_read_service, "list_customer_status", lambda config, limit=100: L())
    res = RUNNER.invoke(app, ["customer", "list", "--config", str(CONFIG_PATH)])
    assert res.exit_code == 0

