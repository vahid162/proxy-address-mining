from pathlib import Path


def test_docs_regression_phase6_operator_acceptance() -> None:
    ps = Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
    assert 'current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5' in ps
    assert 'current_working_phase: Phase 8 — Abuse 1h Core planning/readiness' in ps
    assert 'production_traffic: none' in ps
    assert 'firewall_apply_allowed: no' in ps
    assert 'abuse_automation_allowed: no' in ps
    rem = Path('docs/REMAINING_PHASE_PLAN.md').read_text(encoding='utf-8').lower()
    assert '0.1.99' in rem
    ai = Path('docs/AI_PHASE_6_TASK.md').read_text(encoding='utf-8')
    assert 'latest recorded farm5 sync evidence is 0.1.99' in ai
    assert 'normal -> over_tracking -> over_grace -> hard' in ai
