from pathlib import Path

from mpf.config import load_config
from mpf.services.phase7_policy_reject_accounting_contract_service import (
    build_phase7_policy_reject_accounting_contract_report,
)


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_policy_reject_contract_service_defaults() -> None:
    report = build_phase7_policy_reject_accounting_contract_report(load_config(example_config_path()))
    assert report["component"] == "phase7_policy_reject_accounting_contract"
    assert report["final_decision"] == "BLOCKED"
    assert report["contract_status"] == "POLICY_REJECT_ACCOUNTING_CONTRACT_DEFINED_NOT_ACCEPTED"
    assert report["authorization_status"] == "PHASE7_POLICY_REJECT_ACCOUNTING_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED"
    assert report["execution_allowed"] is False
    assert report["phase7_acceptance_allowed"] is False
    assert report["policy_reject_accounting_contract_defined"] is True
    assert report["policy_events_contract_defined"] is True
    assert report["reject_categories_defined"] is True
    assert report["reject_explainability_contract_defined"] is True
    assert report["reject_report_windows_defined"] is True
    assert report["policy_reject_doctor_contract_defined"] is True
    assert report["policy_reject_collector_runtime_authorized"] is False
    assert report["policy_reject_timer_authorized"] is False
    assert report["policy_reject_db_writes_authorized"] is False
    assert report["policy_reject_live_counter_read_authorized"] is False
    assert report["firewall_counter_live_read_authorized"] is False
    assert report["production_traffic_authorized"] is False
    assert report["abuse_automation_authorized"] is False
    assert report["phase8_start_allowed"] is False


def test_policy_reject_contract_content() -> None:
    report = build_phase7_policy_reject_accounting_contract_report(load_config(example_config_path()))
    contract = report["policy_reject_contract"]
    assert "policy_events" in contract["data_model_tables"]
    assert "usage_samples" in contract["data_model_tables"]
    for item in ["connlimit_reject", "hashlimit_reject", "pause_reject", "block_reject"]:
        assert item in contract["reject_categories"]
    for item in ["customer_id", "lane_id", "port", "event_type", "counter_delta", "evidence_json", "seen_at"]:
        assert item in contract["required_event_fields"]
    assert any("not silent skip" in item for item in contract["required_explainability"])
    assert any("farms-over alone must not harden" in item for item in contract["required_explainability"])
    assert any("worker-over alone must not harden" in item for item in contract["required_explainability"])
    assert "no abuse automation before Phase 8" in contract["required_future_acceptance_criteria"]
