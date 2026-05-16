from pathlib import Path


def test_readme_phase_alignment() -> None:
    t = Path('README.md').read_text(encoding='utf-8')
    assert 'accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5' in t
    assert 'working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness' in t
    assert '0.1.123' in t and 'sync evidence' in t
    assert 'not production activation' in t
    assert 'Phase 9 report-only readiness package after 0.1.123 sync/test' in t
    assert 'production traffic' in t and 'firewall apply' in t and 'Telegram remain disabled' in t
    assert 'Phase 8 Abuse 1h Core accepted on farm5 as evidence/readiness only' in t
    assert 'Phase 9 report-only diagnostics readiness package in progress' in t


def test_readme_stale_wording_removed() -> None:
    t = Path('README.md').read_text(encoding='utf-8')
    assert 'Phase 8 is planning/readiness only' not in t
    assert 'Current Accepted/Working Boundary (Phase 7 accepted / Phase 8 working)' not in t
    assert 'Current target is farm5 controlled worker dry-run evidence collection preparation' not in t
    assert 'Future farm5 controlled worker dry-run evidence collection requires 0.1.121 sync/test' not in t
    assert 'current clean sync gate installed and verified for Phase 5 accepted / Phase 6 working' not in t


def test_ai_coding_rules_current_gate_and_stale_sections() -> None:
    t = Path('docs/AI_CODING_RULES.md').read_text(encoding='utf-8')
    assert 'accepted: Phase 8 — Abuse 1h Core accepted on farm5' in t
    assert 'working: Phase 9 — Check / Report / Diagnostics planning/readiness' in t
    assert 'accepted: Phase 7' not in t
    assert 'Forbidden in current Phase 8 work:' not in t
    assert 'Phase PR bodies must use Why / What / How to test / Version / Risk + Rollback.' in t
