from pathlib import Path

from mpf.config import load_config
from mpf.services.phase7_usage_accounting_contract_service import (
    build_phase7_usage_accounting_contract_report,
)


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase7_usage_accounting_contract_defaults() -> None:
    r = build_phase7_usage_accounting_contract_report(load_config(example_config_path()))
    assert r["component"] == "phase7_usage_accounting_contract"
    assert r["final_decision"] == "BLOCKED"
    assert r["contract_status"] == "USAGE_ACCOUNTING_CONTRACT_DEFINED_NOT_ACCEPTED"
    assert r["authorization_status"] == "PHASE7_USAGE_ACCOUNTING_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED"
    assert r["execution_allowed"] is False
    assert r["phase7_acceptance_allowed"] is False
    assert r["usage_accounting_contract_defined"] is True
    assert r["usage_samples_contract_defined"] is True
    assert r["usage_delta_contract_defined"] is True
    assert r["usage_report_windows_defined"] is True
    assert r["usage_doctor_contract_defined"] is True
    assert r["usage_collector_runtime_authorized"] is False
    assert r["usage_timer_authorized"] is False
    assert r["usage_db_writes_authorized"] is False
    assert r["usage_counter_live_read_authorized"] is False
    assert r["firewall_counter_live_read_authorized"] is False
    assert r["production_traffic_authorized"] is False
    assert r["abuse_automation_authorized"] is False
    assert r["phase8_start_allowed"] is False


def test_phase7_usage_accounting_contract_content() -> None:
    r = build_phase7_usage_accounting_contract_report(load_config(example_config_path()))
    usage_contract = r["usage_contract"]
    assert "usage_samples" in usage_contract["data_model_tables"]
    assert "policy_events" in usage_contract["data_model_tables"]
    assert usage_contract["report_windows"] == ["1h", "1d", "30d"]
    for fld in ("connlimit_rejects", "hashlimit_rejects", "pause_rejects", "block_rejects"):
        assert fld in usage_contract["counter_fields"]
    crit = usage_contract["required_future_acceptance_criteria"]
    assert "no silent skip" in crit
    assert "no abuse automation before Phase 8" in crit
