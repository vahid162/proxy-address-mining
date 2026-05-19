from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_current_position_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- GitHub main repository version before this PR is 0.1.145." in current
    assert "- Repository version after this PR is 0.1.146." in current
    assert "- latest recorded farm5 sync evidence is 0.1.145." in current
    assert "- Phase 10 final-acceptance-readiness is done." in current
    assert "- Phase 10 final acceptance is done." in current
    assert "- Current accepted phase is Phase 10." in current
    assert "- Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in current
    assert "- Phase 11A production readiness inventory is implemented and farm5 evidence recorded." in current
    assert "- Phase 11B canary plan/report is implemented and farm5 evidence recorded." in current
    assert "- Phase 11B remains report-only and non-authorizing for runtime execution." in current
    assert "- Phase 11C controlled activation harness is implemented and farm5 evidence recorded." in current
    assert "- Phase 11C remains non-authorizing; evidence recorded does not authorize runtime execution." in current
    assert "- next target is Phase 11D manual canary customer acceptance package." in current
    assert "- Phase 11D execution is not implemented or authorized by this PR." in current
    assert "- Controlled CLI canary is not authorized by this PR." in current
    assert "- Production activation is not enabled by this PR." in current


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
    assert "Current accepted phase is Phase 10." in t
    assert "Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in t
    assert "Phase 11D execution is not implemented or authorized by this PR." in t
    assert "production traffic remains none." in t
    assert "firewall apply remains no." in t
    assert "abuse automation remains no." in t
    assert "customer onboarding remains db_only." in t
    assert "UI remains no." in t
    assert "Telegram remains no." in t
