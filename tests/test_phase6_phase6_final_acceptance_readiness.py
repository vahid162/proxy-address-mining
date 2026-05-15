from mpf.config import load_config
from mpf.services.phase6_final_acceptance_readiness_service import build_phase6_final_acceptance_readiness_report
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")

def test_phase6_final_acceptance_defaults_blocked():
    r=build_phase6_final_acceptance_readiness_report(load_config(example_config_path()))
    assert r['component']=='phase6_final_acceptance_readiness'
    assert r['final_decision']=='BLOCKED'
    assert r['acceptance_status']=='PHASE6_NOT_ACCEPTED'
    assert r['phase6_acceptance_allowed'] is False
    assert r['execution_allowed'] is False
