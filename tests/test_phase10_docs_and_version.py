from pathlib import Path

from mpf import __version__


def test_version_0_1_134_consistency():
    assert Path("VERSION").read_text().strip() == "0.1.134"
    assert __version__ == "0.1.134"
    assert 'version = "0.1.134"' in Path("pyproject.toml").read_text(encoding="utf-8")


def test_phase10_docs_present():
    t = Path("docs/AI_PHASE_10_TASK.md").read_text(encoding="utf-8")
    assert "This PR is not evidence-only." in t
    assert "Phase 10A/10B/10C readiness contracts" in t


def test_phase10_farm5_0_1_133_evidence_doc_present():
    t = Path("docs/PHASE_10_FARM5_0_1_133_SYNC_TEST_EVIDENCE.md").read_text(encoding="utf-8")
    assert "server version after sync:\n  0.1.133" in t
    assert "773 passed in 145.95s" in t
    assert "production_traffic: none" in t
    assert "firewall_apply_allowed: no" in t
    assert "abuse_automation_allowed: no" in t
    assert "no customer NAT redirects" in t
    assert "production customer traffic is still disabled" in t
