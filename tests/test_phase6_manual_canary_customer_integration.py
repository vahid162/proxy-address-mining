from pathlib import Path
from mpf.config import load_config
from mpf.services.firewall_apply_gate_readiness_service import build_apply_gate_readiness_report

def _cfg():
    return load_config(Path(__file__).resolve().parent.parent / 'configs' / 'mpf.example.yaml')

def test_apply_gate_has_manual_canary_summaries():
    report = build_apply_gate_readiness_report(_cfg())
    assert 'manual_canary_customer_proposal_summary' in report
    assert 'manual_canary_customer_acceptance_readiness_summary' in report
