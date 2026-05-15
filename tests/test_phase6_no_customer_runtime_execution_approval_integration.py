import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from pathlib import Path

def example_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs" / "mpf.example.yaml"


def test_apply_gate_readiness_includes_runtime_summary():
    r = CliRunner().invoke(app,['firewall','apply-gate-readiness','--config',str(example_config_path()),'--output','json'])
    data = json.loads(r.stdout)
    s = data['no_customer_runtime_execution_approval_summary']
    assert s['no_customer_runtime_execution_approval_present'] is True
    assert s['no_customer_runtime_execution_approval_final_decision'] == 'BLOCKED'


def test_gate_review_includes_runtime_summary_and_stays_blocked():
    h = CliRunner().invoke(app,['firewall','gate-review','--config',str(example_config_path()),'--source','config-only'])
    assert 'no_customer_runtime_execution_approval: summary' in h.stdout
    j = CliRunner().invoke(app,['firewall','gate-review','--config',str(example_config_path()),'--source','config-only','--output','json'])
    data = json.loads(j.stdout)
    assert 'apply_gate_readiness_summary' in data
    agr = data['apply_gate_readiness_summary']
    assert 'no_customer_runtime_execution_approval_summary' in agr
    s = agr['no_customer_runtime_execution_approval_summary']
    assert s['no_customer_runtime_execution_approval_present'] is True
    assert s['no_customer_runtime_execution_approval_final_decision'] == 'BLOCKED'
    assert s['no_customer_runtime_execution_approval_execution_allowed'] is False
    assert s['no_customer_runtime_execution_approval_operator_approval_required'] is True
    assert data['final_decision'] == 'BLOCKED'
    assert data['applyable'] is False
    assert data['live_apply_allowed'] is False
