from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase_status_current_state_unchanged_and_proposal_section_present() -> None:
    text = _read("docs/PHASE_STATUS.md")
    current_state = """current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
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
restore_lock_record_execution_allowed: controlled_boundary_only"""
    assert current_state in text
    assert "### Phase 6 Dedicated Apply Gate — Proposal Review" in text


def test_proposal_review_contains_required_non_authorizing_terms() -> None:
    text = _read("docs/PHASE_STATUS.md")
    required = [
        "proposal/review only",
        "documentation/test-only",
        "non-authorizing",
        "firewall_apply_allowed remains no",
        "production_traffic remains none",
        "apply_decision remains BLOCKED",
        "no-customer apply/verify/rollback",
        "customer NAT",
        "customer firewall rules",
        "production traffic",
        "usage automation",
        "abuse automation",
        "UI",
        "Telegram",
        "read-only iptables-save snapshot evidence",
        "restore point + scoped lock + DB apply record preparation boundary",
        "CONTROLLED_BOUNDARY_EXECUTED",
        "restore_point_id=1",
        "firewall_apply_id=1",
    ]
    for phrase in required:
        assert phrase in text


def test_remaining_plan_ai_task_and_readme_alignment() -> None:
    remaining = _read("docs/REMAINING_PHASE_PLAN.md")
    ai_task = _read("docs/AI_PHASE_6_TASK.md")
    readme = _read("README.md")

    assert "docs/PHASE_STATUS.md remains the authoritative gate." in remaining
    assert "read-only iptables-save live snapshot path is explicitly authorized and evidenced" in remaining.lower()
    assert "1. Dedicated Apply Gate Proposal/Review" in remaining
    assert "8. Phase 7 Usage + Policy/Reject Accounting" in remaining
    assert "9. Phase 8 Abuse 1h Core" in remaining

    assert "Live Snapshot Read Gate Proposal" not in ai_task
    assert "live_snapshot_read_allowed: iptables_save_read_only" in ai_task
    assert "restore_lock_record_execution_allowed: controlled_boundary_only" in ai_task

    assert "docs/PHASE_STATUS.md" in readme
    assert "Phase 6-H accepted" not in readme
    assert "Phase 6 Dedicated Apply Gate Proposal/Review" in readme


def test_abuse_invariant_still_present_in_docs() -> None:
    corpus = "\n".join(
        [
            _read("AGENTS.md"),
            _read("docs/AI_PHASE_6_TASK.md"),
            _read("docs/REMAINING_PHASE_PLAN.md"),
        ]
    )
    assert "normal -> over_tracking -> over_grace -> hard" in corpus
    assert "farms-over alone must not harden" in corpus
    assert "worker-over alone must not harden" in corpus
