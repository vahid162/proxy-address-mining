from pathlib import Path


def test_docs_and_readme_updates() -> None:
    d = Path('docs/PHASE_11D_ACTUAL_MANUAL_CANARY_EXECUTION_RUN_PACKAGE.md').read_text(encoding='utf-8')
    assert 'manual-canary-execute --output json' in d
    assert '--operator-confirmed' in d
    assert 'does **not** run canary' in d

    r = Path('README.md').read_text(encoding='utf-8')
    assert 'Latest recorded farm5 sync evidence is 0.1.153.' in r
    assert 'Phase 11D actual operator-approved manual canary execution run package farm5 sync/test evidence is recorded.' in r
    assert 'Actual canary execution has not been performed or accepted.' in r

    rp = Path('docs/REMAINING_PHASE_PLAN.md').read_text(encoding='utf-8')
    assert 'GitHub main repository version before this PR is 0.1.153.' in rp
    assert 'Repository version after this PR is 0.1.154.' in rp
    assert 'Latest recorded farm5 sync evidence' not in rp
    assert 'latest recorded farm5 sync evidence is 0.1.153.' in rp
    assert 'Phase 11D actual operator-approved manual canary execution run package is implemented in GitHub and farm5 sync/test evidence is recorded.' in rp
    assert 'Actual farm5 canary execution has not been run by this PR.' in rp
    assert 'Next target: one explicit operator-approved manual canary execution run on farm5 and evidence collection.' in rp
    assert 'Phase 11 remains not accepted.' in rp
