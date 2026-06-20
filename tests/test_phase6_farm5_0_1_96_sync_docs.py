from pathlib import Path

def test_phase_status_contains_096_sync_evidence_section():
    t=Path('docs/history/PHASE_STATUS_LEGACY_0.1.302.md').read_text(encoding='utf-8')
    assert 'Phase 6 farm5 0.1.96 Sync + Manual Canary Proposal Readiness Evidence' in t
