from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase9_diagnostics_common import DANGEROUS_AUTHORIZATION_FLAGS
from mpf.services.phase9_final_acceptance_service import build_phase9_final_acceptance_report


def cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def test_phase9_final_acceptance_accepted() -> None:
    r = build_phase9_final_acceptance_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["acceptance_status"] == "PHASE9_ACCEPTED_ON_FARM5"
    assert r["latest_recorded_farm5_sync_evidence"] == "0.1.127"
    assert r["phase9_final_acceptance_readiness_status"] == "ACCEPTED"
    assert r["blockers"] == [] and r["warnings"] == [] and r["errors"] == []


def test_phase9_final_acceptance_fail_closed_without_0_1_127_evidence(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    phase = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8").replace("### Phase 9 farm5 0.1.127 Sync/Test Evidence", "### removed")
    (docs / "PHASE_STATUS.md").write_text(phase, encoding="utf-8")
    r = build_phase9_final_acceptance_report(cfg(), repo_root=tmp_path)
    assert r["final_decision"] == "BLOCKED"
    assert "farm5_0_1_127_sync_test_evidence_missing" in r["blockers"]


def test_phase9_final_acceptance_fail_closed_without_final_acceptance_readiness(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    phase = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8").replace("phase9 final-acceptance-readiness:\n  ACCEPTED", "phase9 final-acceptance-readiness:\n  BLOCKED")
    (docs / "PHASE_STATUS.md").write_text(phase, encoding="utf-8")
    r = build_phase9_final_acceptance_report(cfg(), repo_root=tmp_path)
    assert r["final_decision"] == "BLOCKED"
    assert "phase9_final_acceptance_readiness_missing" in r["blockers"]


def test_phase9_final_acceptance_all_dangerous_flags_are_computed_and_false() -> None:
    r = build_phase9_final_acceptance_report(cfg())
    assert all(r[k] is False for k in DANGEROUS_AUTHORIZATION_FLAGS)
    assert r["all_dangerous_authorization_flags_false"] is True


def test_phase9_final_acceptance_cli_json() -> None:
    out = CliRunner().invoke(app, ["phase9", "final-acceptance", "--config", "configs/mpf.example.yaml", "--output", "json"])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data["component"] == "phase9_final_acceptance"
