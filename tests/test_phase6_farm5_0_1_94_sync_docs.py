from pathlib import Path


def test_phase_status_current_state_unchanged_and_sync_evidence_present():
    t = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5" in t
    assert "farm5 synced to 0.1.94" in t
    assert "631 passed" in t
    assert "/var/backups/mpf/source-before-zip-sync-20260515T070627Z" in t


def test_remaining_plan_and_ai_phase_task_updated():
    r = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "latest recorded farm5 sync evidence is 0.1.94" in r
    assert "Controlled no-customer runtime execution evidence — current next target" in r

    a = Path("docs/AI_PHASE_6_TASK.md").read_text(encoding="utf-8")
    assert "latest recorded farm5 sync evidence is 0.1.94" in a
    assert "mpf firewall no-customer-runtime-execution-evidence" in a
    assert "normal -> over_tracking -> over_grace -> hard" in a
