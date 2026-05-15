import json
from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import firewall_no_customer_runtime_execution_approval_service
from pathlib import Path

def example_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs" / "mpf.example.yaml"


def test_runtime_execution_approval_defaults_blocked():
    from mpf.config import load_config
    report = firewall_no_customer_runtime_execution_approval_service.build_no_customer_runtime_execution_approval_report(load_config(example_config_path()))
    assert report['component'] == 'firewall_no_customer_runtime_execution_approval'
    assert report['final_decision'] == 'BLOCKED'
    assert report['authorization_status'] == 'RUNTIME_EXECUTION_APPROVAL_READY_BUT_NOT_GRANTED'
    assert report['execution_allowed'] is False
    assert report['apply_decision'] == 'BLOCKED'


def test_runtime_execution_approval_cli_json():
    r = CliRunner().invoke(app,['firewall','no-customer-runtime-execution-approval','--config',str(example_config_path()),'--output','json'])
    assert r.exit_code == 0
    data = json.loads(r.stdout)
    assert data['final_decision'] == 'BLOCKED'
    assert data['execution_allowed'] is False
