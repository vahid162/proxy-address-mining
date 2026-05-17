from pathlib import Path


def test_phase_status_has_farm5_0_1_124_evidence() -> None:
    t = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "### Phase 9 farm5 0.1.124 Sync/Test Evidence" in t
    assert "synced to 0.1.124" in t
    assert "pytest: 743 passed" in t
    assert "phase8 final-acceptance: ACCEPTED" in t
    assert "phase9 readiness: ACCEPTED / report-only" in t
    assert "all dangerous authorization flags remain false" in t
