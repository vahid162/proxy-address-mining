from pathlib import Path


def test_phase_status_contains_0_1_120_sync_evidence() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "Phase 8 farm5 0.1.120 Operator Dry-Run Package Sync Evidence" in text
    assert "server version after sync: 0.1.120" in text
    assert "synced to 0.1.120" in text
    assert "pytest: 741 passed in 85.74s" in text
    assert "/var/backups/mpf/source-before-zip-sync-20260516T134158Z" in text
    assert "production_traffic: none" in text
    assert "firewall_apply_allowed: no" in text
    assert "abuse_automation_allowed: no" in text
    assert "no MPF/customer IPv4 firewall references detected" in text
    assert "no MPF/customer IPv6 firewall references detected" in text
    assert "This evidence does not accept Phase 8." in text
    assert "It does not claim controlled worker dry-run evidence has been collected." in text
    assert "It does not authorize background worker start." in text
    assert "It does not authorize scheduler/timer." in text
    assert "It does not authorize abuse runner." in text
    assert "It does not authorize production DB execution." in text
    assert "It does not authorize firewall apply." in text
    assert "It does not authorize customer NAT/customer firewall rules." in text
    assert "It does not authorize hard/soft blocks." in text
    assert "It does not authorize pause automation." in text
    assert "It does not authorize UI or Telegram." in text
    assert "It does not authorize production traffic." in text


def test_remaining_plan_targets_updated() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "GitHub main repository version before this PR is 0.1.121" in text
    assert "Repository version after this PR is 0.1.122" in text
    assert "latest recorded farm5 sync evidence is 0.1.121" in text
    assert "Current target is Phase 8 final Abuse 1h acceptance readiness/review" in text
    assert "Next target after this PR is Phase 8 final Abuse 1h acceptance, but only after this PR is merged and 0.1.122 is synced/tested on farm5" in text
    assert "14. Phase 8 farm5 controlled worker dry-run evidence collection preparation — done in 0.1.121 and synced/tested on farm5" in text
    assert "16. Phase 8 final Abuse 1h acceptance readiness/review — current target in 0.1.122" in text
    assert "17. Phase 8 final Abuse 1h acceptance — next after 0.1.122 sync/test" in text
