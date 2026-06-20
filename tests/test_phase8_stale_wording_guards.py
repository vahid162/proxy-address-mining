from pathlib import Path


def test_phase_status_has_no_stale_active_phase7_working_sentence() -> None:
    text = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8")
    assert "Current working phase is Phase 7 planning/readiness only" not in text
    assert "Historical note: at that time, current working phase was Phase 8 Abuse 1h Core planning/readiness only" in text


def test_remaining_plan_current_position_not_stale() -> None:
    text = Path("docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md").read_text(encoding="utf-8")
    assert "- Phase 6 is the accepted phase" not in text
    assert "- Phase 7 is the working phase" not in text
    assert "- Current work is Phase 7 planning/readiness" not in text
    assert "## Historical/Compatibility Notes" in text


def test_verify_current_phase_gate_messages_are_not_stale() -> None:
    text = Path("scripts/verify_current_phase_gate.sh").read_text(encoding="utf-8")
    assert "accepted Phase 5 gate" not in text
    assert "Phase 6 as current working phase" not in text
    assert "accepted Phase 5" not in text
    assert "accepted Phase 11" in text
    assert "Phase 12" in text


def test_ai_coding_rules_redirect_keeps_non_authorizing_compatibility_anchor() -> None:
    text = Path("docs/AI_CODING_RULES.md").read_text(encoding="utf-8")
    assert "Phase 8 Controlled Worker Pre-Acceptance Stop Condition" in text
    assert "Compatibility redirect" in text
    assert "docs/GUIDELINES.md" in text
