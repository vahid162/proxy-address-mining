from pathlib import Path
def test_readme_current_status_is_phase11_accepted():
 s=Path('README.md').read_text(); current=s[s.index('## Current Status'):s.index('Historical compatibility anchors')]; assert 'Phase 11 — Production / Customer Activation Gate accepted on farm5' in current and 'Latest recorded farm5 sync evidence is 0.1.153' not in current and 'Actual canary execution has not been performed' not in current and 'Do not use this repository for production customer traffic yet' not in current
def test_current_contract_docs_have_0_1_234_update():
 for f in ('AGENTS.md','docs/INDEX.md','docs/AI_CODING_RULES.md','docs/REMAINING_PHASE_PLAN.md'): assert '0.1.234' in Path(f).read_text() or 'Phase 11 — Production / Customer Activation Gate accepted on farm5' in Path(f).read_text()
