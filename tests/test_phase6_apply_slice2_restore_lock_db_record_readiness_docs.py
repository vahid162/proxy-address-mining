from pathlib import Path

DOC = Path("docs/PHASE_6_APPLY_SLICE_2_RESTORE_LOCK_DB_APPLY_RECORD_READINESS.md")
PHASE_STATUS = Path("docs/PHASE_STATUS.md").read_text()
INDEX = Path("docs/INDEX.md").read_text()
AI_TASK = Path("docs/AI_PHASE_6_TASK.md").read_text()
REMAINING = Path("docs/REMAINING_PHASE_PLAN.md").read_text()


def test_slice2_doc_exists_and_status():
    t = DOC.read_text()
    assert DOC.exists()
    assert "Status: planned, documentation/test-only, non-authorizing" in t


def test_phase_status_current_state_unchanged_and_next_step_slice3():
    expected = """current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5\ncurrent_working_phase: Phase 8 — Abuse 1h Core planning/readiness\nserver_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\nproxy_data_plane_allowed: limited_runtime_local_only\nui_allowed: no\ntelegram_allowed: no"""
    assert expected in PHASE_STATUS
    assert "Future Dedicated Phase 6 Apply Gate Proposal/Review" in PHASE_STATUS


def test_not_accepted_server_results_and_indexing():
    accepted_block = PHASE_STATUS.split("## Accepted Server Results", 1)[1].split("## Next Planned Step", 1)[0]
    assert "Apply Slice 1-2" in accepted_block
    assert "docs/PHASE_6_APPLY_SLICE_2_RESTORE_LOCK_DB_APPLY_RECORD_READINESS.md" in INDEX
    assert "Slice 1 and Slice 2 are server-synced documentation/test-only readiness boundaries." in AI_TASK
    assert "finite" in REMAINING.lower()


def test_non_authorizing_terms_and_abuse_invariant_preserved():
    bundle = "\n".join([
        DOC.read_text(), PHASE_STATUS, INDEX, AI_TASK, REMAINING,
        Path("README.md").read_text(), Path("AGENTS.md").read_text(),
        Path("docs/AI_CODING_RULES.md").read_text(), Path("docs/FIREWALL.md").read_text(),
        Path("docs/ROADMAP.md").read_text(),
    ]).lower()
    required = [
        "no restore point writes", "no lock acquisition", "no db apply writes", "db apply record",
        "no migrations", "no live firewall read/write/apply/rollback/verify", "no iptables-save",
        "no iptables-restore", "no real adapters", "no subprocess firewall calls",
        "no customer nat", "no customer firewall rules", "no production traffic",
        "usage automation", "abuse automation", "ui", "telegram",
    ]
    for token in required:
        assert token in bundle

    t = DOC.read_text()
    assert "normal -> over_tracking -> over_grace -> hard" in t
    assert "sustained miner-abuse hardens after about 3600 seconds" in t
    assert "farms-over alone must not harden" in t
    assert "worker-over alone must not harden" in t
    assert "all active customers in enabled lanes must be covered" in t
    assert "no silent skip is allowed" in t
