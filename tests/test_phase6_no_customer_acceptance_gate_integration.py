from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_cli_human_and_integrations():
    res = RUNNER.invoke(app, ["firewall", "no-customer-apply-acceptance-gate", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "component: firewall_no_customer_apply_acceptance_gate" in res.output
    assert "authorization_status: ACCEPTANCE_GATE_DEFINED_NOT_EXECUTABLE" in res.output
    agr = RUNNER.invoke(app, ["firewall", "apply-gate-readiness", "--config", str(example_config_path()), "--output", "json"])
    assert '"no_customer_apply_acceptance_gate_summary"' in agr.output
    assert '"final_decision": "BLOCKED"' in agr.output
    gr = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--source", "config-only"])
    assert "no_customer_apply_acceptance_gate: summary" in gr.output
    assert "authorization_status: ACCEPTANCE_GATE_DEFINED_NOT_EXECUTABLE" in gr.output
