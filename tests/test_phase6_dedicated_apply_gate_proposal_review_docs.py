from __future__ import annotations

from pathlib import Path


def _contains_positive_authorization(text: str, term: str) -> bool:
    blockers = ("not authorized", "no ", "forbidden", "must not", "remains not accepted")
    for line in text.lower().splitlines():
        if term in line:
            if any(b in line for b in blockers):
                continue
            if "does not authorize" in line:
                continue
            return True
    return False


def test_phase6_dedicated_apply_gate_proposal_review_docs() -> None:
    repo = Path(__file__).resolve().parents[1]
    phase_status = (repo / "docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    proposal = (repo / "docs/PHASE_6_DEDICATED_APPLY_GATE_PROPOSAL_REVIEW.md").read_text(encoding="utf-8")

    expected_current_state = """## Current State

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```
"""
    assert expected_current_state in phase_status
    assert "Status: proposal/review contract only; documentation/test-only; non-authorizing" in proposal
    assert "docs/PHASE_6_DEDICATED_APPLY_GATE_PROPOSAL_REVIEW.md" in phase_status
    assert "Future dedicated Phase 6 apply gate remains not accepted and not authorized" in phase_status

    accepted_section = phase_status[phase_status.index("## Accepted Server Results") :]
    assert "Dedicated Apply Gate Proposal/Review" not in accepted_section

    checked = [phase_status, proposal]
    forbidden_terms = [
        "authorize live firewall read",
        "authorize live firewall write",
        "authorize live firewall apply",
        "authorize live firewall rollback",
        "authorize live firewall verify",
        "authorize iptables-save",
        "authorize iptables-restore",
        "authorize real adapters",
        "authorize subprocess firewall calls",
        "authorize restore point writes",
        "authorize lock acquisition",
        "authorize db writes",
        "authorize db apply records",
        "authorize migrations",
        "authorize customer nat",
        "authorize customer firewall rules",
        "authorize production traffic",
        "authorize usage automation",
        "authorize abuse automation",
        "authorize ui",
        "authorize telegram",
    ]

    for doc in checked:
        for term in forbidden_terms:
            assert not _contains_positive_authorization(doc, term)

    assert "one-hour miner-abuse state machine" in (repo / "docs/ABUSE.md").read_text(encoding="utf-8")
