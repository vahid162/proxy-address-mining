from mpf.config import load_config
from mpf.services.firewall_no_customer_apply_execution_acceptance_service import build_no_customer_apply_execution_acceptance_report
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")

def _cfg(): return load_config(example_config_path())

def test_execution_acceptance_default_report():
    r=build_no_customer_apply_execution_acceptance_report(_cfg())
    assert r['component']=='firewall_no_customer_apply_execution_acceptance'
    assert r['final_decision']=='BLOCKED'
    assert r['authorization_status']=='EXECUTION_ACCEPTANCE_DEFINED_NOT_EXECUTABLE'
    assert r['execution_allowed'] is False
    assert r['apply_decision']==r['verify_decision']==r['rollback_decision']=='BLOCKED'

def test_cli_human_json():
    from typer.testing import CliRunner
    from mpf.interfaces.cli import app
    c=example_config_path(); runner=CliRunner()
    h=runner.invoke(app,['firewall','no-customer-apply-execution-acceptance','--config',str(c)])
    j=runner.invoke(app,['firewall','no-customer-apply-execution-acceptance','--config',str(c),'--output','json'])
    assert 'EXECUTION_ACCEPTANCE_DEFINED_NOT_EXECUTABLE' in h.output
    assert '"execution_allowed": false' in j.output
