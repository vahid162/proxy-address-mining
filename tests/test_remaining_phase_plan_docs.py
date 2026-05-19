from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_current_position_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- GitHub main repository version before this PR is 0.1.145." in current
    assert "- Repository version after this PR is 0.1.146." in current
    assert "- latest recorded farm5 sync evidence is 0.1.145." in current
    assert "- Phase 11A production readiness inventory is implemented and farm5 evidence recorded." in current
    assert "- Phase 11B canary plan/report is implemented and farm5 evidence recorded." in current
    assert "- Phase 11C controlled activation harness is implemented and farm5 evidence recorded." in current
    assert "- Phase 11C remains non-authorizing; evidence recorded does not authorize runtime execution." in current
    assert "- next target is Phase 11D manual canary customer acceptance package." in current
    assert "- Phase 11D execution is not implemented or authorized by this PR." in current
    assert "- Current accepted phase is Phase 10." in current
    assert "- Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in current


def test_phase11_non_accepted_and_gates_closed() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "Current accepted phase is Phase 10." in t
    assert "Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in t
    assert "production traffic remains none." in t
    assert "firewall apply remains no." in t
    assert "abuse automation remains no." in t
    assert "customer onboarding remains db_only." in t
    assert "UI remains no." in t
    assert "Telegram remains no." in t
