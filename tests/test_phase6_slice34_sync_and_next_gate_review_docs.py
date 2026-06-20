from pathlib import Path

DOCS = [
    "docs/history/PHASE_STATUS_LEGACY_0.1.302.md",
    "README.md",
    "AGENTS.md",
    "docs/AI_CODING_RULES.md",
    "docs/AI_PHASE_6_TASK.md",
    "docs/INDEX.md",
    "docs/REMAINING_PHASE_PLAN.md",
]


def _text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase_status_current_state_unchanged_and_sync_evidence_present() -> None:
    phase = _text("docs/history/PHASE_STATUS_LEGACY_0.1.302.md")
    assert """current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no""" in phase
    for token in [
        "### Phase 6 Apply Slice 3-4 — Documentation Boundary Sync",
        "version accepted on farm5: 0.1.86",
        "pytest during sync: 499 passed",
        "manual pytest after sync: 499 passed",
        "source aligned with GitHub zip: OK",
        "Slice 3 and Slice 4 are accepted only as documentation/test-only boundaries",
        "Next planning target is Future Dedicated Phase 6 Apply Gate Proposal/Review.",
    ]:
        assert token in phase


def test_stale_next_step_wording_removed() -> None:
    phase = _text("docs/history/PHASE_STATUS_LEGACY_0.1.302.md")
    assert "Next planned Phase 6 implementation sub-step is Apply Slice 4" not in phase
    assert "batch server sync/review for Slice 3 and Slice 4" not in phase


def test_docs_aligned_and_no_positive_authorization() -> None:
    corpus = "\n".join(_text(p).lower() for p in DOCS)
    assert "next operational step: batch server sync/review for slice 3 and slice 4" not in corpus
    assert "not accepted by server evidence yet" not in _text("docs/REMAINING_PHASE_PLAN.md").lower()

    assert "dedicated apply gate remains not accepted and not authorized" in corpus
    assert "no manual canary apply" in corpus
    assert "no no-customer apply" in corpus
    assert "no live firewall read/write/apply/rollback/verify" in corpus
    assert "firewall_apply_allowed: yes" not in corpus
    assert "production_traffic: enabled" not in corpus
    assert "abuse_automation_allowed: yes" not in corpus


def test_abuse_invariant_preserved() -> None:
    corpus = "\n".join(_text(p) for p in DOCS).lower()
    assert "normal -> over_tracking -> over_grace -> hard" in corpus
