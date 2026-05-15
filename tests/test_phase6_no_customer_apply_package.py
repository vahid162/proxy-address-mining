from pathlib import Path
from mpf.config import load_config
from mpf.services.firewall_no_customer_apply_package_service import build_no_customer_apply_package_report
from mpf.__init__ import __version__
import tomllib
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def _cfg(): return load_config(example_config_path())

def test_version_consistency():
    assert Path('VERSION').read_text().strip()=='0.1.109'
    assert tomllib.loads(Path('pyproject.toml').read_text())['project']['version']=='0.1.109'
    assert __version__=='0.1.109'
    r=CliRunner().invoke(app,['--version'])
    assert '0.1.109' in r.output

def test_package_default_report():
    r=build_no_customer_apply_package_report(_cfg())
    assert r['component']=='firewall_no_customer_apply_package'
    assert r['final_decision']=='BLOCKED'
    assert r['authorization_status']=='PACKAGE_DEFINED_NOT_EXECUTABLE'
    assert r['execution_allowed'] is False
    assert r['apply_decision']==r['verify_decision']==r['rollback_decision']=='BLOCKED'
    assert all(i['executable'] is False and i['executed'] is False for i in r['modeled_sequence'])
