from mpf.config import load_config
from mpf.services.phase7_usage_policy_readiness_service import build_phase7_usage_policy_readiness_report
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")

def test_phase7_readiness_report_blocked_defaults() -> None:
    cfg = load_config(example_config_path())
    r = build_phase7_usage_policy_readiness_report(cfg)
    assert r["component"] == "phase7_usage_policy_readiness"
    assert r["final_decision"] == "BLOCKED"
    assert r["readiness_status"] == "PHASE7_READINESS_DEFINED_NOT_ACCEPTED"
    assert r["authorization_status"] == "PHASE7_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED"
    for k in ("execution_allowed","phase7_acceptance_allowed","usage_automation_authorized","usage_collectors_authorized","policy_reject_collectors_authorized","abuse_automation_authorized","customer_nat_authorized","production_traffic_authorized","phase8_start_allowed"):
        assert r[k] is False

def test_phase7_safety_flags_all_false() -> None:
    cfg = load_config(example_config_path())
    r = build_phase7_usage_policy_readiness_report(cfg)
    for k,v in r.items():
        if k.endswith("_allowed") or k.endswith("_executed") or k.endswith("_written") or k.endswith("_changed"):
            if isinstance(v, bool):
                assert v is False


def test_phase7_ai_task_doc_passes_readiness_detector() -> None:
    cfg = load_config(example_config_path())
    r = build_phase7_usage_policy_readiness_report(cfg)
    assert r["ai_phase7_task_present"] is True
    assert "ai_phase7_task_present" not in r["blockers"]


def test_phase7_sync_evidence_generic_and_compatibility_aliases_present() -> None:
    cfg = load_config(example_config_path())
    r = build_phase7_usage_policy_readiness_report(cfg)
    assert "latest_recorded_farm5_sync_evidence_present" in r
    assert "fresh_farm5_sync_evidence_required_before_acceptance" in r
    assert "farm5_0_1_102_sync_evidence_present" in r
    assert "fresh_farm5_0_1_103_sync_evidence_required" in r
    assert r["execution_allowed"] is False
