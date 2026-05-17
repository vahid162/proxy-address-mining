from pathlib import Path

from mpf import __version__


def test_version_0_1_129_consistency():
    assert Path('VERSION').read_text().strip() == '0.1.129'
    assert __version__ == '0.1.129'
    assert 'version = "0.1.129"' in Path('pyproject.toml').read_text(encoding='utf-8')


def test_phase10_docs_present():
    t = Path('docs/AI_PHASE_10_TASK.md').read_text(encoding='utf-8')
    assert 'Forbidden in this phase10 PR' in t
    assert 'report-only' in t


def test_phase_status_has_0_1_128_evidence():
    t = Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
    assert '### Phase 10 farm5 0.1.128 Sync/Test Evidence' in t
    assert '759 passed' in t
