from pathlib import Path
from mpf.config import load_config
from mpf.services.firewall_manual_canary_customer_proposal_service import build_manual_canary_customer_proposal_report

def _cfg():
    return load_config(Path(__file__).resolve().parent.parent / 'configs' / 'mpf.example.yaml')

def test_manual_canary_proposal_defaults_blocked():
    report = build_manual_canary_customer_proposal_report(_cfg())
    assert report['component'] == 'firewall_manual_canary_customer_proposal'
    assert report['final_decision'] == 'BLOCKED'
