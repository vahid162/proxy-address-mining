from pathlib import Path


def test_readme_phase_alignment() -> None:
    t = Path("README.md").read_text(encoding="utf-8")
    assert "accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5" in t
    assert "working_phase: Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness" in t
    assert "Latest recorded farm5 sync evidence is 0.1.128" in t
    assert "not production activation" in t
    assert "Current target is Phase 10 planning/readiness" in t
    assert "fresh farm5 0.1.129 sync/test evidence" in t
    assert "production traffic" in t and "firewall apply" in t and "Telegram remain disabled" in t
    assert "Phase 9 Check / Report / Diagnostics accepted on farm5 as report-only/final diagnostics" in t
    assert "Phase 10 Session / Worker / Policy / Share Timeline planning/readiness in progress" in t


def test_readme_stale_wording_removed() -> None:
    t = Path("README.md").read_text(encoding="utf-8")
    assert "Phase 8 is planning/readiness only" not in t
    assert "Current Accepted/Working Boundary (Phase 7 accepted / Phase 8 working)" not in t
    assert "Current target is farm5 controlled worker dry-run evidence collection preparation" not in t
    assert "Future farm5 controlled worker dry-run evidence collection requires 0.1.121 sync/test" not in t
    assert "current clean sync gate installed and verified for Phase 5 accepted / Phase 6 working" not in t
    assert "Current Accepted/Working Boundary (Phase 8 accepted / Phase 9 planning)" not in t
    assert "Phase 9 report-only readiness package after 0.1.123 sync/test" not in t
    assert "fresh farm5 0.1.128 sync/test evidence is required after merge before Phase 10 implementation PRs" not in t


def test_ai_coding_rules_current_gate_and_stale_sections() -> None:
    t = Path("docs/AI_CODING_RULES.md").read_text(encoding="utf-8")
    assert "accepted: Phase 9 — Check / Report / Diagnostics accepted on farm5" in t
    assert "working: Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness" in t
    assert "accepted: Phase 7" not in t
    assert "Forbidden in current Phase 8 work:" not in t
    assert "Phase PR bodies must use Why / What / How to test / Version / Risk + Rollback." in t
