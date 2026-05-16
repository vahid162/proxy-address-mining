from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.abuse_transition_plan import build_db_mutation_plan, build_operator_approval_contract, build_transition_intent_from_dry_run_result
from mpf.interfaces.cli import app
from mpf.services.phase8_db_transition_readiness_service import build_phase8_db_transition_readiness_report


def cfg_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_readme_current_advancement_target_is_db_transition_readiness() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Current advancement target is the Phase 8 DB-only controlled transition execution package, manual and dry-run-by-default/non-runtime/non-authorizing." in readme
    assert "Current advancement target is the Phase 8 abuse dry-run evaluator package" not in readme


def test_domain_transition_plan_contracts() -> None:
    class R:
        current_state = "normal"; proposed_state = "over_tracking"; decision = "would_enter_over_tracking"
        would_transition = True; would_harden = False; transition_allowed = False; hardening_allowed = False
        dry_run = True; evidence_status = "complete"; sustained_over_seconds = 0; threshold_seconds = 3600; grace_seconds = 900
        reason = "dry_run_only"; blockers = []; warnings = []

    i1 = build_transition_intent_from_dry_run_result(customer_id=1, lane_id=1, customer_key="c1", port=1, evidence_source="synthetic", observed_at_iso="2026-01-01T00:00:00", dry_run_result=R())
    p1 = build_db_mutation_plan(i1)
    assert p1.writes_allowed is False and p1.execution_allowed is False
    assert p1.future_write_tables == ["abuse_states", "abuse_events"]

    approval = build_operator_approval_contract()
    assert approval.required is True
    assert approval.approval_allowed_in_this_pr is False and approval.execution_allowed_in_this_pr is False


def test_service_cli_and_blocked_defaults() -> None:
    cfg = load_config(cfg_path())
    r = build_phase8_db_transition_readiness_report(cfg)
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False
    assert r["db_reads_authorized"] is False
    assert r["db_writes_authorized"] is False
    assert "no_farm5_0_1_114_sync_evidence_claimed_missing_or_failed" in r["blockers"]
    assert r["synthetic_transition_plan_scenarios_passed"] is True

    runner = CliRunner()
    js = runner.invoke(app, ["phase8", "db-transition-readiness", "--config", str(cfg_path()), "--output", "json"])
    assert js.exit_code == 0
    payload = json.loads(js.stdout)
    assert payload["final_decision"] == "BLOCKED"


def test_blockers_for_stale_docs_and_fabricated_sync_and_missing_contracts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "mpf").mkdir(parents=True)
    (repo / "README.md").write_text("stale", encoding="utf-8")
    (repo / "docs/INDEX.md").write_text("stale", encoding="utf-8")
    (repo / "docs/AI_CODING_RULES.md").write_text("stale", encoding="utf-8")
    (repo / "docs/AI_PHASE_8_TASK.md").write_text("stale", encoding="utf-8")
    (repo / "docs/REMAINING_PHASE_PLAN.md").write_text("stale", encoding="utf-8")
    (repo / "docs/PHASE_STATUS.md").write_text("""current_accepted_phase: Phase 7
current_working_phase: Phase 8
synced to 0.1.110
synced to 0.1.114
""", encoding="utf-8")
    (repo / "mpf/models.py").write_text("", encoding="utf-8")

    cfg = load_config(cfg_path())
    report = build_phase8_db_transition_readiness_report(cfg, repo_root=repo)
    assert "readme_current_gate_aligned_missing_or_failed" in report["blockers"]
    assert "index_current_gate_aligned_missing_or_failed" in report["blockers"]
    assert "ai_coding_rules_current_gate_aligned_missing_or_failed" in report["blockers"]
    assert "remaining_plan_db_transition_target_aligned_missing_or_failed" in report["blockers"]
    assert "no_farm5_0_1_114_sync_evidence_claimed_missing_or_failed" in report["blockers"]


def test_checklist_reflects_failed_prerequisites(tmp_path: Path) -> None:
    repo = tmp_path / "repo2"
    (repo / "docs").mkdir(parents=True)
    (repo / "mpf").mkdir(parents=True)
    (repo / "docs/PHASE_STATUS.md").write_text("""current_accepted_phase: Phase 7
current_working_phase: Phase 8
synced to 0.1.110
""", encoding="utf-8")
    (repo / "README.md").write_text("ok DB-only controlled transition execution package", encoding="utf-8")
    (repo / "docs/INDEX.md").write_text("DB-only controlled transition readiness", encoding="utf-8")
    (repo / "docs/AI_CODING_RULES.md").write_text("Phase 8 DB-only transition readiness stop condition", encoding="utf-8")
    (repo / "docs/AI_PHASE_8_TASK.md").write_text("", encoding="utf-8")
    (repo / "docs/REMAINING_PHASE_PLAN.md").write_text("", encoding="utf-8")
    (repo / "mpf/models.py").write_text("", encoding="utf-8")

    cfg = load_config(cfg_path())
    report = build_phase8_db_transition_readiness_report(cfg, repo_root=repo)
    c = {i["item"]: i["status"] for i in report["phase8_db_transition_readiness_checklist"]}
    assert c["ai_phase8_task_present"] == "BLOCKED"
    assert c["existing_abuse_models_detected"] == "BLOCKED"
    assert report["future_migration_required"] is True


def test_static_safety_for_new_domain_and_service_files() -> None:
    banned = [
        "subprocess.run", "subprocess.popen", "os.system", "open(", '"w"', "write_text", "psycopg.connect",
        "insert into", "delete from", "select ", "alembic", "create_engine", "session.add", "session.commit",
    ]
    for file_path in ["mpf/domain/abuse_transition_plan.py", "mpf/services/phase8_db_transition_readiness_service.py"]:
        text = Path(file_path).read_text(encoding="utf-8").lower()
        for item in banned:
            assert item not in text
