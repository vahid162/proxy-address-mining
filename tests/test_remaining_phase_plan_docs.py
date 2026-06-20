from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_remaining_phase_plan_is_non_authorizing_redirect() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert t.startswith("# Remaining Phase Plan")
    assert "historical compatibility only" in t
    assert "Current phase, runtime authorization, and next required step exist only in `docs/PHASE_STATUS.md`" in t
    assert "docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md" in t
    assert "cannot authorize runtime work" in t


def test_remaining_phase_plan_archive_retains_historical_text() -> None:
    t = _read("docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md")
    assert t.startswith("# Non-authorizing historical snapshot")
    body = t.split("---\n", 1)[1]
    assert "## Current Position" in body
    assert "- Current accepted phase is Phase 10." in body
    assert "- Repository version after this PR is 0.1.216." in body


def test_remaining_phase_plan_redirect_has_no_stale_snapshot_markers() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    stale = (
        "Current Position",
        "Current Position update",
        "Active Target Position",
        "Current accepted phase is Phase",
        "Repository version after this PR is 0.1.",
        "current_working_phase: Phase",
    )
    for marker in stale:
        assert marker not in t


def test_ai_phase10_task_is_historical_redirect() -> None:
    t = _read("docs/AI_PHASE_10_TASK.md")
    assert t.startswith("# AI Phase 10 Task")
    assert "historical compatibility only" in t
    assert "does not define the current phase" in t
    assert "docs/PHASE_STATUS.md" in t
    assert "docs/history/AI_PHASE_10_TASK_LEGACY_0.1.303.md" in t


def test_ai_phase10_archive_retains_historical_phase10_text() -> None:
    t = _read("docs/history/AI_PHASE_10_TASK_LEGACY_0.1.303.md")
    assert t.startswith("# Non-authorizing historical snapshot")
    body = t.split("---\n", 1)[1]
    assert "# AI Phase 10 Task" in body
    assert "Phase 10 is accepted by this PR." in body
    assert "This PR implements Phase 10 final acceptance." in body
