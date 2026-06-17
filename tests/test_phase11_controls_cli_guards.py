from types import SimpleNamespace

from typer.testing import CliRunner

from mpf.domain.customer_lifecycle import DomainValidationError
from mpf.domain.customers import CustomerDisableRequest, CustomerUpdateRequest
from mpf.interfaces.cli import app
from mpf.repositories.customer_write_repo import CustomerMutationResult
from mpf.services import customer_dry_run_readiness_service as dryrun


CUSTOMER_ROW = {
    "id": "3",
    "customer_key": "limited-btc-001",
    "name": "limited-btc-001",
    "status": "active",
    "lane_id": "1",
    "activation_mode": "first_connect",
    "service_days": None,
    "deleted_at": "",
}


POLICY_ROW = {
    "id": "10",
    "version": "1",
    "miners": "1",
    "farms": "1",
    "maxconn": "1",
    "rate_per_min": "60",
    "burst": "10",
    "ips_mode": "any",
    "reason": "test",
}


def _fake_query(ok=True, rows=None, message="OK"):
    return SimpleNamespace(ok=ok, rows=list(rows or []), message=message)


def test_update_blocked_controlled(monkeypatch):
    import mpf.interfaces.cli as cli
    monkeypatch.setattr(cli, "_load", lambda p: SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf")))
    monkeypatch.setattr(cli.customer_mutation_service, "update_db_only_customer", lambda *a, **k: (_ for _ in ()).throw(DomainValidationError("status must be active/paused/expired/deleted")))
    res = CliRunner().invoke(app, ["customer", "update", "--customer-key", "limited-btc-001", "--status", "blocked"])
    assert res.exit_code == 1
    assert "status must be active/paused/expired/deleted" in res.output
    assert "Traceback" not in res.output


def test_no_yes_dry_run_reaches_service_and_yes_guards(monkeypatch):
    import mpf.interfaces.cli as cli
    cfg = SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf"))
    monkeypatch.setattr(cli, "_load", lambda p: cfg)
    called = []
    monkeypatch.setattr(cli.customer_mutation_service, "disable_db_only_customer", lambda cfg, req, dry_run: called.append(("disable", dry_run)) or CustomerMutationResult(ok=True, message="DRY_RUN_OK"))
    monkeypatch.setattr(cli.customer_mutation_service, "update_db_only_customer", lambda cfg, req, dry_run: called.append(("update", dry_run)) or CustomerMutationResult(ok=True, message="DRY_RUN_OK"))
    monkeypatch.setattr(cli, "write_local_peer_root_guard_message", lambda *a, **k: "local peer PostgreSQL write requires mpf OS user")
    r = CliRunner().invoke(app, ["customer", "disable", "--customer-key", "limited-btc-001"])
    assert r.exit_code == 0 and ("disable", True) in called
    r = CliRunner().invoke(app, ["customer", "update", "--customer-key", "limited-btc-001", "--status", "expired"])
    assert r.exit_code == 0 and ("update", True) in called
    r = CliRunner().invoke(app, ["customer", "update", "--customer-key", "limited-btc-001", "--status", "expired", "--yes"])
    assert r.exit_code == 1
    assert "local peer PostgreSQL write requires mpf OS user" in r.output


def test_disable_dry_run_uses_read_only_query_path(monkeypatch):
    calls = []

    def fake_query(config, sql, params=()):
        calls.append((sql, params))
        return _fake_query(rows=[CUSTOMER_ROW])

    monkeypatch.setattr(dryrun, "query_database_params", fake_query)
    result = dryrun.dry_run_disable_customer(
        SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf")),
        CustomerDisableRequest(customer_key="limited-btc-001", reason="probe"),
    )

    assert result.ok is True
    assert result.message == "DRY_RUN_OK"
    assert result.customer_id == 3
    assert result.would_mutate_customer is True
    assert result.would_create_event is True
    assert result.would_create_audit is True
    assert len(calls) == 1
    assert "select c.id" in calls[0][0].lower()


def test_update_dry_run_uses_read_only_query_path_for_status_only(monkeypatch):
    calls = []

    def fake_query(config, sql, params=()):
        calls.append((sql, params))
        return _fake_query(rows=[CUSTOMER_ROW])

    monkeypatch.setattr(dryrun, "query_database_params", fake_query)
    result = dryrun.dry_run_update_customer(
        SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf")),
        CustomerUpdateRequest(customer_key="limited-btc-001", status="expired"),
    )

    assert result.ok is True
    assert result.message == "DRY_RUN_OK"
    assert result.customer_id == 3
    assert result.would_mutate_customer is True
    assert result.would_create_event is True
    assert result.would_create_audit is True
    assert result.would_create_policy_version is False
    assert len(calls) == 1


def test_update_dry_run_validates_policy_and_lane_read_only(monkeypatch):
    calls = []

    def fake_query(config, sql, params=()):
        calls.append((sql, params))
        lowered = sql.lower()
        if "from customer_policies" in lowered:
            return _fake_query(rows=[POLICY_ROW])
        if "from lanes" in lowered:
            return _fake_query(rows=[{"id": "1", "enabled": "t"}])
        return _fake_query(rows=[CUSTOMER_ROW])

    monkeypatch.setattr(dryrun, "query_database_params", fake_query)
    req = CustomerUpdateRequest(
        customer_key="limited-btc-001",
        lane="btc",
        status="active",
        miners=1,
        farms=1,
        maxconn=1,
        rate_per_min=60,
        burst=10,
        ips_mode="any",
    )
    result = dryrun.dry_run_update_customer(SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf")), req)

    assert result.ok is True
    assert result.message == "DRY_RUN_OK"
    assert result.would_create_policy_version is True
    assert len(calls) == 3


def test_update_dry_run_fails_closed_on_read_error(monkeypatch):
    monkeypatch.setattr(dryrun, "query_database_params", lambda *a, **k: _fake_query(ok=False, message="read failed"))
    result = dryrun.dry_run_update_customer(
        SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf")),
        CustomerUpdateRequest(customer_key="limited-btc-001", status="expired"),
    )

    assert result.ok is False
    assert result.message == "read failed"
    assert result.would_mutate_customer is False
