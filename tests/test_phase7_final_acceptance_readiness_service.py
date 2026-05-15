from pathlib import Path

from mpf.config import load_config
from mpf.services.phase7_final_acceptance_readiness_service import build_phase7_final_acceptance_readiness_report
from mpf.services.phase7_operator_acceptance_decision_service import build_phase7_operator_acceptance_decision_report


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase7_final_acceptance_readiness_service_defaults() -> None:
    r = build_phase7_final_acceptance_readiness_report(load_config(example_config_path()))
    assert r["component"] == "phase7_final_acceptance_readiness"
    assert r["final_decision"] == "BLOCKED"
    assert r["readiness_status"] == "PHASE7_FINAL_ACCEPTANCE_READY_FOR_OPERATOR_REVIEW"
    assert r["authorization_status"] == "PHASE7_FINAL_ACCEPTANCE_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED"
    assert r["execution_allowed"] is False
    assert r["phase7_acceptance_allowed"] is False
    assert r["phase8_start_allowed"] is False
    assert r["farm5_sync_version"] == "0.1.107"
    assert r["farm5_0_1_107_sync_evidence_present"] is True
    assert isinstance(r["phase7_usage_policy_readiness_clean"], bool)
    assert isinstance(r["phase7_usage_accounting_contract_clean"], bool)
    assert isinstance(r["phase7_policy_reject_accounting_contract_clean"], bool)
    assert isinstance(r["phase7_reports_summary_clean"], bool)
    assert isinstance(r["phase7_doctor_ok"], bool)
    assert isinstance(r["phase7_contract_stack_complete"], bool)
    assert isinstance(r["blockers"], list)


def test_phase7_operator_acceptance_decision_service_defaults() -> None:
    r = build_phase7_operator_acceptance_decision_report(load_config(example_config_path()))
    assert r["component"] == "phase7_operator_acceptance_decision"
    assert r["operator_decision"] == "READY_FOR_OPERATOR_ACCEPTANCE"
    assert r["final_decision"] == "BLOCKED"
    assert r["acceptance_scope"] == "report_only_service_contract_readiness"
    assert r["recommended_next_phase_after_operator_acceptance"] == "Phase 8 — Abuse 1h Core planning/readiness"
    assert r["execution_allowed"] is False
    assert r["phase7_acceptance_allowed"] is False
    assert r["phase8_start_allowed"] is False
    assert r["separate_phase_gate_update_pr_required"] is True
    assert isinstance(r["blockers"], list)
