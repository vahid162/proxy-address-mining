from pathlib import Path

def test_phase_status_has_farm5_0_1_98_evidence_section():
    t = Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
    assert 'Phase 6 farm5 0.1.98 Sync + Final Review Readiness Evidence' in t
    assert 'pytest during sync: 652 passed' in t
    assert '/var/backups/mpf/source-before-zip-sync-20260515T090826Z' in t
