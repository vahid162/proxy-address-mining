import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase6_final_acceptance_review_cli_json():
    r = CliRunner().invoke(app,['phase6','final-acceptance-review','--config',str(example_config_path()),'--output','json'])
    assert r.exit_code == 0
    d = json.loads(r.stdout)
    assert d['final_decision'] == 'BLOCKED'


def test_apply_gate_readiness_and_gate_review_include_phase6_final_acceptance_review_summary():
    agr = CliRunner().invoke(app,['firewall','apply-gate-readiness','--config',str(example_config_path()),'--output','json'])
    assert agr.exit_code == 0
    ad = json.loads(agr.stdout)
    assert 'phase6_final_acceptance_review_summary' in ad
    gr = CliRunner().invoke(app,['firewall','gate-review','--config',str(example_config_path()),'--source','config-only','--output','json'])
    assert gr.exit_code == 0
    gd = json.loads(gr.stdout)
    assert 'phase6_final_acceptance_review_summary' in gd['apply_gate_readiness_summary']
