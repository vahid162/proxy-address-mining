from pathlib import Path


def test_phase_status_phase7_acceptance_and_0_1_108_evidence() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in text
    assert "current_working_phase: Phase 8 — Abuse 1h Core planning/readiness" in text
    assert "synced to 0.1.108" in text
    assert "/var/backups/mpf/source-before-zip-sync-20260515T181252Z" in text
    assert "694 passed" in text
    assert "Phase 7 Acceptance Scope" in text
    assert "Phase 8 Planning/Readiness Boundary" in text
    assert "Phase 7 acceptance does not authorize production traffic" in text
    assert "Phase 7 acceptance does not authorize firewall apply" in text
    assert "Phase 7 acceptance does not authorize abuse automation" in text
    assert "Phase 8 starts only as planning/readiness" in text


def test_remaining_phase_plan_active_wording() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "GitHub main repository version before this PR is 0.1.108" in text
    assert "Repository version after this PR is 0.1.109" in text
    assert "latest recorded farm5 sync evidence is 0.1.108" in text
    assert "Phase 7 is accepted as report-only/service-contract/readiness" in text
    assert "Phase 8 is the current working phase" in text
    assert "Next target after this PR is Phase 8 abuse state-machine contract package" in text
    assert "No server sync evidence for 0.1.109 exists until the operator syncs it after merge" in text


def test_ai_phase8_task_exists_and_invariant() -> None:
    text = Path("docs/AI_PHASE_8_TASK.md").read_text(encoding="utf-8")
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip" in text
