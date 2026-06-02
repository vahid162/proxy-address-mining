from pathlib import Path
def test_final_docs_record_scope_and_safety():
 s=Path('docs/PHASE_11_FINAL_ACCEPTANCE.md').read_text(); assert 'controlled_cli_limited' in s and '127.0.0.1:60010 -> forwarder -> v2rayA -> pool' in s and 'normal -> over_tracking -> over_grace -> hard' in s and 'Worker enforcement remains disabled' in s
def test_evidence_doc_records_hashes():
 s=Path('docs/PHASE_11_FARM5_0_1_233_FINAL_ACCEPTANCE_PR_READINESS_READY.md').read_text(); assert '1551 passed' in s and 'fad4cdfcfa874a5712c4b79595e8675405b420dc0adff84356f67ed4901d55bc' in s and 'f7efe4921e8018c88b3670bf4c4be3d4dcb2a5b5285b7fd0102b6aa3b073a717' in s
