from pathlib import Path
from mpf.config import load_config
from mpf.services.firewall_apply_gate_readiness_service import build_apply_gate_readiness_report
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")
from typer.testing import CliRunner
from mpf.interfaces.cli import app

def test_apply_gate_has_new_summaries():
    r=build_apply_gate_readiness_report(load_config(example_config_path()))
    assert 'no_customer_apply_package_summary' in r
    assert 'no_customer_apply_execution_acceptance_summary' in r
    assert r['final_decision']=='BLOCKED'

def test_gate_review_human_has_new_summaries():
    res=CliRunner().invoke(app,['firewall','gate-review','--config',str(example_config_path()),'--source','config-only'])
    assert 'no_customer_apply_package: summary' in res.output
    assert 'no_customer_apply_execution_acceptance: summary' in res.output

def test_static_safety_patterns_absent():
    for p in ['mpf/services/firewall_no_customer_apply_package_service.py','mpf/services/firewall_no_customer_apply_execution_acceptance_service.py']:
        t=Path(p).read_text().lower()
        for bad in ['subprocess.run','os.system','open(..., "w")','write_text','psycopg.connect','insert into','update','delete from','alembic','migration']:
            assert bad not in t
