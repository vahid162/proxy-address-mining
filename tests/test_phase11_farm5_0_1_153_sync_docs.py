from pathlib import Path


def test_phase11_farm5_0_1_153_evidence_doc_required_content() -> None:
    p = Path("docs/PHASE_11_FARM5_0_1_153_SYNC_TEST_EVIDENCE.md")
    assert p.exists()
    t = p.read_text(encoding="utf-8")

    assert "0.1.153" in t
    assert "835 passed in 155.97s" in t
    assert "mpf production manual-canary-execute --output json" in t
    assert "PLAN_READY_FOR_FARM5_SYNC_EVIDENCE" in t
    assert "MANUAL_CANARY_EXECUTION_PACKAGE_NON_AUTHORIZING" in t
    assert "execution_allowed: false" in t
    assert "actual_canary_execution_performed: false" in t
    assert "mutation_performed: false" in t
    assert "production_traffic_enabled: false" in t
    assert "All dangerous safety flags are false" in t
    assert "mpf production canary-execution-run-prep --output json" in t
    assert "READY_FOR_FARM5_SYNC_EVIDENCE" in t
    assert "actual canary execution is **not performed**" in t
    assert "actual canary execution is **not accepted**" in t
    assert "Limited real customer onboarding remains forbidden" in t
    assert "Production traffic, firewall apply" in t


def test_docs_alignment_after_0_1_153_evidence_recording() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Latest recorded farm5 sync evidence is 0.1.153." in readme

    plan = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "latest recorded farm5 sync evidence is 0.1.159." in plan
    assert "Next target: sync latest main to farm5, run explicit operator-approved single-canary execution once, and collect evidence; if execution blocks, implement the exact missing primitive reported as `accepted_single_canary_host_apply_primitive`." in plan
    assert "Phase 11 remains not accepted." in plan
    assert "production traffic remains none." in plan
    assert "firewall apply remains no except future explicit single-canary operator-approved run path." in plan
    assert "abuse automation remains no." in plan
    assert "customer onboarding remains db_only except future explicit canary run path." in plan
    assert "UI remains no." in plan
    assert "Telegram remains no." in plan

    phase_status = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 10" in phase_status
    assert "current_working_phase: Phase 11" in phase_status
    assert "Phase 11D actual execution not authorized" in phase_status or "actual canary execution not accepted" in phase_status
