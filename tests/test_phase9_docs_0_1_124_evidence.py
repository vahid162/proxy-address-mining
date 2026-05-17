from pathlib import Path


def test_phase_status_has_farm5_0_1_126_evidence() -> None:
    t = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "### Phase 9 farm5 0.1.126 Sync/Test Evidence" in t
    assert "server version after sync:\n  0.1.126" in t
    assert "pytest:\n  750 passed" in t
    assert "phase9 diagnostics:\n  ACCEPTED" in t
    assert "all dangerous authorization flags:\n  false" in t
