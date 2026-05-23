from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.services import customer_read_service
from mpf.services.phase11_canary_usage_visibility_service import (
    Phase11CanaryUsageVisibilityEvidence,
    build_phase11_canary_usage_visibility_report,
)


def _cfg():
    from mpf.config import load_config

    return load_config(Path("configs/mpf.example.yaml"))


def test_db_missing_blocks(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    r = build_phase11_canary_usage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.185", farm5_baseline_version="0.1.168")
    assert r["usage_counters_visibility"]["status"] == "BLOCKED"


def test_exact_scope_present(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    ev = Phase11CanaryUsageVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=True, usage_reference="ref", total_connections=1)
    r = build_phase11_canary_usage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.185", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["final_decision"] == "USAGE_VISIBILITY_READY"


def test_cli_smoke(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    res = CliRunner().invoke(app, ["production", "canary-usage-visibility", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_usage_visibility"' in res.stdout
