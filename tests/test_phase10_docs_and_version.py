from pathlib import Path

from mpf import __version__


def test_version_0_1_131_consistency():
    assert Path('VERSION').read_text().strip() == '0.1.131'
    assert __version__ == '0.1.131'
    assert 'version = "0.1.131"' in Path('pyproject.toml').read_text(encoding='utf-8')


def test_phase10_docs_present():
    t = Path('docs/AI_PHASE_10_TASK.md').read_text(encoding='utf-8')
    assert 'Forbidden in this phase10 PR' in t
    assert 'report-only' in t


def test_phase_status_has_0_1_128_evidence():
    t = Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
    assert '### Phase 10 farm5 0.1.128 Sync/Test Evidence' in t
    assert '759 passed' in t


def test_phase10_farm5_0_1_130_evidence_doc_present():
    t = Path('docs/PHASE_10_FARM5_0_1_130_SYNC_TEST_EVIDENCE.md').read_text(encoding='utf-8')
    assert 'server version: 0.1.130' in t
    assert 'pytest: 767 passed in 82.44s' in t
    assert 'all dangerous authorization flags: false' in t
    assert '/opt/mpf-py-src/.venv/bin/python -m pytest -q' in t
