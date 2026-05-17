from pathlib import Path


def test_remaining_plan_targets_updated() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "GitHub main repository version before this PR is 0.1.127" in text
    assert "GitHub main repository version before this PR is 0.1.125" not in text.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "Repository version after this PR is 0.1.128" in text
    assert "latest recorded farm5 sync evidence is 0.1.127" in text
    assert "Current target is Phase 10 planning/readiness" in text
