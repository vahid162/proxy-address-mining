from pathlib import Path


def test_phase_status_phase8_evidence_and_boundary() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in text
    assert "current_working_phase: Phase 8 — Abuse 1h Core planning/readiness" in text
    assert "farm5 synced to 0.1.110" in text
    assert "/var/backups/mpf/source-before-zip-sync-20260515T192056Z" in text
    assert "701 passed" in text
    assert "current Phase 7 accepted / Phase 8 working safety gate passed" in text
    assert "accepted current phase gate is installed and verified" in text
    assert "no runtime gate opened" in text
    assert "runtime restrictions remain unchanged" in text
    assert "Phase 8 Abuse State-Machine Contract Boundary" in text
    assert "Phase 8 Abuse Evidence/Reporting Contract Boundary" in text
    assert "Missing evidence must be explicit and must not harden" in text
    assert "Stale evidence must be explicit and must not harden" in text
    assert "does not read live conntrack" in text
    assert "does not read live firewall counters" in text
    assert "does not read DB customers" in text
    assert "does not apply hard/soft blocks" in text
    assert "does not apply pause automation" in text
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip" in text
    assert "does not run an abuse runner" in text
    assert "does not write abuse_states" in text
    assert "does not write abuse_events" in text
    assert "does not apply hard/soft blocks" in text
    assert "does not apply pause automation" in text


def test_remaining_phase_plan_and_current_gate_docs() -> None:
    remaining = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "GitHub main repository version before this PR is 0.1.111" in remaining
    assert "Repository version after this PR is 0.1.112" in remaining
    assert "latest recorded farm5 sync evidence is 0.1.110" in remaining
    assert "Current target is Phase 8 abuse evidence/reporting contract package" in remaining
    assert "Next target after this PR is Phase 8 abuse dry-run evaluator package" in remaining
    assert "offline sync may be batched with PR #119 and the next Phase 8 dry-run evaluator PR" in remaining
    assert "No server sync evidence for 0.1.111 or 0.1.112 exists until operator syncs after merge" in remaining
    assert "No Phase 8 runtime automation is enabled by this PR" in remaining

    readme = Path("README.md").read_text(encoding="utf-8")
    index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    rules = Path("docs/AI_CODING_RULES.md").read_text(encoding="utf-8")

    assert "accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in readme
    assert "working_phase: Phase 8 — Abuse 1h Core planning/readiness" in readme
    assert "accepted_phase: Phase 6" not in readme

    assert "Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in index
    assert "Phase 8 — Abuse 1h Core planning/readiness" in index

    assert "accepted: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in rules
    assert "working: Phase 8 — Abuse 1h Core planning/readiness" in rules

    for text in (readme, index, rules):
        assert "production_traffic: none" in text
        assert "firewall_apply_allowed: no" in text
        assert "abuse_automation_allowed: no" in text
        assert "ui_allowed: no" in text
        assert "telegram_allowed: no" in text


def test_ai_phase8_task_state_machine_section() -> None:
    text = Path("docs/AI_PHASE_8_TASK.md").read_text(encoding="utf-8")
    assert "Current Phase 8 Step — Abuse State-Machine Contract" in text
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip" in text
    assert "does not run the abuse runner" in text
    assert "does not write abuse_states" in text
    assert "does not write abuse_events" in text
    assert "runtime implementation remains future-gated" in text
    assert "Current Phase 8 Step — Abuse Evidence/Reporting Contract" in text
    assert "no live evidence collection" in text
    assert "no DB reads" in text
    assert "no DB writes" in text
    assert "no abuse runner" in text
    assert "no hard/soft blocks" in text
    assert "no pause automation" in text
    assert "missing/stale evidence must be explicit and cannot harden" in text
    assert "abuse dry-run evaluator" in text
