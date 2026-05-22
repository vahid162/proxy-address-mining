from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.services import customer_read_service
from mpf.services.phase11_canary_acceptance_review_service import (
    Phase11CanaryAcceptanceEvidence,
    build_phase11_canary_acceptance_review_report,
    load_phase11_canary_acceptance_evidence_json,
)


def _cfg():
    from mpf.config import load_config

    return load_config(Path("configs/mpf.example.yaml"))


def _base_evidence():
    return Phase11CanaryAcceptanceEvidence(
        evidence_reference="ref",
        farm5_baseline_version="0.1.168",
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


def _report(monkeypatch, ev: Phase11CanaryAcceptanceEvidence, **kwargs):
    cfg = _cfg()
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    return build_phase11_canary_acceptance_review_report(
        cfg,
        customer_key=kwargs.get("customer_key", "canary-btc-001"),
        lane=kwargs.get("lane", "btc"),
        port=kwargs.get("port", 20001),
        expected_version=kwargs.get("expected_version", "0.1.181"),
        farm5_baseline_version=kwargs.get("farm5_baseline_version", "0.1.168"),
        evidence=ev,
    )


def test_ready_when_all_present(monkeypatch):
    report = _report(monkeypatch, _base_evidence())
    assert report["final_decision"] == "ACCEPTANCE_REVIEW_READY"


def test_blocks_wrong_farm5_baseline_version(monkeypatch):
    report = _report(monkeypatch, _base_evidence(), farm5_baseline_version="0.1.167")
    assert "farm5_baseline_version_not_allowed" in report["blockers"]


def test_blocks_evidence_farm5_mismatch(monkeypatch):
    ev = _base_evidence()
    ev.farm5_baseline_version = "0.1.167"
    report = _report(monkeypatch, ev)
    assert "farm5_baseline_version_mismatch_with_evidence" in report["blockers"]


def test_blocks_loopback_variants(monkeypatch):
    ev = _base_evidence(); ev.canary_nat_target = "127.0.0.2:60010"
    r1 = _report(monkeypatch, ev)
    assert "loopback_canary_target_forbidden" in r1["blockers"]
    ev2 = _base_evidence(); ev2.canary_nat_target = "localhost:60010"
    r2 = _report(monkeypatch, ev2)
    assert "localhost_canary_target_forbidden" in r2["blockers"]


def test_blocks_public_and_wrong_port_targets(monkeypatch):
    ev = _base_evidence(); ev.canary_nat_target = "8.8.8.8:60010"
    r1 = _report(monkeypatch, ev)
    assert "non_private_canary_target_forbidden" in r1["blockers"]
    ev2 = _base_evidence(); ev2.canary_nat_target = "172.18.0.3:60011"
    r2 = _report(monkeypatch, ev2)
    assert "wrong_canary_target_port" in r2["blockers"]


def test_blocks_duplicate_and_extra_nat(monkeypatch):
    ev = _base_evidence(); ev.canary_nat_rule_count = 2
    r1 = _report(monkeypatch, ev)
    assert "duplicate_or_missing_canary_nat_rule" in r1["blockers"]
    ev2 = _base_evidence(); ev2.no_extra_customer_nat_rules = False
    r2 = _report(monkeypatch, ev2)
    assert "extra_customer_nat_rule_detected" in r2["blockers"]


def test_blocks_missing_bridge_and_direct_20170_not_blocked(monkeypatch):
    ev = _base_evidence(); ev.bridge_healthy = False
    r1 = _report(monkeypatch, ev)
    assert "bridge_unhealthy_or_missing" in r1["blockers"]
    ev2 = _base_evidence(); ev2.direct_v2raya_20170_blocked = False
    r2 = _report(monkeypatch, ev2)
    assert "direct_v2raya_20170_not_blocked" in r2["blockers"]


def test_evidence_json_missing_fields_default_false(tmp_path):
    p = tmp_path / "evidence.json"
    p.write_text("{}", encoding="utf-8")
    ev = load_phase11_canary_acceptance_evidence_json(p)
    assert ev.stratum_subscribe_ok is False
    assert ev.bridge_healthy is False


def test_cli_json_smoke(tmp_path, monkeypatch):
    runner = CliRunner()
    p = tmp_path / "evidence.json"
    p.write_text('{"evidence_reference":"ref"}', encoding="utf-8")
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    res = runner.invoke(
        app,
        [
            "production",
            "canary-acceptance-review",
            "--expected-version",
            "0.1.181",
            "--farm5-baseline-version",
            "0.1.168",
            "--evidence-json",
            str(p),
            "--output",
            "json",
            "--config",
            "configs/mpf.example.yaml",
        ],
    )
    assert res.exit_code == 0
    assert '"component": "phase11_canary_acceptance_review"' in res.stdout


def test_customer_list_read_failure_blocks_fail_closed(monkeypatch):
    cfg = _cfg()
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=False, message="db read failed", customers=[]))
    report = build_phase11_canary_acceptance_review_report(
        cfg,
        customer_key="canary-btc-001",
        lane="btc",
        port=20001,
        expected_version="0.1.181",
        farm5_baseline_version="0.1.168",
        evidence=Phase11CanaryAcceptanceEvidence(),
    )
    assert report["final_decision"] == "BLOCKED"
    assert "customer_list_read_failed" in report["blockers"]
    assert report["mutation_performed"] is False
    assert report["firewall_mutation_performed"] is False
    assert report["nat_mutation_performed"] is False
    assert report["conntrack_mutation_performed"] is False


