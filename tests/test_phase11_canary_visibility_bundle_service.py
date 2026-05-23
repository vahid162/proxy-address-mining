from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import customer_read_service
from mpf.repositories.customer_repo import CustomerRecord
from mpf.services.phase11_canary_visibility_bundle_service import (
    Phase11CanaryVisibilityEvidence,
    build_phase11_canary_visibility_bundle_report,
    merge_phase11_canary_visibility_evidence,
)


def _cfg():
    from mpf.config import load_config

    return load_config(Path("configs/mpf.example.yaml"))


def test_missing_customer_visibility(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "MISSING"


def test_present_customer_visibility(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "PRESENT"


def test_usage_true_without_ref_is_missing(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    ev = Phase11CanaryVisibilityEvidence(usage_visibility_ok=True)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
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
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
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
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", collect_live=True, evidence=ev)
    assert "visibility_evidence_scope_mismatch" in r["blockers"]
    assert r["visibility"]["usage_counters_visibility"]["status"] == "BLOCKED"


def test_active_canary_wrong_lane_or_port_blocked(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="zec", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "BLOCKED"
    assert "canary_customer_db_scope_mismatch" in r["blockers"]


def test_rollback_reference_without_ok_remains_missing(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, rollback_reference="r")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["rollback_or_restore_plan_visibility"]["status"] == "MISSING"


def test_unexpected_active_customer_blocked(monkeypatch):
    c = CustomerRecord(id=1, customer_key="other", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168")
    assert r["visibility"]["canary_customer_db_visibility"]["status"] == "BLOCKED"
    assert "unexpected_active_customer_present" in r["blockers"]



def test_usage_integration_present_with_exact_scope_and_counter(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    ev = Phase11CanaryVisibilityEvidence(
        customer_key="canary-btc-001", lane="btc", port=20001,
        usage_visibility_ok=True, usage_reference="usage-ref", total_connections=1,
    )
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "PRESENT"
    assert r["visibility"]["usage_counters_visibility"]["reference"] == "usage-ref"
    for k in ("reject_counters_visibility", "active_recent_sessions_visibility", "unique_ips_visibility", "unique_workers_visibility", "abuse_coverage_visibility", "final_check_report_visibility", "rollback_or_restore_plan_visibility"):
        assert r["visibility"][k]["status"] != "PRESENT"
    assert r["final_decision"] == "PARTIAL_VISIBILITY"


def test_usage_integration_exact_scope_reference_without_counter_missing(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=True, usage_reference="usage-ref")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "MISSING"


def test_usage_integration_exact_scope_counter_without_reference_missing_with_warning(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=True, total_connections=2)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["usage_counters_visibility"]["status"] == "MISSING"
    assert "usage_visibility_ok_true_without_reference" in r["warnings"]


def test_merge_preserves_true_usage_when_later_false():
    usage_ev = Phase11CanaryVisibilityEvidence(
        customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=True, usage_reference="usage-ref", total_connections=2
    )
    session_ev = Phase11CanaryVisibilityEvidence(
        customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=False, session_visibility_ok=True, session_reference="session-ref"
    )
    merged = merge_phase11_canary_visibility_evidence([usage_ev, session_ev], customer_key="canary-btc-001", lane="btc", port=20001)
    assert merged.usage_visibility_ok is True
    assert merged.usage_reference == "usage-ref"
    assert merged.session_visibility_ok is True
    assert merged.session_reference == "session-ref"


def test_merge_does_not_accept_positive_without_reference():
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, session_visibility_ok=True)
    merged = merge_phase11_canary_visibility_evidence([ev], customer_key="canary-btc-001", lane="btc", port=20001)
    assert merged.session_visibility_ok is False
    assert merged.session_reference is None


def test_merge_fail_closed_on_scope_mismatch_and_backend_mismatch():
    ev_scope_mismatch = Phase11CanaryVisibilityEvidence(
        customer_key="other", lane="btc", port=20001, usage_visibility_ok=True, usage_reference="usage-ref"
    )
    ev_backend_mismatch = Phase11CanaryVisibilityEvidence(
        customer_key="canary-btc-001", lane="btc", port=20001, backend_target="172.18.0.99:60010", unique_ip_visibility_ok=True, unique_ip_reference="ip-ref"
    )
    merged = merge_phase11_canary_visibility_evidence(
        [ev_scope_mismatch, ev_backend_mismatch],
        customer_key="canary-btc-001",
        lane="btc",
        port=20001,
        expected_backend_target="172.18.0.3:60010",
    )
    assert merged.usage_visibility_ok is False
    assert merged.unique_ip_visibility_ok is False


def test_cli_visibility_bundle_accepts_repeated_evidence_json(monkeypatch, tmp_path):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    usage = tmp_path / "usage.json"
    usage.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"usage_visibility_ok":true,"usage_reference":"usage-ref","total_connections":3}', encoding="utf-8")
    sess = tmp_path / "sess.json"
    sess.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"usage_visibility_ok":false,"session_visibility_ok":true,"session_reference":"session-ref","unique_ip_visibility_ok":true,"unique_ip_reference":"ip-ref"}', encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(app, ["production", "canary-visibility-bundle", "--evidence-json", str(usage), "--evidence-json", str(sess), "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert '"usage_counters_visibility": {' in res.stdout
    assert '"next_required_step": "reject_counters_visibility"' in res.stdout


def test_cli_visibility_bundle_collect_live_wrong_backend_evidence_not_lifted(monkeypatch, tmp_path):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    monkeypatch.setattr(
        "mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report",
        lambda *a, **k: {"evidence": {"canary_nat_target": "172.18.0.3:60010"}},
    )
    usage = tmp_path / "usage.json"
    usage.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"usage_visibility_ok":true,"usage_reference":"usage-ref","total_connections":3}', encoding="utf-8")
    wrong_backend = tmp_path / "wrong_backend.json"
    wrong_backend.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"backend_target":"172.18.0.99:60010","session_visibility_ok":true,"session_reference":"session-ref","unique_ip_visibility_ok":true,"unique_ip_reference":"ip-ref"}', encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(app, ["production", "canary-visibility-bundle", "--collect-live", "--evidence-json", str(usage), "--evidence-json", str(wrong_backend), "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert '"next_required_step": "reject_counters_visibility"' in res.stdout
    assert '"mutation_performed": false' in res.stdout
    assert '"firewall_mutation_performed": false' in res.stdout

def test_bundle_next_step_moves_to_unique_workers_when_usage_reject_session_ip_present(monkeypatch, tmp_path):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    usage = tmp_path / "usage.json"
    usage.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"backend_target":"172.18.0.3:60010","usage_visibility_ok":true,"usage_reference":"usage-ref","total_connections":2}', encoding="utf-8")
    sess = tmp_path / "sess.json"
    sess.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"backend_target":"172.18.0.3:60010","session_visibility_ok":true,"session_reference":"session-ref","unique_ip_visibility_ok":true,"unique_ip_reference":"ip-ref"}', encoding="utf-8")
    rej = tmp_path / "rej.json"
    rej.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"backend_target":"172.18.0.3:60010","evidence_source":"live_source_backed_canary_reject_counters","reject_visibility_ok":true,"reject_reference":"iptables_filter_counter:canary-btc-001:btc:20001:abcd"}', encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(app, ["production", "canary-visibility-bundle", "--evidence-json", str(usage), "--evidence-json", str(sess), "--evidence-json", str(rej), "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert '"usage_counters_visibility": {' in res.stdout and '"status": "PRESENT"' in res.stdout
    assert '"reject_counters_visibility": {' in res.stdout
    assert '"active_recent_sessions_visibility": {' in res.stdout
    assert '"unique_ips_visibility": {' in res.stdout
    assert '"next_required_step": "unique_workers_visibility"' in res.stdout


def test_reject_evidence_wrong_backend_or_missing_ref_not_lifted():
    usage_ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=True, usage_reference="u")
    wrong_backend_reject = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, backend_target="172.18.0.99:60010", reject_visibility_ok=True, reject_reference="r")
    missing_ref_reject = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, reject_visibility_ok=True)
    merged = merge_phase11_canary_visibility_evidence([usage_ev, wrong_backend_reject, missing_ref_reject], customer_key="canary-btc-001", lane="btc", port=20001, expected_backend_target="172.18.0.3:60010")
    assert merged.usage_visibility_ok is True
    assert merged.reject_visibility_ok is False


