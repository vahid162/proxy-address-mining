from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_current_position_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- Current accepted phase is Phase 10." in current
    assert "- Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in current
    assert "- Repository version after this PR is 0.1.205." in current
    assert "- farm5 0.1.200 single-customer DB-only staging evidence is recorded." in current
    assert "- After 0.1.205 sync and full pytest, run `mpf production single-customer-post-apply-evidence` to classify the recorded apply evidence on farm5." in current
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
