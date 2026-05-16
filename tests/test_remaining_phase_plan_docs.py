from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding='utf-8')


def test_remaining_phase_plan_exists() -> None:
    assert Path('docs/REMAINING_PHASE_PLAN.md').exists()


def test_current_position_single_and_targets() -> None:
    t = _read('docs/REMAINING_PHASE_PLAN.md')
    assert t.count('## Current Position') == 1
    assert '- GitHub main repository version before this PR is 0.1.123.' in t
    assert '- Repository version after this PR is 0.1.124.' in t
    assert '- latest recorded farm5 sync evidence is 0.1.123.' in t
    assert '- Current target is Phase 9 Check / Report / Diagnostics planning/readiness.' in t
    assert '- Next target after this PR is Phase 9 readiness/report-only package, but only after this PR is merged and 0.1.123 is synced/tested on farm5.' in t
