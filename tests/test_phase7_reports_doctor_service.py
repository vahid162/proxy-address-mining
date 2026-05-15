from mpf.config import load_config
from mpf.services.phase7_reports_doctor_service import build_phase7_doctor_report, build_phase7_reports_summary
from pathlib import Path


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")



def test_phase7_reports_summary_defaults() -> None:
    r = build_phase7_reports_summary(load_config(example_config_path()))
    assert r["component"] == "phase7_reports_summary"
    assert r["final_decision"] == "BLOCKED"
    assert r["summary_status"] == "PHASE7_REPORTS_SUMMARY_DEFINED_NOT_ACCEPTED"
    assert r["authorization_status"] == "PHASE7_REPORTS_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED"
    assert r["execution_allowed"] is False
    assert r["phase7_acceptance_allowed"] is False
    assert isinstance(r["usage_policy_readiness_clean"], bool)
    assert isinstance(r["usage_accounting_contract_clean"], bool)
    assert isinstance(r["policy_reject_accounting_contract_clean"], bool)
    assert r["latest_recorded_farm5_sync_evidence_present"] is True
    assert r["no_fabricated_0_1_105_or_0_1_106_sync_evidence"] is True
    assert r["production_traffic_authorized"] is False
    assert r["firewall_apply_authorized"] is False
    assert r["customer_nat_authorized"] is False
    assert r["abuse_automation_authorized"] is False
    assert r["phase8_start_allowed"] is False


def test_phase7_doctor_defaults() -> None:
    r = build_phase7_doctor_report(load_config(example_config_path()))
    assert r["component"] == "phase7_doctor"
    assert r["final_verdict"] in {"OK", "BLOCKED"}
    assert r["final_decision"] == "BLOCKED"
    assert r["doctor_status"] == "PHASE7_DOCTOR_REPORT_ONLY"
    assert r["authorization_status"] == "PHASE7_DOCTOR_RUNTIME_NOT_AUTHORIZED"
    assert r["execution_allowed"] is False
    assert r["phase7_acceptance_allowed"] is False
    assert r["child_reports"]
    assert r["child_reports"]["usage_policy_readiness"]["blocker_count"] >= 0
    assert r["child_reports"]["usage_accounting_contract"]["blocker_count"] >= 0
    assert r["child_reports"]["policy_reject_accounting_contract"]["blocker_count"] >= 0
    assert r["phase8_start_allowed"] is False
    assert isinstance(r["blockers"], list)
