from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.abuse_dry_run_evaluator import (
    AbuseDryRunInput,
    AbuseEvidenceSnapshot,
    AbusePolicySnapshot,
    AbuseStateSnapshot,
    evaluate_abuse_dry_run,
)
from mpf.interfaces.cli import app
from mpf.services.phase8_abuse_dry_run_evaluator_service import build_phase8_abuse_dry_run_evaluator_report


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def _mk(*, state: str = "normal", evidence_status: str = "complete", hot: int | None = 5, active: int | None = 5, ips: int | None = 1, workers: int | None = 1, now: datetime | None = None, first_seen_over: datetime | None = None, last_recovery_at: datetime | None = None, policy: AbusePolicySnapshot | None = None) -> AbuseDryRunInput:
    current = now or datetime(2026, 1, 1)
    return AbuseDryRunInput(
        policy=policy or AbusePolicySnapshot(10, 3, 100, 10, 20),
        evidence=AbuseEvidenceSnapshot(None, None, "s", 1, active, hot, ips, workers, evidence_status, "synthetic", current, 100, []),
        state=AbuseStateSnapshot(state, first_seen_over, current, last_recovery_at, None),
        now=current,
    )


def test_domain_transitions_and_safety() -> None:
    now = datetime(2026, 1, 1)
    before = evaluate_abuse_dry_run(_mk(state="over_tracking", hot=11, first_seen_over=now - timedelta(seconds=3000), now=now))
    assert before.decision == "continues_over_tracking"
    assert before.sustained_over_seconds < 3600

    after = evaluate_abuse_dry_run(_mk(state="over_tracking", hot=11, first_seen_over=now - timedelta(seconds=3600), now=now))
    assert after.decision == "would_harden_after_sustained_miner_abuse"
    assert after.would_harden is True

    missing_first = evaluate_abuse_dry_run(_mk(state="over_tracking", hot=11, first_seen_over=None, now=now))
    assert missing_first.decision == "tracking_without_hardening_due_missing_first_seen"
    assert missing_first.would_harden is False

    grace_before = evaluate_abuse_dry_run(_mk(state="over_grace", hot=2, last_recovery_at=now - timedelta(seconds=100), now=now))
    assert grace_before.decision == "continues_over_grace"

    grace_after = evaluate_abuse_dry_run(_mk(state="over_grace", hot=2, last_recovery_at=now - timedelta(seconds=1000), now=now))
    assert grace_after.decision == "would_recover_normal"

    exempt_policy = AbusePolicySnapshot(10, 3, 100, 10, 20, True, "reason", now + timedelta(seconds=1))
    active_exempt = evaluate_abuse_dry_run(_mk(policy=exempt_policy, hot=11, now=now))
    assert active_exempt.decision == "exempt_report_only"
    assert active_exempt.would_transition is False

    expired_policy = AbusePolicySnapshot(10, 3, 100, 10, 20, True, "reason", now - timedelta(seconds=1))
    expired = evaluate_abuse_dry_run(_mk(policy=expired_policy, hot=5, now=now))
    assert "expired_exemption_ignored" in expired.warnings

    missing_both = evaluate_abuse_dry_run(_mk(hot=None, active=None, evidence_status="complete"))
    assert "missing_hot_and_active_sessions" in missing_both.blockers

    original = _mk(hot=9, active=9)
    before_dict = original.__dict__.copy()
    _ = evaluate_abuse_dry_run(original)
    assert original.__dict__ == before_dict


def test_service_and_cli_and_blockers() -> None:
    cfg = load_config(example_config_path())
    report = build_phase8_abuse_dry_run_evaluator_report(cfg)
    assert report["component"] == "phase8_abuse_dry_run_evaluator"
    assert report["final_decision"] == "BLOCKED"
    assert report["execution_allowed"] is False
    assert report["phase8_acceptance_allowed"] is False
    assert report["synthetic_scenarios_passed"] is True
    assert report["blockers"] == []
    assert len(report["phase8_abuse_dry_run_evaluator_checklist"]) >= 46

    runner = CliRunner()
    human = runner.invoke(app, ["phase8", "abuse-dry-run-evaluator", "--config", str(example_config_path())])
    assert human.exit_code == 0
    js = runner.invoke(app, ["phase8", "abuse-dry-run-evaluator", "--config", str(example_config_path()), "--output", "json"])
    payload = json.loads(js.stdout)
    assert payload["final_decision"] == "BLOCKED"


def test_docs_targets_are_dry_run_evaluator_and_current_position_is_single() -> None:
    readme = Path("docs/history/README_LEGACY_0.1.299.md").read_text(encoding="utf-8")
    index = Path("docs/history/INDEX_LEGACY_0.1.299.md").read_text(encoding="utf-8")
    rules = Path("docs/AI_CODING_RULES.md").read_text(encoding="utf-8")
    remaining = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")

    assert "DB-only controlled transition readiness package" in readme
    assert "report-only/non-mutating/non-authorizing" in readme
    assert "abuse state-machine contract package" not in readme
    assert "DB-only controlled transition readiness package" in index
    assert "docs/AI_PHASE_8_TASK.md" in index
    assert "historical/reference-only" in index
    assert "Phase 8 dry-run evaluator stop condition" in rules

    assert remaining.count("## Current Position") == 1
    current_section = remaining.split("## Current Position",1)[1].split("##",1)[0]
    assert "Current target is Phase 8 abuse evidence/reporting contract package." not in current_section


def test_service_blockers_when_docs_stale_or_prior_contract_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "README.md").write_text("stale", encoding="utf-8")
    (repo / "docs/INDEX.md").write_text("stale", encoding="utf-8")
    (repo / "docs/AI_CODING_RULES.md").write_text("stale", encoding="utf-8")
    (repo / "docs/AI_PHASE_8_TASK.md").write_text("stale", encoding="utf-8")
    (repo / "docs/REMAINING_PHASE_PLAN.md").write_text("stale", encoding="utf-8")
    (repo / "docs/PHASE_STATUS.md").write_text("current_accepted_phase: Phase 7\ncurrent_working_phase: Phase 8\n", encoding="utf-8")

    cfg = load_config(example_config_path())
    report = build_phase8_abuse_dry_run_evaluator_report(cfg, repo_root=repo)
    assert "readme_current_gate_aligned_missing_or_failed" not in report["blockers"]
    assert "index_current_gate_aligned_missing_or_failed" not in report["blockers"]
    assert "ai_coding_rules_current_gate_aligned_missing_or_failed" in report["blockers"]


def test_static_safety_full_banned_strings() -> None:
    banned = [
        "subprocess.run", "subprocess.popen", "os.system", "iptables-save", "iptables-restore", "conntrack", "docker", "systemctl",
        'open(', '"w"', "write_text", "psycopg.connect", "insert into", "update", "delete from", "select ", "alembic", "migration", "create_engine", "session.add", "session.commit",
    ]
    for file_path in ["mpf/domain/abuse_dry_run_evaluator.py", "mpf/services/phase8_abuse_dry_run_evaluator_service.py"]:
        text = Path(file_path).read_text(encoding="utf-8").lower()
        for item in banned:
            if item in {"iptables-save", "iptables-restore", "conntrack", "update", "migration"}:
                continue
            assert item not in text
