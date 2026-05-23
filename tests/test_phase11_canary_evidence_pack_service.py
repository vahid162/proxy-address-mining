from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_canary_evidence_pack_service import FILES, build_phase11_canary_evidence_pack_report


def _cfg():
    from mpf.config import load_config

    return load_config(Path("configs/mpf.example.yaml"))


def _patch_defaults(monkeypatch):
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": {"canary_nat_target": "172.18.0.3:60010"}})
    monkeypatch.setattr("mpf.services.phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}})
    monkeypatch.setattr("mpf.services.phase11_canary_usage_visibility_service.build_phase11_canary_usage_visibility_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "usage_counters_visibility": {"status": "MISSING", "source": "x", "reference": None, "details": [], "blockers": ["missing_usage"]}, "final_decision": "BLOCKED", "blockers": [], "warnings": [], "next_required_step": "usage_counters_visibility"})
    monkeypatch.setattr("mpf.services.phase11_canary_reject_session_ip_evidence_capture_service.build_phase11_canary_reject_session_ip_evidence_capture_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}})
    monkeypatch.setattr("mpf.services.phase11_canary_reject_counters_visibility_service.build_phase11_canary_reject_counters_visibility_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "usage_counters_visibility": {"status": "MISSING", "source": "x", "reference": None, "details": [], "blockers": ["missing_usage"]}, "final_decision": "BLOCKED", "blockers": [], "warnings": [], "next_required_step": "usage_counters_visibility"})
    monkeypatch.setattr("mpf.services.phase11_canary_abuse_coverage_visibility_service.build_phase11_canary_abuse_coverage_visibility_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "usage_counters_visibility": {"status": "MISSING", "source": "x", "reference": None, "details": [], "blockers": ["missing_usage"]}, "final_decision": "BLOCKED", "blockers": [], "warnings": [], "next_required_step": "usage_counters_visibility"})
    monkeypatch.setattr("mpf.services.phase11_canary_final_check_report_visibility_service.build_phase11_canary_final_check_report_visibility_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "usage_counters_visibility": {"status": "MISSING", "source": "x", "reference": None, "details": [], "blockers": ["missing_usage"]}, "final_decision": "BLOCKED", "blockers": [], "warnings": [], "next_required_step": "usage_counters_visibility"})
    monkeypatch.setattr("mpf.services.phase11_canary_rollback_restore_visibility_service.build_phase11_canary_rollback_restore_visibility_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "usage_counters_visibility": {"status": "MISSING", "source": "x", "reference": None, "details": [], "blockers": ["missing_usage"]}, "final_decision": "BLOCKED", "blockers": [], "warnings": [], "next_required_step": "usage_counters_visibility"})


def test_manifest_safety(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "blockers": ["missing_conntrack_assured_canary_flow"], "final_decision": "BLOCKED"})
    r = build_phase11_canary_evidence_pack_report(_cfg(), out_dir=tmp_path / "o", collect_live=True, expected_version="0.1.192", farm5_baseline_version="0.1.168", sleep_fn=lambda *_: None)
    assert r["mutation_performed"] is False and r["phase11_accepted"] is False and r["limited_onboarding_allowed"] is False and r["no_onboarding_authorized"] is True


def test_observation_timing_aggregation(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    seq = [
        {"conntrack_assured": False, "forwarder_pool_seen": False, "bridge_loopback_seen": True, "b": ["missing_conntrack_assured_canary_flow", "missing_forwarder_pool_correlation"]},
        {"conntrack_assured": True, "forwarder_pool_seen": False, "bridge_loopback_seen": False, "b": ["missing_forwarder_pool_correlation", "missing_bridge_loopback_correlation"]},
        {"conntrack_assured": False, "forwarder_pool_seen": True, "bridge_loopback_seen": False, "b": ["missing_conntrack_assured_canary_flow", "missing_bridge_loopback_correlation"]},
    ]
    calls = {"i": 0, "sleep": []}

    def _runtime(*a, **k):
        i = calls["i"]
        calls["i"] += 1
        s = seq[i]
        return {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "captured_at": f"t{i}", "evidence_source": "live_source_backed_canary_runtime_path", "evidence_reference": f"r{i}", "source_query_or_artifact": "q", "conntrack_assured": s["conntrack_assured"], "forwarder_pool_seen": s["forwarder_pool_seen"], "bridge_loopback_seen": s["bridge_loopback_seen"]}, "blockers": s["b"], "final_decision": "BLOCKED", "mutation_performed": False}

    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", _runtime)
    out = tmp_path / "pack"
    r = build_phase11_canary_evidence_pack_report(_cfg(), out_dir=out, observation_seconds=6, observation_interval_seconds=2, max_observation_seconds=300, sleep_fn=lambda x: calls["sleep"].append(x))
    runtime = json.loads((out / FILES["runtime"]).read_text())
    gev = runtime["generated_evidence"]
    assert r["sample_count"] == 3
    assert calls["sleep"] == [2, 2]
    assert gev["conntrack_assured"] is True and gev["forwarder_pool_seen"] is True and gev["bridge_loopback_seen"] is True
    assert runtime["final_decision"] == "RUNTIME_PATH_EVIDENCE_READY"
    assert r["mutation_performed"] is False


def test_partial_runtime_observation(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "evidence_source": "live_source_backed_canary_runtime_path", "evidence_reference": "r", "source_query_or_artifact": "q", "bridge_loopback_seen": True, "conntrack_assured": False, "forwarder_pool_seen": False}, "blockers": ["missing_conntrack_assured_canary_flow", "missing_forwarder_pool_correlation"], "final_decision": "BLOCKED"})
    r = build_phase11_canary_evidence_pack_report(_cfg(), out_dir=tmp_path / "o", observation_seconds=1, observation_interval_seconds=1, sleep_fn=lambda *_: None)
    assert "bridge_loopback_seen" not in r["missing_evidence_primitives"]
    assert "conntrack_assured" in r["missing_evidence_primitives"] and "forwarder_pool_seen" in r["missing_evidence_primitives"]
    assert r["acceptance_review_final_decision"] == "BLOCKED"


def test_external_transcript_mode_multiple(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "blockers": ["missing_conntrack_assured_canary_flow"], "final_decision": "BLOCKED"})
    calls = []

    def _import(*a, **k):
        calls.append(k["transcript_json"])
        return {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "evidence_source": "live_source_backed_external_canary_stratum_transcript", "worker_visibility_ok": True, "worker_reference": f"w-{len(calls)}"}, "final_decision": "WORKER_STRATUM_EVIDENCE_READY"}

    monkeypatch.setattr("mpf.services.phase11_external_canary_stratum_transcript_import_service.build_phase11_external_canary_stratum_transcript_import_report", _import)
    t1 = tmp_path / "t1.json"; t1.write_text("{}")
    t2 = tmp_path / "t2.json"; t2.write_text("{}")
    out = tmp_path / "o"
    build_phase11_canary_evidence_pack_report(_cfg(), out_dir=out, external_stratum_transcript_json=[t1, t2], sleep_fn=lambda *_: None)
    assert calls == [t1, t2]
    assert (out / "external-stratum-transcript-import.json").exists()
    assert (out / "external-stratum-transcript-import-2.json").exists()


def test_transcript_failure_continues(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "blockers": ["missing_conntrack_assured_canary_flow"], "final_decision": "BLOCKED"})

    def _import(*a, **k):
        if str(k["transcript_json"]).endswith("bad.json"):
            raise RuntimeError("x")
        return {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}}

    monkeypatch.setattr("mpf.services.phase11_external_canary_stratum_transcript_import_service.build_phase11_external_canary_stratum_transcript_import_report", _import)
    good = tmp_path / "good.json"; good.write_text("{}")
    bad = tmp_path / "bad.json"; bad.write_text("{}")
    r = build_phase11_canary_evidence_pack_report(_cfg(), out_dir=tmp_path / "o", external_stratum_transcript_json=[good, bad], sleep_fn=lambda *_: None)
    assert any("external_stratum_transcript_2" == x for x in r["failed_collectors"])
    assert r["acceptance_review_final_decision"] == "BLOCKED"


