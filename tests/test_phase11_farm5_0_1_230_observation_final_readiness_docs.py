from pathlib import Path

EVIDENCE = Path("docs/PHASE_11_FARM5_0_1_230_OBSERVATION_FINAL_READINESS_READY.md").read_text()
STATUS = Path("docs/PHASE_STATUS.md").read_text()

def _current_state(text):
    return text.split("## Current State", 1)[1].split("```text", 1)[1].split("```", 1)[0].strip()

def test_evidence_records_farm5_ready_results_and_hashes():
    for marker in ("1495 passed", "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS", "PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY",
        "PHASE11_FINAL_ACCEPTANCE_READINESS_PLANNING_READY", "limited-btc-001 active in all 3 samples", "canary-btc-001 active in all 3 samples",
        "92e8d5a9dd4da77ee953ad4fce2567b2a3c1989e68f010f0f950f0ac0fbf0af8", "f9bdf39c0f100ef922e11a6ce25ae74ff31410b4035378d8cb72508c0a151436",
        "4f4fabc1597b1af9ca33621fc0b109fada32be547fd9a0b9441d3a90da0c3580", "b547993870f749d72cf9fc5586189733458af8584000685eef9daecbe1dc716b"):
        assert marker in EVIDENCE

def test_phase_status_current_state_stays_closed():
    block = _current_state(STATUS)
    for marker in ("production_traffic: controlled_cli_limited", "firewall_apply_allowed: controlled", "abuse_automation_allowed: controlled", "customer_onboarding_allowed: controlled_cli_limited",
        "proxy_data_plane_allowed: limited_runtime_local_only", "ui_allowed: no", "telegram_allowed: no"):
        assert marker in block
    assert "0.1.231 planning/readiness note" in STATUS

def test_index_and_remaining_plan_reference_new_read_only_step():
    assert "PHASE_11_FARM5_0_1_230_OBSERVATION_FINAL_READINESS_READY.md" in Path("docs/INDEX.md").read_text()
    remaining = Path("docs/REMAINING_PHASE_PLAN.md").read_text()
    assert "Phase 11 0.1.231 Active Target Position" in remaining
    assert "phase11_controlled_boundary_acceptance_package_pr" in remaining
