from pathlib import Path
from mpf.services.phase11e_limited_activation_common import _extract_current_state_block
DOC=Path('docs/PHASE_11_FARM5_0_1_232_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY.md').read_text(); STATUS=Path('docs/PHASE_STATUS.md').read_text(); INDEX=Path('docs/history/INDEX_LEGACY_0.1.299.md').read_text(); PLAN=Path('docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md').read_text()
def test_evidence_doc_records_ready_package_and_classifier_nuance():
 for marker in ('1531 passed','PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY','06f5c33086030d2da5c330c08c47ea36d49cdecd9284b2fcdb6ebe393b7e7271','05e177446951943595ee73b4365fa54409d5c4fde3449f1a388d074c996842fe','limited-btc-001`: active','canary-btc-001`: active','limited_btc_001_not_paused','next_required_step = phase11_controlled_boundary_acceptance_decision_pr','Phase 11 final acceptance is still not granted'): assert marker in DOC
def test_docs_index_and_plan_include_0_1_233_read_only_target(): assert 'PHASE_11_FARM5_0_1_232_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY.md' in INDEX and 'Phase 11 0.1.233 Active Target Position' in PLAN and 'controlled_cli_limited' in PLAN
def test_phase_status_current_state_remains_closed_and_unchanged():
 assert 'current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5' in _extract_current_state_block(STATUS)
 assert 'worker_enforcement_allowed: no' in _extract_current_state_block(STATUS)
