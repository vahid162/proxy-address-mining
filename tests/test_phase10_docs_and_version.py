from pathlib import Path

from mpf import __version__


def test_version_0_1_136_consistency():
    assert Path("VERSION").read_text().strip() == "0.1.136"
    assert __version__ == "0.1.136"
    assert 'version = "0.1.136"' in Path("pyproject.toml").read_text(encoding="utf-8")


def test_phase10_docs_present():
    t = Path("docs/AI_PHASE_10_TASK.md").read_text(encoding="utf-8")
    assert "Phase 10A/10B/10C are implemented." in t
    assert "Phase 10D/10E are implemented." in t
    assert "Phase 10F is implemented." in t
    assert "This PR implements Phase 10 final-acceptance-readiness." in t
    assert "This PR is not evidence-only." in t
    assert "This PR does not finally accept Phase 10." in t


def test_phase10_farm5_0_1_135_evidence_doc_present():
    t = Path("docs/PHASE_10_FARM5_0_1_135_SYNC_TEST_EVIDENCE.md").read_text(encoding="utf-8")
    assert "server version after sync:\n  0.1.135" in t
    assert "779 passed in 136.13s" in t
    assert "implementation-readiness: ACCEPTED" in t
    assert "runtime-worker-dry-run-readiness: ACCEPTED" in t
    assert "scheduler-dry-run-readiness: ACCEPTED" in t
    assert "worker-cycle-dry-run-plan: ACCEPTED" in t
    assert "production_traffic: none" in t
    assert "firewall_apply_allowed: no" in t
    assert "abuse_automation_allowed: no" in t
    assert "no customer NAT redirects" in t
    assert "production customer traffic is still disabled" in t
