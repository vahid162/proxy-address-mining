from pathlib import Path

from mpf.config import load_config
from mpf.services.firewall_no_customer_apply_execution_gate_service import build_no_customer_apply_execution_gate_report


def example_config_path() -> Path:
    return Path('configs/mpf.example.yaml')


def test_execution_gate_default_report():
    cfg = load_config(example_config_path())
    r = build_no_customer_apply_execution_gate_report(cfg)
    assert r["component"] == "firewall_no_customer_apply_execution_gate"
    assert r["final_decision"] == "BLOCKED"
    assert r["authorization_status"] == "NOT_ACCEPTED_FOR_EXECUTION"
    assert r["execution_allowed"] is False
    assert r["apply_decision"] == "BLOCKED"
    assert r["verify_decision"] == "BLOCKED"
    assert r["rollback_decision"] == "BLOCKED"
    assert all(i["status"] in {"PASS", "BLOCKED"} for i in r["execution_readiness_checklist"])
