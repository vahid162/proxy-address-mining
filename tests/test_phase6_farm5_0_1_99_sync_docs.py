from pathlib import Path


def test_phase_status_has_farm5_0_1_99_sync_evidence() -> None:
    t = Path('docs/history/PHASE_STATUS_LEGACY_0.1.302.md').read_text(encoding='utf-8')
    assert 'farm5 synced to 0.1.99' in t
    assert 'pytest during sync: 657 passed' in t
    assert '/var/backups/mpf/source-before-zip-sync-20260515T092830Z' in t
    assert 'no runtime gate opened' in t
    assert 'runtime restrictions remain unchanged' in t
