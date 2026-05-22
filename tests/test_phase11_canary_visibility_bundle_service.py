from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import customer_read_service
from mpf.repositories.customer_repo import CustomerRecord
from mpf.services.phase11_canary_visibility_bundle_service import (
    Phase11CanaryVisibilityEvidence,
    build_phase11_canary_visibility_bundle_report,
)


def _cfg():
    from mpf.config import load_config

    return load_config(Path("configs/mpf.example.yaml"))


def test_missing_customer_visibility(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.173", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "MISSING"


def test_present_customer_visibility(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.173", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "PRESENT"


def test_usage_true_without_ref_is_missing(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    ev = Phase11CanaryVisibilityEvidence(usage_visibility_ok=True)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.173", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "MISSING"
    assert "usage_visibility_ok_true_without_reference" in r["warnings"]


def test_cli_visibility_bundle_json_smoke(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    runner = CliRunner()
    res = runner.invoke(app, ["production", "canary-visibility-bundle", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_visibility_bundle"' in res.stdout
