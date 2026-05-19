from pathlib import Path


def test_remaining_plan_targets_updated() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    current = text.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "GitHub main repository version before this PR is 0.1.139" in current
    assert "Repository version after this PR is 0.1.140" in current
    assert "latest recorded farm5 sync evidence is 0.1.136" in current
    assert "Current accepted phase is Phase 10" in current
    assert "Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness" in current
    assert "Controlled CLI canary is not authorized by this PR" in current
    assert "Production activation is not enabled by this PR" in current
