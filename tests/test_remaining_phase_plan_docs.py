from pathlib import Path

def _read(p:str)->str:return Path(p).read_text(encoding="utf-8")

def test_remaining_phase_plan_exists():
    assert Path("docs/REMAINING_PHASE_PLAN.md").exists()

def test_current_position_updated():
    t=_read("docs/REMAINING_PHASE_PLAN.md")
    assert "Repository version after this PR is 0.1.123." in t
    assert "Current target is Phase 9 Check / Report / Diagnostics planning/readiness." in t

def test_finite_path_updated():
    t=_read("docs/REMAINING_PHASE_PLAN.md")
    assert "3. Phase 8 Abuse 1h Core — accepted on farm5 in 0.1.123" in t
    assert "4. Phase 9 Check / Report / Diagnostics planning/readiness — current target" in t
    assert "11. Production / Customer Activation Gate" in t
