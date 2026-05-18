from pathlib import Path


def test_phase_status_current_state_phase6_accepted_phase7_working() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    required = [
        "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5",
        "current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness",
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "live_snapshot_read_allowed: iptables_save_read_only",
        "restore_lock_record_execution_allowed: controlled_boundary_only",
        "farm5 synced to 0.1.100",
        "pytest during sync: 661 passed",
        "/var/backups/mpf/source-before-zip-sync-20260515T103836Z",
        "no runtime gate opened",
        "runtime restrictions remain unchanged",
    ]
    for item in required:
        assert item in text
