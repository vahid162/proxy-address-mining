from pathlib import Path


def test_readme_phase_alignment() -> None:
    t = Path("docs/history/README_LEGACY_0.1.299.md").read_text(encoding="utf-8")
    hist = Path("docs/HISTORICAL_COMPATIBILITY_ANCHORS.md").read_text(encoding="utf-8")
    assert "accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5" in t
    assert "working_phase: Phase 11 operational completion" in t
    assert "Latest recorded farm5 sync evidence is 0.1.128" in hist
    assert "not production activation" in hist
    assert "Current target is Phase 10 planning/readiness" in hist
    assert "fresh farm5 0.1.129 sync/test evidence" in hist
    assert "production/customer activation" in t and "firewall_apply_allowed: controlled" in t and "UI and Telegram remain later phases" in t
    assert "Phase 9 Check / Report / Diagnostics accepted on farm5 as report-only/final diagnostics" in t
    assert "Phase 10 Session / Worker / Policy / Share Timeline accepted on farm5" in t
    assert "Current advancement target is Phase 11 operational completion" in t
    assert "Historical compatibility anchors are kept in docs/HISTORICAL_COMPATIBILITY_ANCHORS.md." in t


def test_readme_stale_wording_removed() -> None:
    t = Path("docs/history/README_LEGACY_0.1.299.md").read_text(encoding="utf-8")
    assert "Phase 8 is planning/readiness only" not in t
    assert "Current Accepted/Working Boundary (Phase 7 accepted / Phase 8 working)" not in t
    assert "Current target is farm5 controlled worker dry-run evidence collection preparation" not in t
    assert "Future farm5 controlled worker dry-run evidence collection requires 0.1.121 sync/test" not in t
    assert "current clean sync gate installed and verified for Phase 5 accepted / Phase 6 working" not in t
    assert "Current Accepted/Working Boundary (Phase 8 accepted / Phase 9 planning)" not in t
    assert "Phase 9 report-only readiness package after 0.1.123 sync/test" not in t
    assert "fresh farm5 0.1.128 sync/test evidence is required after merge before Phase 10 implementation PRs" not in t


def test_ai_coding_rules_is_redirect_without_gate_snapshots() -> None:
    t = Path("docs/AI_CODING_RULES.md").read_text(encoding="utf-8")
    assert "Compatibility redirect" in t
    assert "docs/history/PHASE_STATUS_LEGACY_0.1.302.md" in t
    assert "docs/GUIDELINES.md" in t
    assert "accepted: Phase 7" not in t
    assert "working: Phase 11 operational completion" not in t
    assert "production_traffic:" not in t
