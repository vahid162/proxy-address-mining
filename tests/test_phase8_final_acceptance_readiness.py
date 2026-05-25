from pathlib import Path
from typer.testing import CliRunner
from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase8_final_acceptance_readiness_service import build_phase8_final_acceptance_readiness_report

EXPECTED_VERSION = "0.1.215"


def cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def test_service_report():
    r = build_phase8_final_acceptance_readiness_report(cfg())
    assert r["component"] == "phase8_final_acceptance_readiness"
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False
    assert r["phase8_acceptance_allowed"] is False
    assert r["phase8_accepted_by_this_pr"] is False
    assert r["repository_version"] == EXPECTED_VERSION
    assert r["latest_recorded_farm5_sync_evidence"] == "0.1.121"
    assert r["farm5_0_1_121_sync_evidence_present"] is True
    assert r["farm5_controlled_worker_dry_run_evidence_present"] is True
    assert r["blockers"] == []


def test_cli_json():
    out = CliRunner().invoke(app, ["phase8", "final-acceptance-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"])
    assert out.exit_code == 0
    assert '"final_decision": "BLOCKED"' in out.stdout
