from pathlib import Path


def test_phase11_farm5_0_1_151_evidence_doc_required_tokens() -> None:
    t = Path("docs/PHASE_11_FARM5_0_1_151_SYNC_TEST_EVIDENCE.md").read_text(encoding="utf-8")
    assert "0.1.151" in t
    assert "825 passed in 153.23s" in t
    assert "planning safety gate passed" in t
    assert "verify_current_phase_gate.sh" in t and "passes after absolute-path hardening" in t
    assert "production_traffic: none" in t
    assert "firewall_apply_allowed: no" in t
    assert "abuse_automation_allowed: no" in t
    assert "customer_onboarding_allowed: db_only" in t
    assert "does **not** authorize Phase 11D actual execution" in t
    assert "Production traffic, firewall apply, customer NAT/rules, customer DB mutation, abuse automation, UI, and Telegram remain closed." in t


def test_readme_plan_phase_status_align_0_1_151() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    plan = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    phase_status = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")

    assert "Latest recorded farm5 sync evidence is 0.1.153." in readme
    assert "Phase 11D operator-reviewed manual canary execution run preparation package farm5 evidence is recorded." in readme
    assert "Actual canary execution has not been performed or accepted." in readme

    assert "latest recorded farm5 sync evidence is 0.1.153." in plan
    assert "Next target: sync latest main to farm5, run explicit operator-approved single-canary execution once, and collect evidence; if execution blocks, implement the exact missing primitive reported as `accepted_single_canary_host_apply_primitive`." in plan
    assert "Current accepted phase is Phase 10." in plan
    assert "Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in plan
    assert "Phase 11 is accepted" not in plan
    assert "production traffic remains none." in plan
    assert "firewall apply remains no" in plan
    assert "abuse automation remains no." in plan
    assert "customer onboarding remains db_only" in plan
    assert "UI remains no." in plan
    assert "Telegram remains no." in plan

    assert "Phase 11D operator-reviewed execution run preparation farm5 evidence recorded" in phase_status
