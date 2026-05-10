from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")


def _result():
    class R:
        ok = True
        message = "DRY_RUN_OK"
        customer_id = 1
        customer_key = "cust_a"
        firewall_change = "no"
        nat_change = "no"
        runtime_change = "no"
        would_create_customer = False
        would_mutate_customer = True
        would_create_policy_version = True
        would_mutate_ip_pins = False
        would_create_event = True
        would_create_audit = True

    return R()


def _assert_safety_output(output: str) -> None:
    assert "firewall_change: no" in output
    assert "nat_change: no" in output
    assert "runtime_change: no" in output




def _disable_guard(monkeypatch):
    from mpf.interfaces import cli
    monkeypatch.setattr(cli, "write_local_peer_root_guard_message", lambda url, command_hint: None)

def test_customer_add_constructs_request_and_dry_run_default(monkeypatch):
    from mpf.interfaces import cli

    _disable_guard(monkeypatch)

    captured = {}

    def fake(config, req, dry_run=True):
        captured["req"] = req
        captured["dry_run"] = dry_run
        x = _result()
        x.would_create_customer = True
        return x

    monkeypatch.setattr(cli.customer_mutation_service, "create_db_only_customer", fake)
    res = RUNNER.invoke(app, ["customer", "add", "--config", str(CONFIG_PATH), "--lane", "btc", "--name", "n", "--customer-key", "cust_a", "--port", "23138", "--miners", "10", "--farms", "2", "--maxconn", "10", "--rate-per-min", "60", "--burst", "20"])
    assert res.exit_code == 0
    assert captured["dry_run"] is True
    assert captured["req"].lane == "btc" and captured["req"].policy.miners == 10
    _assert_safety_output(res.output)


def test_customer_update_rejects_partial_policy_fields(monkeypatch):
    from mpf.interfaces import cli

    _disable_guard(monkeypatch)

    called = {"n": 0}

    def fake(config, req, dry_run=True):
        called["n"] += 1
        return _result()

    monkeypatch.setattr(cli.customer_mutation_service, "update_db_only_customer", fake)
    res = RUNNER.invoke(app, ["customer", "update", "--config", str(CONFIG_PATH), "--customer-key", "cust_a", "--miners", "20"])
    assert res.exit_code == 1
    assert "requires all fields together" in res.output
    assert called["n"] == 0


def test_customer_update_constructs_request_when_all_policy_fields_present(monkeypatch):
    from mpf.interfaces import cli

    _disable_guard(monkeypatch)

    captured = {}

    def fake(config, req, dry_run=True):
        captured["req"] = req
        captured["dry_run"] = dry_run
        return _result()

    monkeypatch.setattr(cli.customer_mutation_service, "update_db_only_customer", fake)
    res = RUNNER.invoke(app, ["customer", "update", "--config", str(CONFIG_PATH), "--customer-key", "cust_a", "--miners", "20", "--farms", "4", "--maxconn", "20", "--rate-per-min", "80", "--burst", "30"])
    assert res.exit_code == 0
    assert captured["dry_run"] is True
    assert captured["req"].policy.maxconn == 20
    _assert_safety_output(res.output)


def test_customer_renew_constructs_request(monkeypatch):
    from mpf.interfaces import cli

    _disable_guard(monkeypatch)

    captured = {}
    def fake(config, req, dry_run=True):
        captured["req"] = req
        return _result()
    monkeypatch.setattr(cli.customer_mutation_service, "renew_db_only_customer", fake)
    res = RUNNER.invoke(app, ["customer", "renew", "--config", str(CONFIG_PATH), "--customer-key", "cust_a", "--service-days", "30"])
    assert res.exit_code == 0
    assert captured["req"].service_days == 30


def test_customer_disable_constructs_request(monkeypatch):
    from mpf.interfaces import cli

    _disable_guard(monkeypatch)

    captured = {}
    def fake(config, req, dry_run=True):
        captured["req"] = req
        return _result()
    monkeypatch.setattr(cli.customer_mutation_service, "disable_db_only_customer", fake)
    res = RUNNER.invoke(app, ["customer", "disable", "--config", str(CONFIG_PATH), "--customer-key", "cust_a"])
    assert res.exit_code == 0
    assert captured["req"].customer_key == "cust_a"


def test_customer_delete_constructs_soft_delete_request(monkeypatch):
    from mpf.interfaces import cli

    _disable_guard(monkeypatch)

    captured = {}
    def fake(config, req, dry_run=True):
        captured["req"] = req
        return _result()
    monkeypatch.setattr(cli.customer_mutation_service, "soft_delete_db_only_customer", fake)
    res = RUNNER.invoke(app, ["customer", "delete", "--config", str(CONFIG_PATH), "--customer-key", "cust_a"])
    assert res.exit_code == 0
    assert captured["req"].soft_delete_only is True


def test_customer_set_ips_constructs_request(monkeypatch):
    from mpf.interfaces import cli

    _disable_guard(monkeypatch)

    captured = {}
    def fake(config, req, dry_run=True):
        captured["req"] = req
        return _result()
    monkeypatch.setattr(cli.customer_mutation_service, "set_ips_db_only_customer", fake)
    res = RUNNER.invoke(app, ["customer", "set-ips", "--config", str(CONFIG_PATH), "--customer-key", "cust_a", "--ips-mode", "whitelist", "--ip", "10.1.0.0/24"])
    assert res.exit_code == 0
    assert captured["req"].ip_whitelist == ["10.1.0.0/24"]


def test_root_local_peer_guard_message_for_dry_run(monkeypatch):
    from mpf.interfaces import cli

    monkeypatch.setattr(cli, "_load", lambda config: type("C", (), {"database": type("DB", (), {"url": "postgresql:///mpf"})()})())
    monkeypatch.setattr(cli, "write_local_peer_root_guard_message", lambda url, command_hint: f"local peer PostgreSQL write requires mpf OS user; run: sudo -u mpf {command_hint}")
    res = RUNNER.invoke(app, ["customer", "renew", "--config", str(CONFIG_PATH), "--customer-key", "cust_a", "--service-days", "30"])
    assert res.exit_code == 1
    assert "sudo -u mpf /usr/local/bin/mpf customer renew ..." in res.output
    assert "--yes" not in res.output


def test_root_local_peer_guard_message_for_yes(monkeypatch):
    from mpf.interfaces import cli

    monkeypatch.setattr(cli, "_load", lambda config: type("C", (), {"database": type("DB", (), {"url": "postgresql:///mpf"})()})())
    monkeypatch.setattr(cli, "write_local_peer_root_guard_message", lambda url, command_hint: f"local peer PostgreSQL write requires mpf OS user; run: sudo -u mpf {command_hint}")
    res = RUNNER.invoke(app, ["customer", "disable", "--config", str(CONFIG_PATH), "--customer-key", "cust_a", "--yes"])
    assert res.exit_code == 1
    assert "--yes" in res.output


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

