from pathlib import Path


def test_phase6_e3_acceptance_doc_exists():
    assert Path("docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md").exists()


def test_phase_status_current_state_unchanged():
    text = Path("docs/PHASE_STATUS.md").read_text()
    expected = """## Current State

```text
current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5
current_working_phase: Phase 8 — Abuse 1h Core planning/readiness
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
```"""
    assert expected in text


def test_phase6_e3_accepted_block_location_and_next_step():
    text = Path("docs/PHASE_STATUS.md").read_text()
    assert "### Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist" in text
    assert "version accepted on farm5: 0.1.70" in text
    accepted_start = text.index("## Accepted Server Results")
    warning_start = text.index("## Current Server Warning", accepted_start)
    accepted_block = text[accepted_start:warning_start]
    assert "### Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist" in accepted_block
    assert "Future dedicated Phase 6 apply gate remains not accepted and not authorized." in text


def test_index_contains_e3_acceptance_doc_in_required_sections():
    idx = Path("docs/INDEX.md").read_text()
    assert "16. `docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md`" in idx
    assert "12. `docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md`" in idx
    assert "docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md" in idx


def test_no_doc_authorizes_live_apply_or_related_actions_now():
    docs = [
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md",
    ]
    text = "\n".join(Path(p).read_text().lower() for p in docs)
    forbidden = [
        "live apply is authorized",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "db apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
    ]
    for token in forbidden:
        assert token not in text


def test_abuse_invariant_preserved_in_e3_acceptance_doc():
    text = Path("docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md").read_text()
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip is allowed" in text


def test_no_stale_e3_next_step_wording_in_readme_and_ai_phase6_task():
    readme = Path("README.md").read_text()
    ai_task = Path("docs/AI_PHASE_6_TASK.md").read_text()

    assert "with Phase 6-E3 isolated/non-production next step" not in readme
    assert "After Phase 6-E1 acceptance, the next planned work is Phase 6-E2" not in readme
    assert "Apply Slice 3 and Apply Slice 4 are server-synced and accepted only as documentation/test-only boundaries" in readme
    assert "with Phase 6-G documentation/test-only non-authorizing next step" not in readme

    assert "Next safe work now is Phase 6-E3" not in ai_task
    assert "Next safe work is Phase 6-E3" not in ai_task
    assert "Phase 6-G is accepted as controlled live apply gate planning / pre-apply review only" in ai_task
