from mpf.config import load_config
from mpf.services.firewall_manual_canary_customer_server_evidence_service import build_manual_canary_customer_server_evidence_report
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")

def test_manual_canary_server_evidence_defaults_blocked():
    r=build_manual_canary_customer_server_evidence_report(load_config(example_config_path()))
    assert r['component']=='firewall_manual_canary_customer_server_evidence'
    assert r['final_decision']=='BLOCKED'
    assert r['authorization_status']=='MANUAL_CANARY_SERVER_EVIDENCE_NOT_ACCEPTED'
    assert r['execution_allowed'] is False
    assert r['customer_nat_authorized'] is False
