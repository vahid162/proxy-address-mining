from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_remaining_phase_plan_exists() -> None:
    assert Path("docs/REMAINING_PHASE_PLAN.md").exists()


def test_current_position_single_and_targets() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert t.count("## Current Position") == 1
    assert "- GitHub main repository version before this PR is 0.1.128." in current
    assert "- Repository version after this PR is 0.1.129." in current
    assert "- latest recorded farm5 sync evidence is 0.1.128." in current
    assert "- Current target is Phase 10 planning/readiness." in current
    assert "Phase 10" in current and "report-only" in current
    assert "farm5 0.1.129 sync/test" in current


def test_current_position_safety_and_non_activation() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- No production traffic is enabled." in current
    assert "- No firewall apply is enabled." in current
    assert "- No abuse automation runner is enabled." in current
    assert "- No customer NAT/customer firewall rules, UI, or Telegram is authorized." in current
    assert "- No production activation is enabled by this PR." in current


def test_finite_path_phase8_phase9_and_future_activation() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "3. Phase 8 Abuse 1h Core — accepted on farm5 in 0.1.123" in t
    assert "4. Phase 9 Check / Report / Diagnostics planning/readiness — accepted" in t
    assert "Phase 10" in t
    assert "Production / Customer Activation Gate — future, separate, explicit" in t


def test_no_stale_active_phase7_phase8_wording_in_current_position() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "accepted Phase 7 / working Phase 8" not in current
    assert "Phase 8 is planning/readiness only" not in current
    assert "Phase 8 Abuse 1h Core is accepted on farm5 in this PR" not in current
    assert "Phase 9 final-verdict report-only diagnostics package — current PR" not in current
    assert "Next explicit Phase 9 report-only diagnostics step — future after 0.1.125 sync/test" not in current
    assert "Phase 9 diagnostics bundle report-only package — current PR" not in current
    assert "Phase 9 final acceptance — current PR" not in current
