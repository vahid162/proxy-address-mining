import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from mpf.services import phase11_limited_acceptance_decision_gate_service as service

runner = CliRunner()

def test_cli_calls_service_and_writes_json(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr("mpf.interfaces.cli._load", lambda *_: object())
    monkeypatch.setattr(service, "build_phase11_limited_acceptance_decision_gate_report", lambda *a, **k: seen.setdefault("report", {"final_decision": "BLOCKED"}))
    args = ["production", "phase11-limited-acceptance-decision-gate", "--expected-version", "x"]
    for name in ("observation-window", "final-readiness-planning", "artifact-gate"):
        args += [f"--{name}-json", "x", f"--{name}-json-sha256", "x"]
    out = tmp_path / "out.json"
    args += ["--operator", "o", "--reason", "r", "--out-json", str(out), "--output", "json"]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.stdout
    assert json.loads(out.read_text())["final_decision"] == "BLOCKED"
    assert seen
