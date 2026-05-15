import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase8_planning_readiness_service import build_phase8_planning_readiness_report


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase8_service_defaults() -> None:
    report = build_phase8_planning_readiness_report(load_config(example_config_path()))
    assert report["component"] == "phase8_planning_readiness"
    assert report["phase"] == "Phase 8 — Abuse 1h Core"
    assert report["final_decision"] == "BLOCKED"
    assert report["readiness_status"] == "PHASE8_PLANNING_READINESS_DEFINED_NOT_ACCEPTED"
    assert report["authorization_status"] == "PHASE8_PLANNING_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED"
    assert report["execution_allowed"] is False
    assert report["phase8_acceptance_allowed"] is False
    assert report["abuse_automation_authorized"] is False
    assert report["abuse_runner_authorized"] is False
    assert report["hard_block_authorized"] is False
    assert report["blockers"] == []


def test_phase8_cli_human_and_json() -> None:
    r = CliRunner()
    human = r.invoke(app, ["phase8", "planning-readiness", "--config", str(example_config_path())])
    assert human.exit_code == 0
    js = r.invoke(app, ["phase8", "planning-readiness", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    data = json.loads(js.stdout)
    assert data["final_decision"] == "BLOCKED"
    assert data["execution_allowed"] is False
    assert data["phase8_acceptance_allowed"] is False
    assert data["abuse_automation_authorized"] is False
    assert data["abuse_runner_authorized"] is False
    assert data["hard_block_authorized"] is False
    assert isinstance(data["blockers"], list)


def test_phase8_service_static_safety() -> None:
    text = Path("mpf/services/phase8_planning_readiness_service.py").read_text(encoding="utf-8").lower()
    banned = ["subprocess.run","subprocess.popen","os.system","conntrack","docker","systemctl","write_text","psycopg.connect","insert into","update","delete from","alembic","migration","create_engine","session.add","session.commit"]
    for b in banned:
        assert b not in text
