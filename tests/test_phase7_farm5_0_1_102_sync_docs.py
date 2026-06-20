from pathlib import Path

def test_phase_status_has_0102_evidence() -> None:
    t = Path('docs/history/PHASE_STATUS_LEGACY_0.1.302.md').read_text(encoding='utf-8')
    assert 'synced to 0.1.102' in t
    assert '665 passed' in t
    assert '/var/backups/mpf/source-before-zip-sync-20260515T112408Z' in t
    assert 'Phase 7 Usage + Policy/Reject Accounting — Planning/Readiness Boundary' in t
    assert 'no runtime gate opened' in t
    assert 'runtime restrictions remain unchanged' in t
