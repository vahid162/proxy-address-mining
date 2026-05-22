from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase8_farm5_dry_run_evidence_collection_service import (
    build_phase8_farm5_dry_run_evidence_collection_report,
)

EXPECTED_VERSION = "0.1.176"


def cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def test_runbook_exists_and_content() -> None:
    p = Path("docs/PHASE_8_FARM5_CONTROLLED_WORKER_DRY_RUN_EVIDENCE_COLLECTION.md")
    assert p.exists()
    t = p.read_text(encoding="utf-8")
    for s in [
        "## Status",
        "## Preconditions",
        "## Commands To Run After 0.1.121 Sync",
        "## Expected Dry-Run Evidence",
        "## Required Safety Evidence",
        "## Evidence Capture Format",
        "Runbook only.",
        "Not executed by this PR.",
        "Does not accept Phase 8.",
        "mpf phase8 controlled-worker-dry-run --output json",
        "mpf phase8 controlled-worker-dry-run --operator-confirmed --output json",
        "mpf phase8 controlled-worker-dry-run-gate --output json",
        "mpf phase8 controlled-worker-pre-acceptance --output json",
        "mpf phase-status",
        "mpf doctor",
        "must not be run as background services",
        "must not be scheduled",
        "must not be wrapped in systemd/cron/docker runtime automation",
    ]:
        assert s in t


def test_service_and_cli() -> None:
    r = build_phase8_farm5_dry_run_evidence_collection_report(cfg())
    assert r["component"] == "phase8_farm5_dry_run_evidence_collection"
    assert r["final_decision"] == "BLOCKED"
    assert r["evidence_collection_status"] == "PREPARED_NOT_EXECUTED"
    assert r["execution_allowed"] is False
    assert r["phase8_acceptance_allowed"] is False
    assert r["dry_run_evidence_claimed"] is False
    assert r["repository_version"] == EXPECTED_VERSION
    assert r["latest_recorded_farm5_sync_evidence"] == "0.1.120"
    assert r["farm5_0_1_120_sync_evidence_present"] is True
    assert r["farm5_0_1_121_sync_required_before_dry_run_evidence"] is True
    assert r["dry_run_evidence_collection_runbook_present"] is True
    assert r["runbook_status_not_executed"] is True
    assert isinstance(r["phase8_farm5_dry_run_evidence_collection_checklist"], list)
    assert all(i["name"] for i in r["phase8_farm5_dry_run_evidence_collection_checklist"])

    out = CliRunner().invoke(app, ["phase8", "farm5-dry-run-evidence-collection", "--config", "configs/mpf.example.yaml", "--output", "json"])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data["final_decision"] == "BLOCKED"
    assert data["execution_allowed"] is False
    assert data["phase8_acceptance_allowed"] is False
    assert data["dry_run_evidence_claimed"] is False
    assert data["farm5_0_1_120_sync_evidence_present"] is True
    assert data["farm5_0_1_121_sync_required_before_dry_run_evidence"] is True
    assert data["worker_start_authorized"] is False
    assert data["scheduler_authorized"] is False
    assert data["production_db_execution_authorized"] is False
    assert data["firewall_apply_authorized"] is False
    assert data["production_traffic_authorized"] is False
