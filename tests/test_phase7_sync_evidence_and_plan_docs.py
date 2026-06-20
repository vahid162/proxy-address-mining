from pathlib import Path


def test_remaining_plan_targets_updated() -> None:
    text = Path("docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md").read_text(encoding="utf-8")
    current = text.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "Current blocker before this PR: loopback canary DNAT target not route-safe for external PREROUTING traffic. (historical)" in text
