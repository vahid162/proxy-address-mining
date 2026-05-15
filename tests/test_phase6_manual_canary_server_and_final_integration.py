import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")

def test_apply_gate_includes_new_summaries_and_gate_review_blocked():
    r=CliRunner().invoke(app,['firewall','apply-gate-readiness','--config',str(example_config_path()),'--output','json'])
    assert r.exit_code==0
    d=json.loads(r.stdout)
    assert 'manual_canary_customer_server_evidence_summary' in d
    assert 'phase6_final_acceptance_readiness_summary' in d
    g=CliRunner().invoke(app,['firewall','gate-review','--config',str(example_config_path()),'--source','config-only','--output','json'])
    gd=json.loads(g.stdout)
    assert gd['final_decision']=='BLOCKED'
    assert gd['applyable'] is False
    assert gd['live_apply_allowed'] is False
