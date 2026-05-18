from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_remaining_phase_plan_exists() -> None:
    assert Path("docs/REMAINING_PHASE_PLAN.md").exists()


def test_current_position_single_and_targets() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert t.count("## Current Position") == 1
    assert "- GitHub main repository version before this PR is 0.1.134." in current
    assert "- Repository version after this PR is 0.1.135." in current
    assert "- latest recorded farm5 sync evidence is 0.1.134." in current
    assert "- Phase 10F runtime worker/scheduler dry-run readiness is introduced." in current
    assert "- Current target is Phase 10 planning/readiness." in current
    assert "Phase 10 remains Session / Worker / Policy / Share Timeline" in current
    assert "farm5 0.1.134 sync/test" in current
    assert "Phase 10 final-acceptance-readiness" in current


def test_current_position_safety_and_non_activation() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- No production traffic is enabled." in current
    assert "- No firewall apply is enabled." in current
    assert "- No abuse automation runner is enabled." in current
    assert "- No real worker daemon is enabled." in current
    assert "- No background worker/scheduler/timer is enabled." in current
    assert "- No collector daemon is enabled." in current
    assert "- No worker policy enforcement is enabled." in current
    assert "- No customer NAT/customer firewall rules, UI, or Telegram is authorized." in current
    assert "- No production activation is enabled by this PR." in current


def test_finite_path_backend_first_after_phase10() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "3. Phase 8 Abuse 1h Core — accepted on farm5 in 0.1.123" in t
    assert "4. Phase 9 Check / Report / Diagnostics planning/readiness — accepted" in t
    assert "6. Phase 10A/10B/10C Session / Worker Identity / Worker Policy readiness" in t
    assert "7. Phase 10D/10E Share Timeline / Collector dry-run readiness" in t
    assert "8. Phase 10F Runtime Worker / Scheduler dry-run readiness" in t
    assert "9. Phase 10 final-acceptance-readiness" in t
    assert "10. Phase 10 final acceptance" in t
    assert "11. Phase 11 Production / Customer Activation Gate" in t
    assert "12. Phase 12 Worker Policy Enforcement" in t
    assert "13. Phase 13 Local UI" in t
    assert "14. Phase 14 Operator UI Actions" in t
    assert "15. Phase 15 Telegram" in t


def test_backend_first_sequence_is_explicit() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "Phase 10 accepted" in t
    assert "-> Phase 11 Production / Customer Activation Gate" in t
    assert "-> Phase 12 Worker Policy Enforcement after evidence/adapter support" in t
    assert "-> Phase 13 Local UI" in t
    assert "-> Phase 14 Operator UI Actions" in t
    assert "-> Phase 15 Telegram" in t


def test_no_stale_active_phase7_phase8_or_ui_first_wording_in_current_position() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    phase10_task = _read("docs/AI_PHASE_10_TASK.md")
    assert "accepted Phase 7 / working Phase 8" not in current
    assert "Phase 8 is planning/readiness only" not in current
    assert "Phase 8 Abuse 1h Core is accepted on farm5 in this PR" not in current
    assert "Phase 9 final acceptance — current PR" not in current
    assert "Phase 11 Local UI + Buyer Read-only" not in t
    assert "Production / Customer Activation Gate — future, separate, explicit" not in t
    assert "Next target\n- Phase 10D" not in phase10_task
    assert "Next target\n- Phase 10E" not in phase10_task
    assert "Next target\n- Phase 10F" not in phase10_task
