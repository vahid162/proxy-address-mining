from pathlib import Path


def test_docs_and_readme_updates() -> None:
    d = Path('docs/PHASE_11D_ACTUAL_MANUAL_CANARY_EXECUTION_RUN_PACKAGE.md').read_text(encoding='utf-8')
    assert 'manual-canary-execute --output json' in d
    assert '--operator-confirmed' in d
    assert 'does **not** run canary' in d

    r = Path('README.md').read_text(encoding='utf-8')
    assert 'Latest recorded farm5 sync evidence is 0.1.151.' in r
    assert 'latest recorded farm5 evidence remains 0.1.151' in r
    assert 'Phase 11D actual operator-approved manual canary execution run package is implemented on GitHub by this PR' in r
    assert 'actual farm5 canary execution evidence is still pending' in r

    rp = Path('docs/REMAINING_PHASE_PLAN.md').read_text(encoding='utf-8')
    assert 'GitHub main repository version before this PR is 0.1.152.' in rp
    assert 'Repository version after this PR is 0.1.153.' in rp
    assert 'Latest recorded farm5 sync evidence' not in rp
    assert 'latest recorded farm5 sync evidence is 0.1.151.' in rp
    assert 'Phase 11D actual operator-approved manual canary execution run package is implemented in GitHub by this PR.' in rp
    assert 'Farm5 evidence for actual manual canary execution run package is pending.' in rp
    assert 'Next target: farm5 sync/test evidence for actual operator-approved manual canary execution run package.' in rp
    assert 'Phase 11 remains not accepted.' in rp