def test_cli_collect_live_review_smoke(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    monkeypatch.setattr(
        "mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report",
        lambda *a, **k: {"evidence": {"mpf_nat_pre_exists": True, "prerouting_hook_present": True, "canary_nat_rule_present": True, "canary_nat_rule_count": 1, "canary_nat_target": "172.18.0.3:60010", "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True}},
    )
    res = runner.invoke(
        app,
        [
            "production",
            "canary-acceptance-review",
            "--expected-version",
            "0.1.181",
            "--farm5-baseline-version",
            "0.1.168",
            "--collect-live",
            "--output",
            "json",
            "--config",
            "configs/mpf.example.yaml",
        ],
    )
    assert res.exit_code == 0
    assert '"controlled_canary_artifact_present": true' in res.stdout
    assert '"backend_target": "172.18.0.3:60010"' in res.stdout
    assert '"final_decision": "BLOCKED"' in res.stdout
    assert '"mutation_performed": false' in res.stdout
    assert '"firewall_mutation_performed": false' in res.stdout
    assert '"nat_mutation_performed": false' in res.stdout
    assert '"conntrack_mutation_performed": false' in res.stdout


def test_cli_collect_visibility_out_of_scope_does_not_lift(monkeypatch, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    p = tmp_path / "vis.json"
    p.write_text('{"customer_key":"wrong","lane":"btc","port":20001,"usage_visibility_ok":true,"usage_reference":"ref"}', encoding="utf-8")
    res = runner.invoke(
        app,
        [
            "production",
            "canary-acceptance-review",
            "--expected-version", "0.1.181",
            "--farm5-baseline-version", "0.1.168",
            "--collect-visibility",
            "--visibility-json", str(p),
            "--output", "json",
            "--config", "configs/mpf.example.yaml",
        ],
    )
    assert res.exit_code == 0
    assert '"final_decision": "BLOCKED"' in res.stdout
    assert '"missing_visibility:usage_counters_visibility"' in res.stdout


def test_cli_collect_visibility_merges_multiple_artifacts(monkeypatch, tmp_path):
    runner = CliRunner()
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    usage = tmp_path / "usage.json"
    usage.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"usage_visibility_ok":true,"usage_reference":"usage-ref","total_connections":5}', encoding="utf-8")
    sess = tmp_path / "sess.json"
    sess.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"usage_visibility_ok":false,"session_visibility_ok":true,"session_reference":"session-ref","unique_ip_visibility_ok":true,"unique_ip_reference":"ip-ref"}', encoding="utf-8")
    res = runner.invoke(
        app,
        [
            "production", "canary-acceptance-review",
            "--expected-version", "0.1.181",
            "--farm5-baseline-version", "0.1.168",
            "--collect-visibility",
            "--visibility-json", str(usage),
            "--visibility-json", str(sess),
            "--output", "json",
            "--config", "configs/mpf.example.yaml",
        ],
    )
    assert res.exit_code == 0
    assert '"final_decision": "BLOCKED"' in res.stdout
    assert '"next_required_step": "reject_counters_visibility"' in res.stdout
    assert '"missing_visibility:reject_counters_visibility"' in res.stdout


def test_cli_collect_visibility_wrong_backend_not_lifted_with_collect_live(monkeypatch, tmp_path):
    runner = CliRunner()
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    monkeypatch.setattr(
        "mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report",
        lambda *a, **k: {"evidence": {"canary_nat_target": "172.18.0.3:60010"}},
    )
    usage = tmp_path / "usage.json"
    usage.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"usage_visibility_ok":true,"usage_reference":"usage-ref","total_connections":5}', encoding="utf-8")
    wrong_backend = tmp_path / "wrong_backend.json"
    wrong_backend.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"backend_target":"172.18.0.99:60010","session_visibility_ok":true,"session_reference":"session-ref","unique_ip_visibility_ok":true,"unique_ip_reference":"ip-ref"}', encoding="utf-8")
    res = runner.invoke(
        app,
        [
            "production", "canary-acceptance-review",
            "--expected-version", "0.1.181",
            "--farm5-baseline-version", "0.1.168",
            "--collect-live",
            "--collect-visibility",
            "--visibility-json", str(usage),
            "--visibility-json", str(wrong_backend),
            "--output", "json",
            "--config", "configs/mpf.example.yaml",
        ],
    )
    assert res.exit_code == 0
    assert '"final_decision": "BLOCKED"' in res.stdout
    assert '"missing_visibility:active_recent_sessions_visibility"' in res.stdout
    assert '"mutation_performed": false' in res.stdout
    assert '"production_traffic_enabled": false' in res.stdout


def test_next_step_usage_when_customer_db_present_but_usage_missing(monkeypatch):
    ev = _base_evidence()
    ev.usage_visibility_ok = False
    report = _report(monkeypatch, ev)
    assert "canary_customer_db_visibility" not in report["missing_visibility_primitives"]
    assert "usage_counters_visibility" in report["missing_visibility_primitives"]
    assert report["next_required_step"] == "usage_counters_visibility"
    assert "starting_with_canary_customer_db_visibility" not in report["next_required_step"]


def test_next_step_reject_when_usage_present_and_reject_missing(monkeypatch):
    ev = _base_evidence()
    ev.reject_visibility_ok = False
    report = _report(monkeypatch, ev)
    assert report["next_required_step"] == "reject_counters_visibility"


def test_next_step_evidence_priority_when_visibility_complete(monkeypatch):
    ev = _base_evidence()
    ev.conntrack_assured = False
    ev.stratum_subscribe_ok = False
    report = _report(monkeypatch, ev)
    assert report["missing_visibility_primitives"] == []
    assert "conntrack_assured" in report["missing_evidence_primitives"]
    assert report["next_required_step"] == "conntrack_assured"
