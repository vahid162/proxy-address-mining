from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase8_controlled_worker_dry_run_gate_service import build_phase8_controlled_worker_dry_run_gate_report


def cfg_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_docs_and_gate_doc_present() -> None:
    phase = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "Phase 8 farm5 0.1.118 Batched Sync Evidence" in phase
    assert "server version after sync: 0.1.118" in phase
    assert "synced to 0.1.118" in phase
    assert "pytest: 738 passed in 73.43s" in phase
    assert "/var/backups/mpf/source-before-zip-sync-20260516T121320Z" in phase
    assert "production_traffic: none" in phase and "firewall_apply_allowed: no" in phase and "abuse_automation_allowed: no" in phase
    assert "no MPF/customer IPv4 firewall references detected" in phase and "no MPF/customer IPv6 firewall references detected" in phase
    assert "0.1.116" in phase and "0.1.117" in phase and "0.1.118" in phase
    assert "This evidence does not accept Phase 8." in phase
    gate = Path("docs/PHASE_8_CONTROLLED_WORKER_DRY_RUN_GATE.md").read_text(encoding="utf-8")
    assert "## Non-Authorization" in gate and "## Required Before Controlled Worker Dry-Run" in gate and "## Future Acceptance Criteria" in gate


def test_remaining_phase_plan_current_target() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "latest recorded farm5 sync evidence is 0.1.118" in text
    assert "version before this PR is 0.1.118" in text and "version after this PR is 0.1.119" in text
    assert "Current target is Phase 8 controlled worker dry-run gate preparation package." in text
    assert "only after this PR is merged and 0.1.119 is synced/tested on farm5" in text


def test_service_and_cli_and_static_safety() -> None:
    r = build_phase8_controlled_worker_dry_run_gate_report(load_config(cfg_path()))
    assert r["component"] == "phase8_controlled_worker_dry_run_gate"
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False and r["phase8_acceptance_allowed"] is False
    assert r["repository_version"] == "0.1.119"
    assert r["latest_recorded_farm5_sync_evidence"] == "0.1.118"
    assert r["farm5_0_1_118_batch_sync_evidence_present"] is True
    assert r["farm5_0_1_119_sync_required_before_controlled_worker_dry_run"] is True
    assert r["controlled_worker_dry_run_gate_doc_present"] is True and r["controlled_worker_dry_run_gate_prepared"] is True
    for k, v in r.items():
        if k.endswith("_authorized"):
            assert v is False
    assert r["blockers"] == []
    assert any(i["item"] == "current_state_preserved" for i in r["phase8_controlled_worker_dry_run_gate_checklist"])

    out = CliRunner().invoke(app, ["phase8", "controlled-worker-dry-run-gate", "--config", str(cfg_path()), "--output", "json"])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data["final_decision"] == "BLOCKED"
    assert data["execution_allowed"] is False
    assert data["phase8_acceptance_allowed"] is False
    assert data["farm5_0_1_118_batch_sync_evidence_present"] is True
    assert data["farm5_0_1_119_sync_required_before_controlled_worker_dry_run"] is True
    assert data["worker_start_authorized"] is False
    assert data["scheduler_authorized"] is False
    assert data["production_db_execution_authorized"] is False
    assert data["firewall_apply_authorized"] is False
    assert data["production_traffic_authorized"] is False
    assert data["blockers"] == []

    svc = Path("mpf/services/phase8_controlled_worker_dry_run_gate_service.py").read_text(encoding="utf-8").lower()
    banned = ["subprocess.run", "subprocess.popen", "os.system", "iptables-save", "iptables-restore", "conntrack", "docker", "systemctl", "psycopg.connect", "create_engine", "session.add", "session.commit", "write_text"]
    for token in banned:
        assert token not in svc
