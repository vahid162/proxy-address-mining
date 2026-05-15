import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase7_final_acceptance_and_operator_cli() -> None:
    r = CliRunner()
    human = r.invoke(app, ["phase7", "final-acceptance-readiness", "--config", str(example_config_path())])
    assert human.exit_code == 0
    js = r.invoke(app, ["phase7", "final-acceptance-readiness", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    data = json.loads(js.stdout)
    assert data["final_decision"] == "BLOCKED"
    assert data["phase7_acceptance_allowed"] is False
    assert data["phase8_start_allowed"] is False
    assert isinstance(data["blockers"], list)

    human2 = r.invoke(app, ["phase7", "operator-acceptance-decision", "--config", str(example_config_path())])
    assert human2.exit_code == 0
    js2 = r.invoke(app, ["phase7", "operator-acceptance-decision", "--config", str(example_config_path()), "--output", "json"])
    assert js2.exit_code == 0
    data2 = json.loads(js2.stdout)
    assert data2["operator_decision"] == "READY_FOR_OPERATOR_ACCEPTANCE"
    assert data2["final_decision"] == "BLOCKED"
    assert data2["separate_phase_gate_update_pr_required"] is True
    assert isinstance(data2["blockers"], list)
