from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase9_final_acceptance_readiness_service import build_phase9_final_acceptance_readiness_report


def cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def test_phase9_final_acceptance_readiness_accepted() -> None:
    r = build_phase9_final_acceptance_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["final_acceptance_readiness"] == "PHASE9_FINAL_ACCEPTANCE_READINESS_ACCEPTED"
    assert r["latest_recorded_farm5_sync_evidence"] == "0.1.127"
    assert r["all_dangerous_authorization_flags_false"] is True
    assert r["blockers"] == [] and r["warnings"] == [] and r["errors"] == []


def test_phase9_final_acceptance_readiness_fail_closed_without_0_1_126_evidence(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    phase = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8").replace("### Phase 9 farm5 0.1.127 Sync/Test Evidence", "### removed")
    (docs / "PHASE_STATUS.md").write_text(phase, encoding="utf-8")
    r = build_phase9_final_acceptance_readiness_report(cfg(), repo_root=tmp_path)
    assert r["final_decision"] == "BLOCKED"
    assert "farm5_0_1_127_sync_test_evidence_missing" in r["blockers"]


def test_phase9_final_acceptance_readiness_fail_closed_without_diagnostics_status(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    phase = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8").replace("phase9 diagnostics:\n  ACCEPTED", "phase9 diagnostics:\n  BLOCKED")
    (docs / "PHASE_STATUS.md").write_text(phase, encoding="utf-8")
    r = build_phase9_final_acceptance_readiness_report(cfg(), repo_root=tmp_path)
    assert r["final_decision"] == "BLOCKED"
    assert "phase9_diagnostics_bundle_missing" in r["blockers"]


def test_phase9_final_acceptance_readiness_cli_json() -> None:
    out = CliRunner().invoke(app, ["phase9", "final-acceptance-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data["component"] == "phase9_final_acceptance_readiness"
