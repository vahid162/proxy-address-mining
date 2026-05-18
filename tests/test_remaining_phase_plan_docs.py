from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_current_position_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- GitHub main repository version before this PR is 0.1.137." in current
    assert "- Repository version after this PR is 0.1.136." in current
    assert "- latest recorded farm5 sync evidence is 0.1.136." in current
    assert "- Phase 10 final acceptance is introduced/completed by this PR." in current
    assert "- Next target is Phase 10 final acceptance after farm5 0.1.136 sync/test evidence." in current
    assert "- No production activation is enabled by this PR." in current


def test_finite_path_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "1. Phase 11 Production / Customer Activation Gate" in t
    assert "2. Phase 12 Worker Policy Enforcement" in t


def test_ai_phase10_task_marks_acceptance() -> None:
    t = _read("docs/AI_PHASE_10_TASK.md")
    assert "Phase 10 is accepted by this PR." in t
    assert "This PR implements Phase 10 final acceptance." in t
    assert "does not authorize Phase 11 production activation" in t
