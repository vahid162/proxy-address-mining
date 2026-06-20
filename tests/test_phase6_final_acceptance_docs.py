from pathlib import Path

def test_docs_updated_for_096_and_new_commands():
    ps=Path('docs/history/PHASE_STATUS_LEGACY_0.1.302.md').read_text(encoding='utf-8')
    assert 'farm5 synced to 0.1.98' in ps
    assert '652 passed' in ps
    assert '/var/backups/mpf/source-before-zip-sync-20260515T083309Z' in ps
    rp=Path('docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md').read_text(encoding='utf-8')
    assert 'latest recorded farm5 sync evidence is 0.1.100' in rp
    ai=Path('docs/AI_PHASE_6_TASK.md').read_text(encoding='utf-8')
    assert 'manual-canary-customer-server-evidence' in ai
    assert 'phase6 final-acceptance-readiness' in ai
