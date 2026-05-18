from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_current_position_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- GitHub main repository version before this PR is 0.1.136." in current
    assert "- Repository version after this PR is 0.1.137." in current
    assert "- latest recorded farm5 sync evidence is 0.1.136." in current
    assert "- Phase 10 final acceptance is introduced/completed by this PR." in current
    assert "- Current accepted phase is Phase 10." in current
    assert "- Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in current
    assert "- Next target is Phase 11 production/customer activation planning-readiness, then controlled CLI canary." in current
    assert "- Controlled CLI canary is not authorized by this PR." in current
    assert "- Production activation is not enabled by this PR." in current


def test_finite_path_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "11. Phase 11 Production / Customer Activation Gate" in t
    assert "12. Phase 12 Worker Policy Enforcement" in t
    assert "13. Phase 13 Local UI" in t
    assert "14. Phase 14 Operator UI Actions" in t
    assert "15. Phase 15 Telegram" in t


def test_ai_phase10_task_marks_acceptance() -> None:
    t = _read("docs/AI_PHASE_10_TASK.md")
    assert "Phase 10 is accepted by this PR." in t
    assert "This PR implements Phase 10 final acceptance." in t
    assert "does not authorize Phase 11 production activation" in t
    assert "Phase 11 Production / Customer Activation Gate planning/readiness." in t
