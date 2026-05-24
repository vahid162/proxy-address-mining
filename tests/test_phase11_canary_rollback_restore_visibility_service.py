from pathlib import Path

from mpf.config import load_config
from mpf.services.phase11_canary_rollback_restore_visibility_service import build_phase11_canary_rollback_restore_visibility_report


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def _patch_live(monkeypatch, **ev):
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": ev})


def test_ready_with_concrete_artifact(monkeypatch):
    _patch_live(monkeypatch, canary_nat_rule_present=True, mpf_nat_pre_exists=True, prerouting_hook_present=True, canary_nat_target="172.18.0.3:60010")
    r = build_phase11_canary_rollback_restore_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.204", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] == "READY"
    assert r["rollback_or_restore_plan_ok"] is True
    assert r["rollback_reference"]
    assert r["mutation_performed"] is False


def test_blocked_missing_artifact(monkeypatch):
    _patch_live(monkeypatch, canary_nat_rule_present=True, mpf_nat_pre_exists=True, prerouting_hook_present=True, canary_nat_target="172.18.0.3:60010")
    monkeypatch.setattr("mpf.services.phase11_canary_rollback_restore_visibility_service._render_restore_artifact", lambda v: {"status": "blocked"})
    r = build_phase11_canary_rollback_restore_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.204", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] == "BLOCKED"


def test_blocked_renderer_unavailable(monkeypatch):
    _patch_live(monkeypatch, canary_nat_rule_present=True, mpf_nat_pre_exists=True, prerouting_hook_present=True, canary_nat_target="172.18.0.3:60010")
    monkeypatch.setattr("mpf.services.phase11_canary_rollback_restore_visibility_service._render_restore_artifact", lambda v: (_ for _ in ()).throw(RuntimeError("x")))
    r = build_phase11_canary_rollback_restore_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.204", farm5_baseline_version="0.1.168", collect_live=True)
    assert "restore_payload_renderer_unavailable" in r["blockers"]


def test_blocked_backend_mismatch(monkeypatch):
    _patch_live(monkeypatch, canary_nat_rule_present=True, mpf_nat_pre_exists=True, prerouting_hook_present=True, canary_nat_target="172.18.0.3:12345")
    r = build_phase11_canary_rollback_restore_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.204", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] == "BLOCKED"


def test_blocked_wrong_scope(monkeypatch):
    _patch_live(monkeypatch, canary_nat_rule_present=True, mpf_nat_pre_exists=True, prerouting_hook_present=True, canary_nat_target="172.18.0.3:60010")
    r = build_phase11_canary_rollback_restore_visibility_report(_cfg(), customer_key="wrong", lane="btc", port=20001, expected_version="0.1.204", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] == "BLOCKED"
