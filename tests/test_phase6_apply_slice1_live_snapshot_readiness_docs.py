from pathlib import Path

DOC = Path("docs/PHASE_6_APPLY_SLICE_1_LIVE_SNAPSHOT_READINESS_BOUNDARY.md")
PHASE_STATUS = Path("docs/PHASE_STATUS.md").read_text()
INDEX = Path("docs/INDEX.md").read_text()
AI_TASK = Path("docs/AI_PHASE_6_TASK.md").read_text()
REMAINING = Path("docs/REMAINING_PHASE_PLAN.md").read_text()
README = Path("README.md").read_text()


def test_new_doc_exists_and_status():
    text = DOC.read_text()
    assert DOC.exists()
    assert "Status: planned, documentation/test-only, non-authorizing" in text


def test_phase_status_current_state_unchanged():
    expected = """current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5\ncurrent_working_phase: Phase 6 — Firewall Planner\nserver_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\nproxy_data_plane_allowed: limited_runtime_local_only\nui_allowed: no\ntelegram_allowed: no"""
    assert expected in PHASE_STATUS


def test_apply_slice1_is_next_planned_not_accepted():
    assert "Apply Slice 1 has been server-synced and accepted only as a documentation/test-only readiness boundary." in PHASE_STATUS
    assert "Apply Slice 3 and Slice 4 are server-synced and accepted only as documentation/test-only boundaries." in PHASE_STATUS


def test_index_and_ai_task_reference_apply_slice1():
    assert "docs/PHASE_6_APPLY_SLICE_1_LIVE_SNAPSHOT_READINESS_BOUNDARY.md" in INDEX
    assert "Slice 1 and Slice 2 are server-synced documentation/test-only readiness boundaries." in AI_TASK


def test_no_authorization_claims_in_changed_docs():
    bundle = "\n".join([
        DOC.read_text(), PHASE_STATUS, INDEX, AI_TASK, REMAINING,
        Path("README.md").read_text(),
        Path("AGENTS.md").read_text(),
        Path("docs/AI_CODING_RULES.md").read_text(),
        Path("docs/FIREWALL.md").read_text(),
        Path("docs/ROADMAP.md").read_text(),
    ]).lower()
    banned = [
        "authorize live firewall read now",
        "authorize iptables-save now",
        "authorize live firewall write now",
        "authorize live firewall apply now",
        "authorize live rollback now",
        "authorize live verify now",
        "authorize iptables-restore now",
        "authorize real adapters now",
        "authorize subprocess firewall calls now",
        "authorize db writes now",
        "authorize locks now",
        "authorize restore points now",
        "authorize nat/customer firewall rules now",
        "authorize production traffic now",
        "authorize usage automation now",
        "authorize abuse automation now",
        "authorize ui now",
        "authorize telegram now",
    ]
    for term in banned:
        assert term not in bundle


def test_abuse_invariant_and_stale_wording_rejection():
    t = DOC.read_text()
    assert "normal -> over_tracking -> over_grace -> hard" in t
    assert "sustained miner-abuse hardens after about 3600 seconds" in t
    assert "farms-over alone must not harden" in t
    assert "worker-over alone must not harden" in t
    assert "no silent skip is allowed" in t

    stale_targets = [
        "next planned step is phase 6-g",
        "next planned documentation/test-only step is phase 6-h",
        "with phase 6-g documentation/test-only non-authorizing next step",
    ]
    for stale in stale_targets:
        assert stale not in (PHASE_STATUS + "\n" + INDEX + "\n" + AI_TASK + "\n" + REMAINING).lower()


def test_readme_and_phase_status_next_step_wording():
    assert "Future Dedicated Phase 6 Apply Gate Proposal/Review" in README
    assert "with Phase 6-G documentation/test-only non-authorizing next step" not in README
    assert "## Next Planned Step" in PHASE_STATUS
    assert "Future Dedicated Phase 6 Apply Gate Proposal/Review" in PHASE_STATUS
    assert "Next planned documentation/test-only step is Phase 6-H" not in PHASE_STATUS
