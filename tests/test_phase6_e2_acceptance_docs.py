from pathlib import Path


def test_phase6_e2_acceptance_doc_exists():
    assert Path("docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md").exists()


def test_phase_status_current_state_unchanged():
    text = Path("docs/PHASE_STATUS.md").read_text()
    expected = """## Current State

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
```"""
    assert expected in text


def test_phase6_e2_accepted_and_e3_next_step_and_safety():
    docs = {
        p: Path(p).read_text()
        for p in [
            "docs/PHASE_STATUS.md",
            "docs/INDEX.md",
            "docs/AI_PHASE_6_TASK.md",
            "docs/FIREWALL.md",
            "docs/REMAINING_PHASE_PLAN.md",
            "docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md",
        ]
    }
    ps = docs["docs/PHASE_STATUS.md"]
    assert "### Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning" in ps
    assert "version accepted on farm5: 0.1.66" in ps
    assert "Future dedicated Phase 6 apply gate remains not accepted and not authorized" in ps
    assert "non-authorizing" in ps

    idx = docs["docs/INDEX.md"]
    assert "docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md" in idx

    forbidden = [
        "live apply is authorized",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "DB apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
    ]
    all_text = "\n".join(docs.values()).lower()
    for token in forbidden:
        assert token not in all_text


def test_abuse_invariant_preserved_in_e2_acceptance_doc():
    text = Path("docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md").read_text()
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip is allowed" in text


def test_e2_block_is_inside_accepted_server_results_not_after_forbidden_now():
    text = Path("docs/PHASE_STATUS.md").read_text()
    accepted_start = text.index("## Accepted Server Results")
    warning_start = text.index("## Current Server Warning", accepted_start)
    accepted_block = text[accepted_start:warning_start]
    assert "### Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning" in accepted_block

    forbidden_start = text.index("## What Is Forbidden Now")
    after_forbidden = text[forbidden_start:]
    assert "### Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning" not in after_forbidden
