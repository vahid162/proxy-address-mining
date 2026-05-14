from pathlib import Path
import json
from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.firewall_apply_gate_readiness_service import build_apply_gate_readiness_report


def example_config_path() -> Path:
    return Path('configs/mpf.example.yaml')


def test_cli_execution_gate_human_and_json():
    runner = CliRunner()
    res = runner.invoke(app, ["firewall", "no-customer-apply-execution-gate", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "component: firewall_no_customer_apply_execution_gate" in res.stdout
    js = runner.invoke(app, ["firewall", "no-customer-apply-execution-gate", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    data = json.loads(js.stdout)
    assert data["execution_allowed"] is False


def test_apply_gate_readiness_includes_execution_gate_summary():
    cfg = load_config(example_config_path())
    report = build_apply_gate_readiness_report(cfg)
    assert report["final_decision"] == "BLOCKED"
    assert "no_customer_apply_execution_gate_summary" in report
