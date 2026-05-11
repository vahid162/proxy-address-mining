from pathlib import Path


def test_phase_status_gate_and_next_step_alignment() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5" in text
    assert "current_working_phase: Phase 6 — Firewall Planner" in text
    assert "production_traffic: none" in text
    assert "firewall_apply_allowed: no" in text
    assert "abuse_automation_allowed: no" in text
    assert "Phase 6-B" in text
    assert "live firewall apply remains forbidden" in text.lower()
