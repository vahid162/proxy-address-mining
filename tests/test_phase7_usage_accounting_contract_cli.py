import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app


r = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase7_usage_accounting_contract_cli_human_and_json() -> None:
    human = r.invoke(app, ["phase7", "usage-accounting-contract", "--config", str(example_config_path())])
    assert human.exit_code == 0
    assert "final_decision: BLOCKED" in human.stdout

    js = r.invoke(app, ["phase7", "usage-accounting-contract", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    data = json.loads(js.stdout)
    assert data["final_decision"] == "BLOCKED"
    assert data["execution_allowed"] is False
    assert data["usage_collector_runtime_authorized"] is False
    assert data["usage_db_writes_authorized"] is False
    assert data["firewall_counter_live_read_authorized"] is False
    assert data["blockers"] == []
