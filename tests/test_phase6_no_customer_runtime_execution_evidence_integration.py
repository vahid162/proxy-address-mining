import json
from pathlib import Path
from typer.testing import CliRunner

from mpf.interfaces.cli import app


def example_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs" / "mpf.example.yaml"


def test_apply_gate_and_gate_review_include_evidence_summary():
    runner = CliRunner()
    agr = runner.invoke(app, ["firewall", "apply-gate-readiness", "--config", str(example_config_path()), "--output", "json"])
    data = json.loads(agr.stdout)
    s = data["no_customer_runtime_execution_evidence_summary"]
    assert s["no_customer_runtime_execution_evidence_present"] is True
    assert s["no_customer_runtime_execution_evidence_final_decision"] == "BLOCKED"

    human = runner.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--source", "config-only"])
    assert "no_customer_runtime_execution_evidence: summary" in human.stdout
    j = runner.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--source", "config-only", "--output", "json"])
    g = json.loads(j.stdout)
    assert g["final_decision"] == "BLOCKED"
    assert g["applyable"] is False
    assert g["live_apply_allowed"] is False
    assert "no_customer_runtime_execution_evidence_summary" in g["apply_gate_readiness_summary"]
