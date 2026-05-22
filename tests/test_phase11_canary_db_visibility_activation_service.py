from pathlib import Path

from typer.testing import CliRunner

from mpf.domain.production import Phase11CanaryDbVisibilityActivationRequest
from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.repositories.customer_write_repo import CustomerMutationResult
from mpf.services import customer_read_service
from mpf.services.phase11_canary_db_visibility_activation_service import build_phase11_canary_db_visibility_activation_report


def _cfg():
    from mpf.config import load_config

    return load_config(Path("configs/mpf.example.yaml"))


def _execute_req() -> Phase11CanaryDbVisibilityActivationRequest:
    return Phase11CanaryDbVisibilityActivationRequest(
        requested_action="execute",
        expected_version="0.1.174",
        operator="operator-1",
        reason="phase11 canary db visibility",
        operator_confirmed=True,
        understand_db_only_canary=True,
        understand_no_firewall_or_nat=True,
        reviewed_rollback=True,
        fresh_farm5_sync_confirmed=True,
    )


def test_plan_create_no_rows(monkeypatch):
    monkeypatch.setattr(
        "mpf.services.customer_read_service.list_customer_status",
        lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]),
    )
    r = build_phase11_canary_db_visibility_activation_report(_cfg(), Phase11CanaryDbVisibilityActivationRequest())
    assert r["planned_action"] == "create_exact_canary_customer"
    assert r["mutation_performed"] is False
    assert r["db_mutation_performed"] is False


def test_already_present(monkeypatch):
    c = CustomerRecord(
        id=1,
        customer_key="canary-btc-001",
        lane="btc",
        name="x",
        port=20001,
        status="active",
        activation_mode=None,
        expires_at=None,
        deleted_at=None,
    )
    monkeypatch.setattr(
        "mpf.services.customer_read_service.list_customer_status",
        lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]),
    )
    r = build_phase11_canary_db_visibility_activation_report(_cfg(), Phase11CanaryDbVisibilityActivationRequest())
    assert r["final_decision"] == "DB_VISIBILITY_ALREADY_PRESENT"


def test_execute_without_confirms_blocked(monkeypatch):
    monkeypatch.setattr(
        "mpf.services.customer_read_service.list_customer_status",
        lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]),
    )
    req = Phase11CanaryDbVisibilityActivationRequest(requested_action="execute", expected_version="0.1.174")
    r = build_phase11_canary_db_visibility_activation_report(_cfg(), req)
    assert r["final_decision"] == "BLOCKED"
    assert r["mutation_performed"] is False


def test_execute_create_path_calls_create_db_only_customer_and_sets_db_only_flags(monkeypatch):
    monkeypatch.setattr(
        "mpf.services.customer_read_service.list_customer_status",
        lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]),
    )

    called: dict[str, object] = {}

    def _fake_create(config, req, *, dry_run=False):
        called["dry_run"] = dry_run
        called["request"] = req
        return CustomerMutationResult(ok=True, message="OK", customer_key=req.customer_key)

    monkeypatch.setattr("mpf.services.customer_mutation_service.create_db_only_customer", _fake_create)
    monkeypatch.setattr(
        "mpf.services.customer_mutation_service.restore_phase11_exact_canary_db_visibility_customer",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("restore must not be called in create path")),
    )

    r = build_phase11_canary_db_visibility_activation_report(_cfg(), _execute_req())

    req = called["request"]
    assert req.customer_key == "canary-btc-001"
    assert req.lane == "btc"
    assert req.port == 20001
    assert req.status == "active"
    assert req.policy.miners == 1
    assert req.policy.farms == 1
    assert req.policy.maxconn == 1
    assert req.policy.rate_per_min == 120
    assert req.policy.burst == 240
    assert req.policy.ips_mode == "any"
    assert called["dry_run"] is False

    assert r["final_decision"] == "DB_VISIBILITY_EXECUTED"
    assert r["mutation_performed"] is True
    assert r["db_mutation_performed"] is True
    assert r["firewall_mutation_performed"] is False
    assert r["nat_mutation_performed"] is False
    assert r["conntrack_mutation_performed"] is False
    assert r["docker_mutation_performed"] is False
    assert r["production_traffic_enabled"] is False


def test_execute_restore_path_calls_restore_and_sets_db_only_flags(monkeypatch):
    deleted = CustomerRecord(
        id=1,
        customer_key="canary-btc-001",
        lane="btc",
        name="x",
        port=20001,
        status="deleted",
        activation_mode=None,
        expires_at=None,
        deleted_at="2026-05-22T00:00:00+00:00",
    )
    monkeypatch.setattr(
        "mpf.services.customer_read_service.list_customer_status",
        lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[deleted]),
    )

    called: dict[str, object] = {}

    def _fake_restore(config, **kwargs):
        called.update(kwargs)
        return CustomerMutationResult(ok=True, message="OK", customer_key="canary-btc-001")

    monkeypatch.setattr(
        "mpf.services.customer_mutation_service.create_db_only_customer",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("create must not be called in restore path")),
    )
    monkeypatch.setattr(
        "mpf.services.customer_mutation_service.restore_phase11_exact_canary_db_visibility_customer",
        _fake_restore,
    )

    r = build_phase11_canary_db_visibility_activation_report(_cfg(), _execute_req())

    assert called["customer_key"] == "canary-btc-001"
    assert called["lane"] == "btc"
    assert called["port"] == 20001
    assert called["dry_run"] is False
    assert r["final_decision"] == "DB_VISIBILITY_EXECUTED"
    assert r["mutation_performed"] is True
    assert r["db_mutation_performed"] is True
    assert r["firewall_mutation_performed"] is False
    assert r["nat_mutation_performed"] is False
    assert r["conntrack_mutation_performed"] is False
    assert r["docker_mutation_performed"] is False


def test_cli_json_smoke(monkeypatch):
    monkeypatch.setattr(
        "mpf.services.customer_read_service.list_customer_status",
        lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]),
    )
    runner = CliRunner()
    res = runner.invoke(app, ["production", "canary-db-visibility-activate", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_db_visibility_activation"' in res.stdout
