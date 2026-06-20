from pathlib import Path
DOC = Path("docs/PHASE_11_FARM5_0_1_231_LIMITED_ACCEPTANCE_DECISION_READY.md").read_text()
STATUS = Path("docs/PHASE_STATUS.md").read_text()
PLAN = Path("docs/REMAINING_PHASE_PLAN.md").read_text()
INDEX = Path("docs/history/INDEX_LEGACY_0.1.299.md").read_text()
def _current_state(text):
    return text.split("## Current State", 1)[1].split("## Accepted Server Results", 1)[0]
def test_evidence_records_ready_paths_hashes_and_closed_boundary():
    for marker in ("1512 passed", "limited-btc-001`, active".replace("`,", "`:"), "canary-btc-001`: active", "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS", "3b298863b05f27e178c68cd27f5480c64dca0662e1ed4b250a72fff69d1c5505", "/tmp/phase11-0.1.231-limited-acceptance-decision-gate-20260601T152222Z/phase11-limited-acceptance-decision-gate.json", "3d32ed030f05dc37801820565892a049a376aed264445f27e8dfa17e25bc48e0", "0636a9aa13923cb79a0c0e0d11220bfa154be6cf42dbfaeebcbf51640b0933fb", "next_required_step = phase11_controlled_boundary_acceptance_package_pr", "Phase 11 final acceptance is still not granted"):
        assert marker in DOC
def test_docs_link_new_evidence_and_target():
    assert "PHASE_11_FARM5_0_1_231_LIMITED_ACCEPTANCE_DECISION_READY.md" in INDEX
    assert "Phase 11 planning/readiness note (0.1.232)" in STATUS
    assert "## Phase 11 0.1.232 Active Target Position" in PLAN
def test_phase_status_current_state_stays_closed():
    block = _current_state(STATUS)
    for marker in ("production_traffic: controlled_cli_limited", "firewall_apply_allowed: controlled", "abuse_automation_allowed: controlled", "customer_onboarding_allowed: controlled_cli_limited", "proxy_data_plane_allowed: limited_runtime_local_only", "ui_allowed: no", "telegram_allowed: no"):
        assert marker in block
