from pathlib import Path

from mpf import __version__


def test_version_0_1_132_consistency():
    assert Path("VERSION").read_text().strip() == "0.1.132"
    assert __version__ == "0.1.132"
    assert 'version = "0.1.132"' in Path("pyproject.toml").read_text(encoding="utf-8")


def test_phase10_docs_present():
    t = Path("docs/AI_PHASE_10_TASK.md").read_text(encoding="utf-8")
    assert "Forbidden in this phase10 PR" in t
    assert "report-only" in t


def test_phase_status_has_0_1_128_evidence():
    t = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "### Phase 10 farm5 0.1.128 Sync/Test Evidence" in t
    assert "759 passed" in t


def test_phase10_farm5_0_1_131_evidence_doc_present():
    t = Path("docs/PHASE_10_FARM5_0_1_131_SYNC_TEST_EVIDENCE.md").read_text(encoding="utf-8")
    assert "server version after sync:\n  0.1.131" in t
    assert "768 passed" in t
    assert "production_traffic:\n  none" in t
    assert "firewall_apply_allowed:\n  no" in t
    assert "abuse_automation_allowed:\n  no" in t
    assert "no customer NAT redirects" in t
    assert "production customer traffic is still disabled" in t
