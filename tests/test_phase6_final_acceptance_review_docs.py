from pathlib import Path

def test_phase6_docs_alignment_for_0_1_98_and_new_command():
    ai = Path('docs/AI_PHASE_6_TASK.md').read_text(encoding='utf-8')
    rem = Path('docs/REMAINING_PHASE_PLAN.md').read_text(encoding='utf-8')
    assert 'latest recorded farm5 sync evidence is 0.1.98' in ai
    assert 'mpf phase6 final-acceptance-review' in ai
    assert '0.1.98' in rem