def test_session_or_usage_cannot_lift_reject():
    sess_only = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, session_visibility_ok=True, session_reference="s", unique_ip_visibility_ok=True, unique_ip_reference="ip")
    usage_only = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, usage_visibility_ok=True, usage_reference="u")
    merged = merge_phase11_canary_visibility_evidence([sess_only, usage_only], customer_key="canary-btc-001", lane="btc", port=20001)
    assert merged.reject_visibility_ok is False


def test_reject_evidence_source_mismatch_not_lifted():
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="conntrack", reject_visibility_ok=True, reject_reference="r")
    merged = merge_phase11_canary_visibility_evidence([ev], customer_key="canary-btc-001", lane="btc", port=20001)
    assert merged.reject_visibility_ok is False


def test_worker_visibility_source_allowlist_fail_closed():
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="bogus_source", worker_visibility_ok=True, worker_reference="bad-ref")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["unique_workers_visibility"]["status"] != "PRESENT"

def test_final_check_merge_source_preservation(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    usage = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_usage", usage_visibility_ok=True, usage_reference="u", total_connections=1)
    worker = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_external_canary_stratum_transcript", worker_visibility_ok=True, worker_reference="w")
    abuse = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_abuse_coverage", abuse_coverage_ok=True, abuse_reference="a")
    final_check = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_final_check_report", final_check_report_ok=True, final_check_report_reference="f")
    merged = merge_phase11_canary_visibility_evidence([usage, worker, abuse, final_check], customer_key="canary-btc-001", lane="btc", port=20001)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=merged)
    assert r["visibility"]["final_check_report_visibility"]["status"] == "PRESENT"
    assert r["visibility"]["unique_workers_visibility"]["status"] == "PRESENT"
    assert r["visibility"]["abuse_coverage_visibility"]["status"] == "PRESENT"


