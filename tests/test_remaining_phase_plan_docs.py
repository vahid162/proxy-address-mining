from pathlib import Path


def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")


def test_current_position_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    current = t.split("## Current Position", 1)[1].split("## Finite Remaining Path", 1)[0]
    assert "- GitHub main repository version before this PR is 0.1.137." in current
    assert "- Repository version after this PR is 0.1.138." in current
    assert "- latest recorded farm5 sync evidence is 0.1.136." in current
    assert "- Phase 10 final-acceptance-readiness is done." in current
    assert "- Phase 10 final acceptance is done." in current
    assert "- Current accepted phase is Phase 10." in current
    assert "- Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in current
    assert "- Next target is Phase 11 production/customer activation planning-readiness, then controlled CLI canary." in current
    assert "- Controlled CLI canary is not authorized by this PR." in current
    assert "- Production activation is not enabled by this PR." in current
    assert "- This PR only aligns stale current-state documentation and version metadata." in current


def test_finite_path_updates() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    path = t.split("## Finite Remaining Path", 1)[1].split("## Backend-First Principle", 1)[0]
    assert "5. Phase 10 Session / Worker / Policy / Share Timeline — accepted on farm5" in path
    assert "6. Phase 11 Production / Customer Activation Gate — current planning/readiness target" in path
    assert "7. Phase 12 Worker Policy Enforcement" in path
    assert "8. Phase 13 Local UI" in path
    assert "9. Phase 14 Operator UI Actions" in path
    assert "10. Phase 15 Telegram" in path
    assert "Phase 10 final acceptance — future explicit gate" not in path


def test_phase11_non_authorization_boundary() -> None:
    t = _read("docs/REMAINING_PHASE_PLAN.md")
    boundary = t.split("## Current Phase 11 Non-Authorization Boundary", 1)[1].split("## Historical Phase 8 Evidence Chain", 1)[0]
    for forbidden in (
        "production traffic",
        "controlled CLI canary execution",
        "limited real customer onboarding",
        "firewall apply",
        "iptables-restore",
        "customer NAT/customer firewall rules",
        "abuse automation runner",
        "real worker runtime",
        "scheduler/timer",
        "collector daemon",
        "UI",
        "Telegram",
    ):
        assert forbidden in boundary


def test_ai_phase10_task_marks_acceptance() -> None:
    t = _read("docs/AI_PHASE_10_TASK.md")
    assert "Phase 10 is accepted by this PR." in t
    assert "This PR implements Phase 10 final acceptance." in t
    assert "does not authorize Phase 11 production activation" in t
    assert "Phase 11 Production / Customer Activation Gate planning/readiness." in t