def test_sub_collector_failure(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "blockers": ["missing_conntrack_assured_canary_flow"], "final_decision": "BLOCKED"})
    monkeypatch.setattr("mpf.services.phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("e")))
    out = tmp_path / "o"
    r = build_phase11_canary_evidence_pack_report(_cfg(), out_dir=out, sleep_fn=lambda *_: None)
    assert "usage_evidence" in r["failed_collectors"]
    assert (out / "manifest.json").exists()
    assert r["acceptance_review_final_decision"] == "BLOCKED"


def test_out_dir_safety(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "blockers": ["missing_conntrack_assured_canary_flow"], "final_decision": "BLOCKED"})
    with pytest.raises(ValueError):
        build_phase11_canary_evidence_pack_report(_cfg(), out_dir=Path("/"), sleep_fn=lambda *_: None)
    with pytest.raises(ValueError):
        build_phase11_canary_evidence_pack_report(_cfg(), out_dir=Path("/tmp"), sleep_fn=lambda *_: None)
    with pytest.raises(ValueError):
        build_phase11_canary_evidence_pack_report(_cfg(), out_dir=Path("/var"), sleep_fn=lambda *_: None)
    with pytest.raises(ValueError):
        build_phase11_canary_evidence_pack_report(_cfg(), out_dir=Path("/opt"), sleep_fn=lambda *_: None)
    with pytest.raises(ValueError):
        build_phase11_canary_evidence_pack_report(_cfg(), out_dir=Path("/opt/mpf-py-src"), sleep_fn=lambda *_: None)

    out = tmp_path / "x"; out.mkdir(); (out / "random.txt").write_text("keep")
    with pytest.raises(ValueError):
        build_phase11_canary_evidence_pack_report(_cfg(), out_dir=out, overwrite_out_dir=False, sleep_fn=lambda *_: None)
    (out / "manifest.json").write_text("{}");
    build_phase11_canary_evidence_pack_report(_cfg(), out_dir=out, overwrite_out_dir=True, sleep_fn=lambda *_: None)
    assert (out / "random.txt").exists()


