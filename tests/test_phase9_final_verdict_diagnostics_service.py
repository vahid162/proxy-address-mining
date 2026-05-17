from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase9_final_verdict_diagnostics_service import (
    DANGEROUS_AUTHORIZATION_FLAGS,
    build_phase9_final_verdict_diagnostics_report,
)


def test_phase9_final_verdict_service_report_only_and_safe_flags() -> None:
    cfg = load_config(Path("configs/mpf.example.yaml"))
    r = build_phase9_final_verdict_diagnostics_report(cfg)
    assert r["component"] == "phase9_final_verdict_diagnostics"
    assert r["execution_allowed"] is False
    assert r["report_only"] is True
    assert r["all_dangerous_authorization_flags_false"] is True
    for key in DANGEROUS_AUTHORIZATION_FLAGS:
        assert r[key] is False


def test_phase9_final_verdict_fails_closed_without_evidence(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "PHASE_STATUS.md").write_text(
        "current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5\n"
        "current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness\n",
        encoding="utf-8",
    )
    cfg = load_config(Path("configs/mpf.example.yaml"))
    r = build_phase9_final_verdict_diagnostics_report(cfg, repo_root=tmp_path)
    assert r["final_decision"] == "BLOCKED"
    assert "farm5_0_1_124_sync_evidence_missing" in r["blockers"]
    assert "phase8_final_acceptance_not_accepted" in r["blockers"]
    assert "phase9_readiness_not_accepted_report_only" in r["blockers"]
    assert r["all_dangerous_authorization_flags_false"] is True


def test_phase9_final_verdict_cli_json() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["phase9", "final-verdict", "--config", "configs/mpf.example.yaml", "--output", "json"])
    assert result.exit_code == 0
    assert '"component": "phase9_final_verdict_diagnostics"' in result.output
    assert '"execution_allowed": false' in result.output
