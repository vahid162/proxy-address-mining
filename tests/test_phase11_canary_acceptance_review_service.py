from pathlib import Path
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence, build_phase11_canary_acceptance_review_report


def _cfg(tmp_path):
    from mpf.config import load_config
    return load_config(Path("configs/mpf.example.yaml"))


def _base_evidence():
    return Phase11CanaryAcceptanceEvidence(
        evidence_reference="ref",
        nat_counter_packets=1,
        nat_counter_bytes=10,
        conntrack_assured=True,
        stratum_subscribe_ok=True,
        stratum_authorize_ok=True,
        stratum_set_difficulty_seen=True,
        stratum_notify_seen=True,
        forwarder_pool_seen=True,
        bridge_loopback_seen=True,
        proxy_doctor_ok=True,
        bridge_healthy=True,
        bridge_reachable_from_forwarder=True,
        canary_nat_rule_present=True,
        canary_nat_rule_count=1,
        canary_nat_target="172.18.0.3:60010",
        mpf_nat_pre_exists=True,
        prerouting_hook_present=True,
        no_extra_customer_nat_rules=True,
        no_unexpected_mpf_firewall_references=True,
        rollback_reference="r",
        restore_reference="s",
        canary_customer_db_visible=True,
        usage_visibility_ok=True,
        reject_visibility_ok=True,
        session_visibility_ok=True,
        unique_ip_visibility_ok=True,
        worker_visibility_ok=True,
        abuse_coverage_ok=True,
        final_check_report_ok=True,
        v2raya_ui_local_only=True,
        btc_backend_local_only=True,
        bridge_no_host_publish=True,
        forwarder_uses_bridge_upstream=True,
        direct_v2raya_20170_blocked=True,
    )


def test_ready_when_all_present(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: type("R", (), {"rows": []})())
    report = build_phase11_canary_acceptance_review_report(cfg, customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.169", farm5_baseline_version="0.1.168", evidence=_base_evidence())
    assert report["final_decision"] == "ACCEPTANCE_REVIEW_READY"
    assert report["phase11_accepted"] is False
    assert report["mutation_performed"] is False


def test_blocks_missing_visibility(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: type("R", (), {"rows": []})())
    ev = _base_evidence(); ev.usage_visibility_ok = False; ev.canary_customer_db_visible = False
    report = build_phase11_canary_acceptance_review_report(cfg, customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.169", farm5_baseline_version="0.1.168", evidence=ev)
    assert report["final_decision"] == "BLOCKED"
    assert "canary_customer_db_visibility" in report["missing_visibility_primitives"]


def test_blocks_wrong_inputs_and_targets(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: type("R", (), {"rows": []})())
    ev = _base_evidence(); ev.canary_nat_target = "127.0.0.1:60010"
    r = build_phase11_canary_acceptance_review_report(cfg, customer_key="x", lane="zec", port=2, expected_version="0.1.169", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["final_decision"] == "BLOCKED"
    assert "customer_key_must_be_canary-btc-001" in r["blockers"]
    assert "loopback_canary_target_forbidden" in r["blockers"]


def test_version_mismatch_blocked(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: type("R", (), {"rows": []})())
    r = build_phase11_canary_acceptance_review_report(cfg, customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.1", farm5_baseline_version="0.1.168", evidence=_base_evidence())
    assert "expected_version_mismatch" in r["blockers"]
