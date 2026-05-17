from __future__ import annotations
import json
from pathlib import Path
from typer.testing import CliRunner
from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase8_controlled_worker_dry_run_service import build_phase8_controlled_worker_dry_run_report

EXPECTED_VERSION = "0.1.129"


def cfg_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase_status_0_1_119_evidence_present() -> None:
    phase = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    for token in ["Phase 8 farm5 0.1.119 Controlled Worker Gate Sync Evidence","server version after sync: 0.1.119","synced to 0.1.119","pytest: 741 passed in 85.21s","/var/backups/mpf/source-before-zip-sync-20260516T130517Z","production_traffic: none","firewall_apply_allowed: no","abuse_automation_allowed: no","no MPF/customer IPv4 firewall references detected","no MPF/customer IPv6 firewall references detected","This evidence does not accept Phase 8.","It does not authorize background worker start.","It does not authorize scheduler/timer.","It does not authorize abuse runner.","It does not authorize production DB execution.","It does not authorize firewall apply.","It does not authorize hard/soft blocks.","It does not authorize pause automation.","It does not authorize UI or Telegram.","It does not authorize production traffic."]:
        assert token in phase


def test_service_and_cli() -> None:
    r = build_phase8_controlled_worker_dry_run_report(load_config(cfg_path()))
    assert r["component"] == "phase8_controlled_worker_dry_run"
    assert r["final_decision"] in {"BLOCKED", "DRY_RUN_ONLY"}
    assert r["execution_allowed"] is False and r["production_side_effects_allowed"] is False and r["phase8_acceptance_allowed"] is False
    assert r["repository_version"] == EXPECTED_VERSION
    assert r["latest_recorded_farm5_sync_evidence"] == "0.1.121"
    assert r["farm5_0_1_121_sync_evidence_present"] is True
    assert r["farm5_0_1_122_sync_required_before_future_server_evidence"] is True
    assert r["controlled_worker_dry_run_gate_doc_present"] is True
    assert r["synthetic_item_count"] >= 10 and r["synthetic_scenarios_passed"] is True and r["all_items_have_no_side_effects"] is True
    for k, v in r.items():
        if k.endswith("_authorized"):
            assert v is False
    assert any("operator_confirmation_required" in b for b in r["blockers"])

    runner = CliRunner()
    out = runner.invoke(app, ["phase8", "controlled-worker-dry-run", "--config", str(cfg_path()), "--output", "json"])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data["execution_allowed"] is False
    assert data["production_side_effects_allowed"] is False
    assert data["phase8_acceptance_allowed"] is False
    assert data["farm5_0_1_121_sync_evidence_present"] is True
    assert data["farm5_0_1_122_sync_required_before_future_server_evidence"] is True
    assert data["worker_start_authorized"] is False and data["scheduler_authorized"] is False and data["production_db_execution_authorized"] is False and data["firewall_apply_authorized"] is False and data["production_traffic_authorized"] is False
    assert any("operator_confirmation_required" in b for b in data["blockers"])

    out2 = runner.invoke(app, ["phase8", "controlled-worker-dry-run", "--config", str(cfg_path()), "--operator-confirmed", "--output", "json"])
    assert out2.exit_code == 0
    data2 = json.loads(out2.stdout)
    assert data2["execution_allowed"] is False and data2["production_side_effects_allowed"] is False
    assert not any("operator_confirmation_required" in b for b in data2["blockers"])


def test_static_safety() -> None:
    text = (Path("mpf/domain/controlled_worker_dry_run.py").read_text()+Path("mpf/services/phase8_controlled_worker_dry_run_service.py").read_text()).lower()
    for token in ["subprocess.run", "subprocess.popen", "os.system", "psycopg.connect", "create_engine", "session.add", "session.commit", "write_text"]:
        assert token not in text
