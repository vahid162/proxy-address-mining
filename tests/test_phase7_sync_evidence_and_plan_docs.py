from pathlib import Path

def test_remaining_plan_targets_updated() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "GitHub main repository version before this PR is 0.1.124" in text
    assert "Repository version after this PR is 0.1.125" in text
    assert "latest recorded farm5 sync evidence is 0.1.124" in text
    assert "Current target is Phase 9 Check / Report / Diagnostics planning/readiness" in text
