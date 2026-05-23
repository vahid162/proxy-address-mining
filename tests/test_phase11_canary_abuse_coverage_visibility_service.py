from pathlib import Path
from types import SimpleNamespace

from mpf.services.phase11_canary_abuse_coverage_visibility_service import build_phase11_canary_abuse_coverage_visibility_report
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence, build_phase11_canary_visibility_bundle_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path('configs/mpf.example.yaml'))


def test_abuse_coverage_visible_with_exact_scope(monkeypatch):
    monkeypatch.setattr('mpf.services.customer_read_service.list_customer_status', lambda *a, **k: SimpleNamespace(ok=True, customers=[SimpleNamespace(customer_key='canary-btc-001', lane='btc', port=20001)], message=''))
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key='canary-btc-001', lane='btc', port=20001, expected_version='0.1.187', farm5_baseline_version='0.1.168')
    assert r['final_decision'] == 'ABUSE_COVERAGE_VISIBLE'
    assert r['generated_evidence']['abuse_coverage_ok'] is True


def test_abuse_coverage_blocked_wrong_scope(monkeypatch):
    monkeypatch.setattr('mpf.services.customer_read_service.list_customer_status', lambda *a, **k: SimpleNamespace(ok=True, customers=[SimpleNamespace(customer_key='canary-btc-001', lane='btc', port=20002)], message=''))
    r = build_phase11_canary_abuse_coverage_visibility_report(_cfg(), customer_key='canary-btc-001', lane='btc', port=20001, expected_version='0.1.187', farm5_baseline_version='0.1.168')
    assert r['final_decision'] == 'BLOCKED'


def test_bundle_marks_abuse_visibility_present_with_source_backed_evidence(monkeypatch):
    monkeypatch.setattr('mpf.services.customer_read_service.list_customer_status', lambda *a, **k: SimpleNamespace(ok=True, customers=[SimpleNamespace(customer_key='canary-btc-001', lane='btc', port=20001)], message=''))
    ev = Phase11CanaryVisibilityEvidence(customer_key='canary-btc-001', lane='btc', port=20001, evidence_source='live_source_backed_canary_abuse_coverage', abuse_coverage_ok=True, abuse_reference='src')
    b = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key='canary-btc-001', lane='btc', port=20001, expected_version='0.1.187', farm5_baseline_version='0.1.168', evidence=ev)
    assert b['visibility']['abuse_coverage_visibility']['status'] == 'PRESENT'
    assert 'abuse_coverage_visibility' not in b['missing_visibility_primitives']
