from pathlib import Path


def test_docs_and_readme_updates() -> None:
    d = Path('docs/PHASE_11D_ACTUAL_MANUAL_CANARY_EXECUTION_RUN_PACKAGE.md').read_text(encoding='utf-8')
    assert 'manual-canary-execute --output json' in d
    assert '--operator-confirmed' in d
    assert 'does **not** run canary' in d
    r = Path('README.md').read_text(encoding='utf-8')
    assert 'latest recorded farm5 evidence remains 0.1.151' in r
    rp = Path('docs/REMAINING_PHASE_PLAN.md').read_text(encoding='utf-8')
    assert 'Next target: farm5 sync/test evidence for actual operator-approved manual canary execution run package.' in rp
    assert 'Phase 11 remains not accepted.' in rp
