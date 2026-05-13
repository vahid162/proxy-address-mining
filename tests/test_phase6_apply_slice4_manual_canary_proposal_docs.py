from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_slice4_doc_exists_and_status() -> None:
    text = _read("docs/PHASE_6_APPLY_SLICE_4_MANUAL_CANARY_APPLY_GATE_PROPOSAL.md")
    assert "Status: planned, documentation/test-only, non-authorizing" in text


def test_phase_status_current_state_unchanged_and_slice4_not_accepted() -> None:
    phase = _read("docs/PHASE_STATUS.md")
    assert "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5" in phase
    assert "current_working_phase: Phase 6 — Firewall Planner" in phase
    assert "### Phase 6 Apply Slice 4" not in phase
    assert "Next planned step is server sync/review for Slice 3 and Slice 4 documentation/test-only boundaries." in phase


def test_index_and_ai_task_have_batch_sync_next_step() -> None:
    assert "docs/PHASE_6_APPLY_SLICE_4_MANUAL_CANARY_APPLY_GATE_PROPOSAL.md" in _read("docs/INDEX.md")
    assert "Batch server sync/review for Slice 3 and Slice 4 documentation/test-only boundaries." in _read("docs/AI_PHASE_6_TASK.md")


def test_docs_do_not_authorize_runtime_actions_now_and_abuse_invariant_preserved() -> None:
    files = [
        "docs/PHASE_6_APPLY_SLICE_4_MANUAL_CANARY_APPLY_GATE_PROPOSAL.md",
        "docs/PHASE_STATUS.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/AI_PHASE_6_TASK.md",
        "README.md",
        "AGENTS.md",
        "docs/AI_CODING_RULES.md",
        "docs/INDEX.md",
    ]
    text = "\n".join(_read(p).lower() for p in files)
    assert "does not authorize" in text
    for forbidden in [
        "manual canary apply is authorized now",
        "no-customer apply is authorized now",
        "live firewall read is authorized now",
        "iptables-save is authorized now",
        "iptables-restore is authorized now",
        "real adapters are authorized now",
        "subprocess firewall calls are authorized now",
        "restore point writes are authorized now",
        "lock acquisition is authorized now",
        "db apply writes are authorized now",
        "db apply records are authorized now",
        "migrations are authorized now",
        "customer nat redirects are authorized now",
        "customer firewall rules are authorized now",
        "production traffic is authorized now",
        "usage automation is authorized now",
        "abuse automation is authorized now",
        "ui is authorized now",
        "telegram is authorized now",
    ]:
        assert forbidden not in text
    assert "normal -> over_tracking -> over_grace -> hard" in text
