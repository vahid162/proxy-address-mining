import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from tests.test_smoke import example_config_path


def test_phase6_operator_acceptance_final_integration() -> None:
    runner = CliRunner()
    h = runner.invoke(app, ["phase6", "operator-acceptance-decision", "--config", str(example_config_path())])
    assert h.exit_code == 0
    j = runner.invoke(app, ["phase6", "operator-acceptance-decision", "--config", str(example_config_path()), "--output", "json"])
    d = json.loads(j.stdout)
    assert d["final_decision"] == "ACCEPTED"
    agr = json.loads(runner.invoke(app, ["firewall", "apply-gate-readiness", "--config", str(example_config_path()), "--output", "json"]).stdout)
    s = agr["phase6_operator_acceptance_decision_summary"]
    assert s["phase6_operator_acceptance_decision_final_decision"] == "ACCEPTED"
    assert s["phase6_operator_acceptance_decision_phase6_accepted"] is True
    grj = json.loads(runner.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--source", "config-only", "--output", "json"]).stdout)
    assert grj["live_apply_allowed"] is False
    assert grj["apply_gate_readiness_summary"]["phase6_operator_acceptance_decision_summary"]["phase6_operator_acceptance_decision_phase7_start_allowed"] is True
