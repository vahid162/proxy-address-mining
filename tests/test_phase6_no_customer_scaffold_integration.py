from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_gate_review_includes_no_customer_scaffold_summary() -> None:
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "no_customer_apply_scaffold: summary" in res.output
    assert "present: true" in res.output
    assert "final_decision: BLOCKED" in res.output
    assert "authorization_status: NOT_AUTHORIZED_FOR_APPLY" in res.output
    assert "execution_allowed: false" in res.output


def test_apply_gate_readiness_includes_no_customer_scaffold_summary() -> None:
    res = RUNNER.invoke(app, ["firewall", "apply-gate-readiness", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"no_customer_apply_scaffold_summary"' in res.output
    assert '"no_customer_apply_scaffold_final_decision": "BLOCKED"' in res.output
