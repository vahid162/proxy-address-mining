from pathlib import Path


def test_phase_status_records_farm5_0_1_107_sync_evidence() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "synced to 0.1.107" in text
    assert "690 passed" in text
    assert "/var/backups/mpf/source-before-zip-sync-20260515T171232Z" in text
    assert "mpf phase7 doctor --output json final_verdict: OK" in text
    assert "all child reports blockers: []" in text
    assert "no runtime gate opened" in text
    assert "runtime restrictions remain unchanged" in text
    assert "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in text
    assert "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" in text


def test_remaining_phase_plan_active_wording() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "GitHub main repository version before this PR is 0.1.107" in text
    assert "Repository version after this PR is 0.1.108" in text
    assert "latest recorded farm5 sync evidence is 0.1.107" in text
    assert "0.1.105 and 0.1.106 were batched and superseded by 0.1.107 farm5 sync evidence" in text
    assert "Phase 7 current target is Phase 7 final acceptance readiness package" in text
    assert "Next target after this PR is Phase 7 operator acceptance / Phase 8 planning boundary" in text
    assert "no Phase 8 runtime automation is enabled by this PR" in text
    assert "farm5 batched offline sync for PR #113 + #114 + #115 is completed and evidenced at 0.1.107" in text
    assert "after this PR is merged, operator should perform a separate farm5 offline sync for 0.1.108 to verify the Phase 7 final acceptance readiness package" in text
    assert "after this PR is merged, operator should perform one batched offline sync for PR #113 + #114 + #115 together." not in text
    assert "Phase 7 remains report-only/service-contract/readiness only" in text


def test_offline_sync_runbook_venv_path() -> None:
    text = Path("docs/OFFLINE_SYNC_RUNBOOK.md").read_text(encoding="utf-8")
    assert "/opt/mpf-py-src/.venv/bin/python -m pytest -q" in text
    assert "/opt/mpf-py-venv/bin/python -m pytest -q" not in text
