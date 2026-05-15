from mpf.config import load_config
from mpf.services.phase6_final_acceptance_review_service import build_phase6_final_acceptance_review_report
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase6_final_acceptance_review_defaults_blocked():
    r = build_phase6_final_acceptance_review_report(load_config(example_config_path()))
    assert r['component'] == 'phase6_final_acceptance_review'
    assert r['final_decision'] == 'BLOCKED'
    assert r['review_status'] == 'READY_FOR_OPERATOR_REVIEW_BUT_NOT_ACCEPTED'
    assert r['acceptance_status'] == 'PHASE6_NOT_ACCEPTED'
    assert r['execution_allowed'] is False
    assert r['phase6_acceptance_allowed'] is False
    assert r['customer_nat_authorized'] is False
    assert r['customer_firewall_rules_authorized'] is False
    assert r['production_traffic_authorized'] is False
