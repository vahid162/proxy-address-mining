from pathlib import Path

def test_docs_updated_manual_canary_target():
    rp = Path('docs/REMAINING_PHASE_PLAN.md').read_text(encoding='utf-8')
    ai = Path('docs/AI_PHASE_6_TASK.md').read_text(encoding='utf-8')
    assert 'latest recorded farm5 sync evidence is 0.1.98' in rp
    assert 'manual-canary-customer-proposal' in ai
