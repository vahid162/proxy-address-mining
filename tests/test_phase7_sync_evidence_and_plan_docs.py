from pathlib import Path


def test_phase_status_records_farm5_0_1_104_sync_evidence() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "synced to 0.1.104" in text
    assert "673 passed" in text
    assert "/var/backups/mpf/source-before-zip-sync-20260515T155057Z" in text
    assert "ai_phase7_task_present: true" in text
    assert "blockers: []" in text
    assert "no runtime gate opened" in text
    assert "runtime restrictions remain unchanged" in text


def test_remaining_phase_plan_active_wording() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "GitHub main repository version before this PR is 0.1.104" in text
    assert "Repository version after this PR is 0.1.105" in text
    assert "latest recorded farm5 sync evidence is 0.1.104" in text
    assert "Phase 7 current target is Usage Accounting service-contract package" in text
    assert "Next target after this PR is Policy/Reject Accounting service contracts" in text
    assert "Historical compatibility anchor" in text


def test_offline_sync_runbook_venv_path() -> None:
    text = Path("docs/OFFLINE_SYNC_RUNBOOK.md").read_text(encoding="utf-8")
    assert "/opt/mpf-py-src/.venv/bin/python -m pytest -q" in text
    assert "/opt/mpf-py-venv/bin/python -m pytest -q" not in text