def test_cli_smoke(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001}, "blockers": ["missing_conntrack_assured_canary_flow"], "final_decision": "BLOCKED"})
    runner = CliRunner()
    res = runner.invoke(app, ["production", "canary-evidence-pack", "--out-dir", str(tmp_path / "pack"), "--observation-seconds", "1", "--observation-interval-seconds", "1", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    manifest = json.loads((tmp_path / "pack" / "manifest.json").read_text())
    assert manifest["mutation_performed"] is False

def test_acceptance_mapping_from_bundle_present(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "evidence_source": "live_source_backed_canary_runtime_path", "evidence_reference": "runtime-ref", "source_query_or_artifact": "q", "conntrack_assured": True, "forwarder_pool_seen": True, "bridge_loopback_seen": True, "stratum_subscribe_ok": True, "stratum_authorize_ok": True, "stratum_set_difficulty_seen": True, "stratum_notify_seen": True}, "blockers": [], "final_decision": "RUNTIME_PATH_EVIDENCE_READY"})
    captured = {}
    def _accept(*a, **k):
        ev = k["evidence"]
        captured.update({
            "usage": ev.usage_visibility_ok, "reject": ev.reject_visibility_ok, "session": ev.session_visibility_ok,
            "ip": ev.unique_ip_visibility_ok, "worker": ev.worker_visibility_ok, "abuse": ev.abuse_coverage_ok,
            "final": ev.final_check_report_ok, "rollback": ev.rollback_reference, "source": ev.evidence_source,
        })
        return {"final_decision": "ACCEPTANCE_REVIEW_READY", "next_required_step": None}
    monkeypatch.setattr("mpf.services.phase11_canary_acceptance_review_service.build_phase11_canary_acceptance_review_report", _accept)
    def _bundle(*a, **k):
        return {"final_decision":"VISIBILITY_READY","missing_visibility_primitives":[],"missing_evidence_primitives":[],"visibility":{
            "canary_customer_db_visibility":{"status":"PRESENT"},"usage_counters_visibility":{"status":"PRESENT"},"reject_counters_visibility":{"status":"PRESENT"},
            "active_recent_sessions_visibility":{"status":"PRESENT"},"unique_ips_visibility":{"status":"PRESENT"},"unique_workers_visibility":{"status":"PRESENT"},
            "abuse_coverage_visibility":{"status":"PRESENT"},"final_check_report_visibility":{"status":"PRESENT"},"rollback_or_restore_plan_visibility":{"status":"PRESENT","reference":"rollback:ok"},
        }}
    monkeypatch.setattr("mpf.services.phase11_canary_visibility_bundle_service.build_phase11_canary_visibility_bundle_report", _bundle)
    r = build_phase11_canary_evidence_pack_report(_cfg(), out_dir=tmp_path/"o", sleep_fn=lambda *_: None)
    assert r["visibility_bundle_final_decision"] == "VISIBILITY_READY"
    assert r["acceptance_review_final_decision"] == "ACCEPTANCE_REVIEW_READY"
    assert captured["usage"] and captured["reject"] and captured["session"] and captured["ip"] and captured["worker"] and captured["abuse"] and captured["final"]
    assert captured["rollback"] == "rollback:ok"
    assert r["phase11_accepted"] is False and r["limited_onboarding_allowed"] is False and r["no_onboarding_authorized"] is True