def test_final_check_bogus_source_not_present(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, final_check_report_ok=True, final_check_report_reference="f", final_check_evidence_source="bogus")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["final_check_report_visibility"]["status"] != "PRESENT"


def test_rollback_merge_source_preservation(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    usage = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_usage", usage_visibility_ok=True, usage_reference="u", total_connections=1)
    rb = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_rollback_restore_plan", rollback_or_restore_plan_ok=True, rollback_reference="rb")
    merged = merge_phase11_canary_visibility_evidence([usage, rb], customer_key="canary-btc-001", lane="btc", port=20001)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=merged)
    assert r["visibility"]["rollback_or_restore_plan_visibility"]["status"] == "PRESENT"


def test_rollback_bogus_source_not_present(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, rollback_or_restore_plan_ok=True, rollback_reference="rb", rollback_restore_evidence_source="bogus")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["rollback_or_restore_plan_visibility"]["status"] != "PRESENT"


def test_runtime_primitives_wrong_source_not_lifted():
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="bogus", evidence_reference="r", source_query_or_artifact="a", conntrack_assured=True, forwarder_pool_seen=True, bridge_loopback_seen=True)
    merged = merge_phase11_canary_visibility_evidence([ev], customer_key="canary-btc-001", lane="btc", port=20001, expected_backend_target="172.18.0.3:60010")
    assert merged.conntrack_assured is False
    assert merged.forwarder_pool_seen is False
    assert merged.bridge_loopback_seen is False


def test_runtime_primitives_missing_reference_not_lifted():
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_runtime_path", source_query_or_artifact="artifact", conntrack_assured=True, forwarder_pool_seen=True, bridge_loopback_seen=True)
    merged = merge_phase11_canary_visibility_evidence([ev], customer_key="canary-btc-001", lane="btc", port=20001, expected_backend_target="172.18.0.3:60010")
    assert merged.conntrack_assured is False
    assert merged.forwarder_pool_seen is False
    assert merged.bridge_loopback_seen is False


def test_runtime_primitives_missing_artifact_not_lifted():
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_runtime_path", evidence_reference="ref", conntrack_assured=True, forwarder_pool_seen=True, bridge_loopback_seen=True)
    merged = merge_phase11_canary_visibility_evidence([ev], customer_key="canary-btc-001", lane="btc", port=20001, expected_backend_target="172.18.0.3:60010")
    assert merged.conntrack_assured is False
    assert merged.forwarder_pool_seen is False
    assert merged.bridge_loopback_seen is False


def test_visibility_missing_primitives_removes_only_proven_runtime_primitive(monkeypatch):
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_runtime_path", evidence_reference="rt-ref", source_query_or_artifact="artifact", bridge_loopback_seen=True, conntrack_assured=False, forwarder_pool_seen=False)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.191", farm5_baseline_version="0.1.168", evidence=ev)
    missing = r["missing_evidence_primitives"]
    assert "bridge_loopback_seen" not in missing
    assert "conntrack_assured" in missing
    assert "forwarder_pool_seen" in missing

