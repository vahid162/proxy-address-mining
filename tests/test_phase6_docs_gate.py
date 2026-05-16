from pathlib import Path


def test_phase_status_gate_and_next_step_alignment() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5" in text
    assert "current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness" in text
    assert "production_traffic: none" in text
    assert "firewall_apply_allowed: no" in text
    assert "abuse_automation_allowed: no" in text
    assert "live firewall apply remains forbidden" in text.lower()


def test_next_step_mentions_phase6g_and_not_authorize_live_apply() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "## Next Planned Step" in text
    assert "Phase 6-G" in text
    assert "does not authorize live apply" in text.lower() or "live apply remains forbidden" in text.lower()


def test_phase6_c_accepted_server_results_subsection_present() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "### Phase 6-C — Offline Apply Gate Readiness/Review" in text
    assert "version accepted on farm5: 0.1.56" in text
    assert "pytest passed: 337 passed" in text
    assert "mpf firewall gate-review final_decision: BLOCKED" in text
    assert "risk_summary.total: 18" in text
    assert "checklist_summary.total: 4" in text


def test_phase6_c_acceptance_doc_indexed() -> None:
    text = Path("docs/INDEX.md").read_text(encoding="utf-8")
    assert "docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md" in text