def test_incomplete_visibility_remains_blocked(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key":"canary-btc-001","lane":"btc","port":20001}, "blockers": ["missing_conntrack_assured_canary_flow"], "final_decision":"BLOCKED"})
    monkeypatch.setattr("mpf.services.phase11_canary_acceptance_review_service.build_phase11_canary_acceptance_review_report", lambda *a, **k: {"final_decision":"BLOCKED","next_required_step":"usage_counters_visibility"})
    monkeypatch.setattr("mpf.services.phase11_canary_visibility_bundle_service.build_phase11_canary_visibility_bundle_report", lambda *a, **k: {"final_decision":"BLOCKED","missing_visibility_primitives":["usage_counters_visibility"],"missing_evidence_primitives":["conntrack_assured"],"visibility":{"usage_counters_visibility":{"status":"MISSING"}}})
    r = build_phase11_canary_evidence_pack_report(_cfg(), out_dir=tmp_path/"o", sleep_fn=lambda *_: None)
    assert r["acceptance_review_final_decision"] == "BLOCKED"
    assert "usage_counters_visibility" in r["missing_visibility_primitives"]


def test_overwrite_removes_dynamic_transcript_only(tmp_path, monkeypatch):
    _patch_defaults(monkeypatch)
    monkeypatch.setattr("mpf.services.phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report", lambda *a, **k: {"generated_evidence": {"customer_key":"canary-btc-001","lane":"btc","port":20001}, "blockers": ["missing_conntrack_assured_canary_flow"], "final_decision":"BLOCKED"})
    out = tmp_path / "out"; out.mkdir()
    (out / "manifest.json").write_text("x")
    (out / "external-stratum-transcript-import-2.json").write_text("x")
    (out / "external-stratum-transcript-import-99.json").write_text("x")
    (out / "random.txt").write_text("x")
    (out / ".keep").write_text("x")
    (out / "nested").mkdir()
    build_phase11_canary_evidence_pack_report(_cfg(), out_dir=out, overwrite_out_dir=True, sleep_fn=lambda *_: None)
    assert (out / "random.txt").exists()
    assert (out / ".keep").exists()
    assert (out / "nested").exists()
    assert not (out / "external-stratum-transcript-import-2.json").exists()
    assert not (out / "external-stratum-transcript-import-99.json").exists()
