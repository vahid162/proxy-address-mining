import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")

r = CliRunner()

def test_phase7_cli_human_and_json() -> None:
    res = r.invoke(app,["phase7","usage-policy-readiness","--config",str(example_config_path())])
    assert res.exit_code == 0
    assert "final_decision: BLOCKED" in res.stdout
    res = r.invoke(app,["phase7","usage-policy-readiness","--config",str(example_config_path()),"--output","json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["ai_phase7_task_present"] is True
    assert data["blockers"] == []
    assert data["final_decision"] == "BLOCKED"
    assert data["execution_allowed"] is False
