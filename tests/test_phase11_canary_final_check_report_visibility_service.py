from pathlib import Path

from mpf.config import load_config
from mpf.services.phase11_canary_final_check_report_visibility_service import build_phase11_canary_final_check_report_visibility_report
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def test_ready_report_emits_generated_evidence():
    ev = Phase11CanaryVisibilityEvidence(
        customer_key="canary-btc-001", lane="btc", port=20001, backend_target="172.18.0.3:60010",
        canary_customer_db_visible=True, usage_visibility_ok=True, reject_visibility_ok=True,
        session_visibility_ok=True, unique_ip_visibility_ok=True, worker_visibility_ok=True, abuse_coverage_ok=True,
    )
    r = build_phase11_canary_final_check_report_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.197", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["final_decision"] == "READY"
    gev = r["generated_evidence"]
    assert isinstance(gev, dict)
    assert gev["evidence_source"] == "live_source_backed_canary_final_check_report"
    assert gev["final_check_report_ok"] is True
    assert gev["mutation_performed"] is False


def test_fail_closed_when_prereq_missing():
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, canary_customer_db_visible=True, usage_visibility_ok=True)
    r = build_phase11_canary_final_check_report_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.197", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["final_decision"] == "BLOCKED"
    assert r["generated_evidence"] is None
    assert "missing_worker_visibility_ok" in r["blockers"]
