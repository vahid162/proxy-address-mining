from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_current_position_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- Current accepted phase is Phase 10." in current
    assert "- Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in current
    assert "- Repository version after this PR is 0.1.209." in current
    assert "- post-apply evidence READY is recorded from farm5 0.1.205." in current
    assert "- 20101 controlled NAT/filter primitive artifact exists and is pending runtime-path/Stratum/visibility evidence." in current
    assert "- after 0.1.209 sync and full pytest, next intended farm5 step is long-lived external Stratum + runtime evidence collection/classification for 20101." in current
    assert "- then Stratum transcript evidence and visibility bundle." in current
    assert "- production traffic remains none." in current
    assert "- firewall apply remains no." in current
    assert "- customer onboarding remains db_only." in current
    assert "- abuse automation remains no." in current
    assert "- UI remains no." in current
    assert "- Telegram remains no." in current


def test_finite_path_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "11. Phase 11 Production / Customer Activation Gate" in t
    assert "12. Phase 12 Worker Policy Enforcement" in t
    assert "13. Phase 13 Local UI" in t
    assert "14. Phase 14 Operator UI Actions" in t
    assert "15. Phase 15 Telegram" in t


def test_ai_phase10_task_marks_acceptance() -> None:
    t = _read("docs/AI_PHASE_10_TASK.md")
    assert "Phase 10 is accepted by this PR." in t
    assert "This PR implements Phase 10 final acceptance." in t
    assert "does not authorize Phase 11 production activation" in t
    assert "Phase 11 Production / Customer Activation Gate planning/readiness." in t


def test_phase11_non_accepted_and_gates_closed() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "real customer traffic remains blocked until runtime path evidence, Stratum transcript, visibility bundle, abuse 1h coverage, restart/container-order evidence, and a later explicit acceptance PR." in t
