import json
from typer.testing import CliRunner

from mpf.interfaces.cli import app
from pathlib import Path


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")



def test_phase7_summary_and_doctor_cli() -> None:
    r = CliRunner()
    human = r.invoke(app, ["phase7", "summary", "--config", str(example_config_path())])
    assert human.exit_code == 0
    js = r.invoke(app, ["phase7", "summary", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    summary = json.loads(js.output)
    assert summary["final_decision"] == "BLOCKED"
    assert summary["execution_allowed"] is False

    human2 = r.invoke(app, ["phase7", "doctor", "--config", str(example_config_path())])
    assert human2.exit_code == 0
    js2 = r.invoke(app, ["phase7", "doctor", "--config", str(example_config_path()), "--output", "json"])
    assert js2.exit_code == 0
    doctor = json.loads(js2.output)
    assert doctor["final_verdict"] in {"OK", "BLOCKED"}
    assert doctor["final_decision"] == "BLOCKED"
    assert doctor["phase8_start_allowed"] is False
    assert isinstance(doctor["blockers"], list)
