from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase8_controlled_worker_dry_run_service import build_phase8_controlled_worker_dry_run_report


EXPECTED_VERSION = "0.1.142"


def cfg_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase_status_0_1_119_evidence_present() -> None:
    phase = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "Phase 8 farm5 0.1.119 Controlled Worker Gate Sync Evidence" in phase
    assert "synced to 0.1.119" in phase
    assert "production_traffic: none" in phase
    assert "firewall_apply_allowed: no" in phase
    assert "abuse_automation_allowed: no" in phase


def test_service_and_cli() -> None:
    r = build_phase8_controlled_worker_dry_run_report(load_config(cfg_path()))
    assert r["component"] == "phase8_controlled_worker_dry_run"
    assert r["final_decision"] in {"BLOCKED", "DRY_RUN_ONLY"}
    assert r["execution_allowed"] is False
    assert r["production_side_effects_allowed"] is False
    assert r["phase8_acceptance_allowed"] is False
    assert r["repository_version"] == EXPECTED_VERSION
    assert r["latest_recorded_farm5_sync_evidence"] == "0.1.121"
    assert r["farm5_0_1_121_sync_evidence_present"] is True
    assert r["controlled_worker_dry_run_gate_doc_present"] is True
    assert r["synthetic_scenarios_passed"] is True

    out = CliRunner().invoke(app, ["phase8", "controlled-worker-dry-run", "--config", str(cfg_path()), "--output", "json"])
    assert out.exit_code == 0
    assert "phase8_controlled_worker_dry_run" in out.stdout
