from pathlib import Path


def test_remaining_plan_targets_updated() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    current = text.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "GitHub main repository version before this PR is 0.1.155" in current
    assert "Repository version after this PR is 0.1.156" in current
    assert "latest recorded farm5 sync evidence is 0.1.153" in current
    assert "Next target: implement the missing accepted single-canary firewall apply adapter (`missing_real_firewall_apply_adapter`) so the explicit operator-approved canary execution can complete via service-layer boundaries." in current