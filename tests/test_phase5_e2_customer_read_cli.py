from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")


def _fake_customer(service_days=30):
    class C:
        pass

    c = C()
    c.id = 1
    c.customer_key = "cust_a"
    c.lane = "btc"
    c.name = "alice"
    c.port = 20001
    c.status = "active"
    c.activation_mode = "immediate"
    c.service_days = service_days
    c.activated_at = None
    c.starts_at = None
    c.expires_at = None
    c.first_connected_at = None
    c.expired_at = None
    c.delete_eligible_at = None
    c.deleted_at = None
    c.auto_expire_enabled = False
    c.auto_delete_enabled = False
    c.lifecycle_note = None
    c.miners = 1
    c.farms = 1
    c.maxconn = 1
    c.rate_per_min = 1
    c.burst = 1
    c.ips_mode = "any"
    c.abuse_exempt = False
    c.abuse_exempt_reason = None
    c.abuse_exempt_until = None
    c.abuse_exempt_by = None
    c.enabled_ip_pins = []
    return c


def test_customer_show_requires_exactly_one_target():
    res = RUNNER.invoke(app, ["customer", "show", "--config", str(CONFIG_PATH)])
    assert res.exit_code == 1


def test_customer_show_rejects_multiple_targets():
    res = RUNNER.invoke(app, ["customer", "show", "--config", str(CONFIG_PATH), "--customer-key", "cust_a", "--id", "1"])
    assert res.exit_code == 1


def test_customer_show_by_id(monkeypatch):
    from mpf.interfaces import cli

    class R:
        ok = True
        message = "OK"
        customer = _fake_customer()

    monkeypatch.setattr(cli.customer_read_service, "show_customer", lambda *a, **k: R())
    res = RUNNER.invoke(app, ["customer", "show", "--config", str(CONFIG_PATH), "--id", "1"])
    assert res.exit_code == 0


def test_customer_show_by_port(monkeypatch):
    from mpf.interfaces import cli

    class R:
        ok = True
        message = "OK"
        customer = _fake_customer(service_days=None)

    monkeypatch.setattr(cli.customer_read_service, "show_customer", lambda *a, **k: R())
    res = RUNNER.invoke(app, ["customer", "show", "--config", str(CONFIG_PATH), "--port", "20001"])
    assert res.exit_code == 0
    assert "service_days: None" in res.output



def test_customer_show_accepts_direct_customer_key_argument(monkeypatch):
    from mpf.interfaces import cli

    class R:
        ok = True
        message = "OK"
        customer = _fake_customer()

    seen = {}
    def show_customer(_config, **kwargs):
        seen.update(kwargs)
        return R()

    monkeypatch.setattr(cli.customer_read_service, "show_customer", show_customer)
    res = RUNNER.invoke(app, ["customer", "show", "cust_a", "--config", str(CONFIG_PATH)])
    assert res.exit_code == 0, res.output
    assert seen == {"customer_key": "cust_a", "customer_id": None, "port": None}
    assert "customer_key: cust_a" in res.output

def test_customer_list_filters_status(monkeypatch):
    from mpf.interfaces import cli
    from mpf.repositories.customer_repo import CustomerRecord

    class L:
        ok = True
        message = "OK"
        customers = [CustomerRecord(1, None, "btc", "a", 1, "active", "immediate", None, None)]

    captured = {}

    def fake(config, **kwargs):
        captured.update(kwargs)
        return L()

    monkeypatch.setattr(cli.customer_read_service, "list_customer_status", fake)
    res = RUNNER.invoke(app, ["customer", "list", "--config", str(CONFIG_PATH), "--status", "active"])
    assert res.exit_code == 0
    assert captured["status"] == "active"
    assert "firewall_change: no" in res.output


def test_customer_list_empty_non_deleted_message(monkeypatch):
    from mpf.interfaces import cli

    class L:
        ok = True
        message = "OK"
        customers = []

    monkeypatch.setattr(cli.customer_read_service, "list_customer_status", lambda config, **kwargs: L())
    res = RUNNER.invoke(app, ["customer", "list", "--config", str(CONFIG_PATH)])
    assert "no non-deleted customers; use --include-deleted to show deleted rows" in res.output
