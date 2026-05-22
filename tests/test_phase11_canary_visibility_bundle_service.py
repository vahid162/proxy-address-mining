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
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "MISSING"


def test_present_customer_visibility(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "PRESENT"


def test_usage_true_without_ref_is_missing(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    ev = Phase11CanaryVisibilityEvidence(usage_visibility_ok=True)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "BLOCKED"
    assert "missing_canary_customer_db_visibility" in r["blockers"]


def test_cli_visibility_bundle_json_smoke(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    runner = CliRunner()
    res = runner.invoke(app, ["production", "canary-visibility-bundle", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_visibility_bundle"' in res.stdout


def test_positive_evidence_missing_scope_not_present(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    ev = Phase11CanaryVisibilityEvidence(customer_key=None, lane=None, port=None, usage_visibility_ok=True, usage_reference="ref")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "BLOCKED"
    assert "visibility_evidence_scope_mismatch" in r["blockers"]
    assert r["final_decision"] == "BLOCKED"


def test_wrong_backend_target_scope_blocked(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    monkeypatch.setattr(
        "mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report",
        lambda *a, **k: {"evidence": {"canary_nat_target": "172.18.0.3:60010"}},
    )
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, backend_target="172.18.0.99:60010", usage_visibility_ok=True, usage_reference="ref")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168", collect_live=True, evidence=ev)
    assert "visibility_evidence_scope_mismatch" in r["blockers"]
    assert r["visibility"]["usage_counters_visibility"]["status"] == "BLOCKED"


def test_active_canary_wrong_lane_or_port_blocked(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="zec", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "BLOCKED"
    assert "canary_customer_db_scope_mismatch" in r["blockers"]


def test_rollback_reference_without_ok_remains_missing(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, rollback_reference="r")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["rollback_or_restore_plan_visibility"]["status"] == "MISSING"


def test_unexpected_active_customer_blocked(monkeypatch):
    c = CustomerRecord(id=1, customer_key="other", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "BLOCKED"
    assert "unexpected_active_customer_present" in r["blockers"]



def test_usage_integration_present_with_exact_scope_and_counter(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    ev = Phase11CanaryVisibilityEvidence(
        customer_key="canary-btc-001", lane="btc", port=20001,
        usage_visibility_ok=True, usage_reference="usage-ref", total_connections=1,
    )
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "PRESENT"
    assert r["visibility"]["usage_counters_visibility"]["reference"] == "usage-ref"
    for k in ("reject_counters_visibility", "active_recent_sessions_visibility", "unique_ips_visibility", "unique_workers_visibility", "abuse_coverage_visibility", "final_check_report_visibility", "rollback_or_restore_plan_visibility"):
        assert r["visibility"][k]["status"] != "PRESENT"
    assert r["final_decision"] == "PARTIAL_VISIBILITY"


def test_usage_integration_exact_scope_reference_without_counter_missing(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=True, usage_reference="usage-ref")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "MISSING"


def test_usage_integration_exact_scope_counter_without_reference_missing_with_warning(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=True, total_connections=2)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.178", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "MISSING"
    assert "usage_visibility_ok_true_without_reference" in r["warnings"]
