from pathlib import Path

def test_phase_status_has_0_1_95_evidence():
    text = Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
    assert 'farm5 synced to 0.1.95' in text
    assert '636 passed' in text
