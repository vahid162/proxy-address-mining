from pathlib import Path


def test_docs_and_readme_updates() -> None:
    d = Path('docs/PHASE_11D_ACTUAL_MANUAL_CANARY_EXECUTION_RUN_PACKAGE.md').read_text(encoding='utf-8')
    assert 'manual-canary-execute --output json' in d

    r = Path('README.md').read_text(encoding='utf-8')
    assert 'Actual canary execution has not been performed or accepted.' in r

    rp = Path('docs/REMAINING_PHASE_PLAN.md').read_text(encoding='utf-8')
    assert 'GitHub main repository version before this PR is 0.1.164.' in rp
    assert 'Repository version after this PR is 0.1.165.' in rp
    assert 'latest recorded farm5 sync evidence is 0.1.164.' in rp
    assert 'Current blocker before this PR: single_canary_restore_payload_renderer_missing.' in rp
    assert 'single_canary_host_apply_context_not_confirmed' in rp
    assert 'accepted_single_canary_host_apply_execution_missing' in rp
    assert 'Phase 11 remains not accepted.' in rp


def test_runbook_exists_with_exact_command() -> None:
    rb = Path('docs/PHASE_11D_FARM5_MANUAL_CANARY_EXECUTION_RUNBOOK.md').read_text(encoding='utf-8')
    assert '--expected-version 0.1.165' in rb
    assert 'MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow' in rb
    assert 'single_canary_host_apply_context_not_confirmed' in rb
    assert 'accepted_single_canary_host_apply_execution_missing' in rb
    assert 'MPF_PHASE11_SINGLE_CANARY_HOST_APPLY=allow' in rb
