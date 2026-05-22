from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.services import customer_read_service
from mpf.services.phase11_canary_db_visibility_activation_service import build_phase11_canary_db_visibility_activation_report
from mpf.domain.production import Phase11CanaryDbVisibilityActivationRequest


def _cfg():
    from mpf.config import load_config
    return load_config(Path("configs/mpf.example.yaml"))


def test_plan_create_no_rows(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    r = build_phase11_canary_db_visibility_activation_report(_cfg(), Phase11CanaryDbVisibilityActivationRequest())
    assert r["planned_action"] == "create_exact_canary_customer"
    assert r["mutation_performed"] is False


def test_already_present(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", lane="btc", name="x", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    r = build_phase11_canary_db_visibility_activation_report(_cfg(), Phase11CanaryDbVisibilityActivationRequest())
    assert r["final_decision"] == "DB_VISIBILITY_ALREADY_PRESENT"


def test_execute_without_confirms_blocked(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    req = Phase11CanaryDbVisibilityActivationRequest(requested_action="execute", expected_version="0.1.174")
    r = build_phase11_canary_db_visibility_activation_report(_cfg(), req)
    assert r["final_decision"] == "BLOCKED"
    assert r["mutation_performed"] is False


def test_cli_json_smoke(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    runner = CliRunner()
    res = runner.invoke(app, ["production", "canary-db-visibility-activate", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_db_visibility_activation"' in res.stdout
