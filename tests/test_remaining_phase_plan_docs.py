from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_current_position_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- GitHub main repository version before this PR is 0.1.135." in current
    assert "- Repository version after this PR is 0.1.136." in current
    assert "- latest recorded farm5 sync evidence is 0.1.135." in current
    assert "- Phase 10 final-acceptance-readiness is introduced." in current
    assert "- Next target is Phase 10 final acceptance after farm5 0.1.136 sync/test evidence." in current
    assert "- No production activation is enabled by this PR." in current


def test_finite_path_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "9. Phase 10 final-acceptance-readiness" in t
    assert "10. Phase 10 final acceptance" in t
    assert "11. Phase 11 Production / Customer Activation Gate" in t


def test_ai_phase10_target_is_not_phase10f() -> None:
    t = _read("docs/AI_PHASE_10_TASK.md")
    assert "Phase 10F is implemented." in t
    assert "Next target\n- Phase 10F" not in t
    assert "Next target\n- Phase 10 final acceptance" in t
