from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import operator_execution_context_service, phase11_canary_usage_evidence_capture_service


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def test_operator_context_local_peer_root_read_ok(monkeypatch):
    monkeypatch.setattr("getpass.getuser", lambda: "root")
    r = operator_execution_context_service.build_operator_execution_context_report(_cfg(), mode="read")
    assert r["final_decision"] == "OK_FOR_READ"


def test_operator_context_local_peer_root_db_write_blocked(monkeypatch):
    monkeypatch.setattr("getpass.getuser", lambda: "root")
    r = operator_execution_context_service.build_operator_execution_context_report(_cfg(), mode="db-write")
    assert r["final_decision"] == "BLOCKED"
    assert "db_write_requires_mpf_os_user" in r["blockers"]


def test_usage_capture_cli_smoke():
    res = CliRunner().invoke(app, ["production", "canary-usage-evidence-capture", "--output", "json", "--config", "configs/mpf.example.yaml", "--no-collect-live"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_usage_evidence_capture"' in res.output
