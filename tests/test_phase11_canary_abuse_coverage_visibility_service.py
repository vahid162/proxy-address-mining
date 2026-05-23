from pathlib import Path
from types import SimpleNamespace

from mpf.services.phase11_canary_abuse_coverage_visibility_service import build_phase11_canary_abuse_coverage_visibility_report
from mpf.services.phase11_canary_visibility_bundle_service import (
    Phase11CanaryVisibilityEvidence,
    build_phase11_canary_visibility_bundle_report,
    merge_phase11_canary_visibility_evidence,
)


def _cfg():
    from mpf.config import load_config

    return load_config(Path("configs/mpf.example.yaml"))


def _canary_row(port=20001):
    return SimpleNamespace(customer_key="canary-btc-001", lane="btc", port=port)


def test_abuse_coverage_visible_with_exact_scope(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert r["final_decision"] == "ABUSE_COVERAGE_VISIBLE"
    assert r["generated_evidence"]["abuse_coverage_ok"] is True
    assert r["generated_evidence"]["abuse_evidence_source"] == "live_source_backed_canary_abuse_coverage"


def test_abuse_coverage_blocked_wrong_scope(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row(port=20002)], message="ok"))
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert r["final_decision"] == "BLOCKED"
    assert "canary_customer_db_visibility_not_exact_scope" in r["blockers"]


def test_abuse_coverage_blocked_unexpected_active_customer(monkeypatch):
    rows = [_canary_row(), SimpleNamespace(customer_key="other", lane="btc", port=21000)]
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=rows, message="ok"))
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert r["final_decision"] == "BLOCKED"


def test_abuse_coverage_blocked_customer_list_read_failed(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=False, customers=[], message="fail"))
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert r["final_decision"] == "BLOCKED"
    assert "customer_list_read_failed" in r["blockers"]


def test_abuse_coverage_blocked_wrong_baseline(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.167")
    assert r["final_decision"] == "BLOCKED"
    assert "farm5_baseline_version_not_allowed" in r["blockers"]


def test_abuse_coverage_blocked_missing_transition_policy(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    monkeypatch.setattr("mpf.services.phase11_canary_abuse_coverage_visibility_service.AbuseDryRunInput.threshold_seconds", 1800)
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert r["final_decision"] == "BLOCKED"
    assert "missing_one_hour_abuse_transition_policy" in r["blockers"]


def test_bundle_merge_preserves_abuse_allowlisted_source(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    usage = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_usage", usage_visibility_ok=True, usage_reference="u", total_connections=1)
    worker = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_external_canary_stratum_transcript", worker_visibility_ok=True, worker_reference="w")
    abuse = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_abuse_coverage", abuse_coverage_ok=True, abuse_reference="a")
    merged = merge_phase11_canary_visibility_evidence([usage, worker, abuse], customer_key="canary-btc-001", lane="btc", port=20001)
    b = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168", evidence=merged)
    assert b["visibility"]["abuse_coverage_visibility"]["status"] == "PRESENT"
    assert "abuse_coverage_visibility" not in b["missing_visibility_primitives"]
    assert b["visibility"]["unique_workers_visibility"]["status"] == "PRESENT"


def test_bundle_rejects_bogus_abuse_source(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, abuse_coverage_ok=True, abuse_reference="a", abuse_evidence_source="bogus_source")
    b = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168", evidence=ev)
    assert b["visibility"]["abuse_coverage_visibility"]["status"] != "PRESENT"


def test_abuse_coverage_blocked_missing_over_tracking(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    fake = SimpleNamespace(OVER_TRACKING=SimpleNamespace(value="x"), OVER_GRACE=SimpleNamespace(value="over_grace"), HARD=SimpleNamespace(value="hard"))
    monkeypatch.setattr("mpf.services.phase11_canary_abuse_coverage_visibility_service.AbuseStatus", fake)
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert "missing_abuse_state_coverage:over_tracking" in r["blockers"]


def test_abuse_coverage_blocked_missing_over_grace(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    fake = SimpleNamespace(OVER_TRACKING=SimpleNamespace(value="over_tracking"), OVER_GRACE=SimpleNamespace(value="x"), HARD=SimpleNamespace(value="hard"))
    monkeypatch.setattr("mpf.services.phase11_canary_abuse_coverage_visibility_service.AbuseStatus", fake)
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert "missing_abuse_state_coverage:over_grace" in r["blockers"]


def test_abuse_coverage_blocked_missing_hard(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    fake = SimpleNamespace(OVER_TRACKING=SimpleNamespace(value="over_tracking"), OVER_GRACE=SimpleNamespace(value="over_grace"), HARD=SimpleNamespace(value="x"))
    monkeypatch.setattr("mpf.services.phase11_canary_abuse_coverage_visibility_service.AbuseStatus", fake)
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert "missing_abuse_state_coverage:hard" in r["blockers"]


def test_abuse_coverage_blocked_when_abuse_automation_not_proven_disabled(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    monkeypatch.setattr("mpf.services.phase11_canary_abuse_coverage_visibility_service._parse_current_state_block", lambda *_: {"abuse_automation_allowed": "yes", "restore_lock_record_execution_allowed": "controlled_boundary_only", "production_traffic": "none"})
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert "abuse_automation_not_proven_disabled" in r["blockers"]


def test_abuse_coverage_blocked_when_scheduler_not_proven_disabled(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    monkeypatch.setattr("mpf.services.phase11_canary_abuse_coverage_visibility_service._parse_current_state_block", lambda *_: {"abuse_automation_allowed": "no", "restore_lock_record_execution_allowed": "wrong", "production_traffic": "none"})
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert "scheduler_not_proven_disabled" in r["blockers"]


def test_abuse_coverage_blocked_when_worker_enforcement_not_proven_disabled(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: SimpleNamespace(ok=True, customers=[_canary_row()], message="ok"))
    monkeypatch.setattr("mpf.services.phase11_canary_abuse_coverage_visibility_service._parse_current_state_block", lambda *_: {"abuse_automation_allowed": "no", "restore_lock_record_execution_allowed": "controlled_boundary_only", "production_traffic": "none", "current_accepted_phase": "Phase 12", "current_working_phase": "Phase 12"})
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.187", farm5_baseline_version="0.1.168")
    assert "worker_enforcement_not_proven_disabled" in r["blockers"]
