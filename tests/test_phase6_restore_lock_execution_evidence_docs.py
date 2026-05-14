from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase_status_current_state_restore_lock_controlled_boundary_only() -> None:
    text = _read("docs/PHASE_STATUS.md")
    assert "restore_lock_record_execution_allowed: controlled_boundary_only" in text


def test_phase_status_contains_controlled_execution_server_evidence() -> None:
    text = _read("docs/PHASE_STATUS.md")
    assert "### Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence" in text
    for marker in (
        "583 passed",
        "CONTROLLED_BOUNDARY_EXECUTED",
        "restore_point_id=1",
        "firewall_apply_id=1",
        "lock_acquired=true",
        "db_apply_record_written=true",
        "apply_decision=BLOCKED",
        "iptables_restore_executed=false",
        "customer_nat_changed=false",
        "customer_firewall_rules_changed=false",
        "production_traffic_changed=false",
    ):
        assert marker in text


def test_phase_status_controlled_execution_keeps_non_authorizing_scope() -> None:
    text = _read("docs/PHASE_STATUS.md")
    for marker in (
        "no firewall apply",
        "no iptables-restore",
        "no customer NAT/customer firewall rules",
        "no production traffic",
        "no usage automation",
        "no abuse automation",
        "no UI",
        "no Telegram",
    ):
        assert marker in text


def test_apply_gate_readiness_and_gate_review_remain_blocked_in_phase_status() -> None:
    text = _read("docs/PHASE_STATUS.md")
    assert "apply-gate-readiness: final_decision=BLOCKED" in text
    assert "gate-review: final_decision=BLOCKED; applyable=false; live_apply_allowed=false" in text


def test_remaining_phase_plan_aligned_with_controlled_execution_boundary() -> None:
    text = _read("docs/REMAINING_PHASE_PLAN.md")
    assert "executed once on farm5 under the accepted controlled boundary" in text
    assert "no uncontrolled restore point writes, lock acquisition, or DB apply writes" in text
    for marker in (
        "firewall apply",
        "iptables-restore",
        "customer NAT/customer firewall rules",
        "production traffic remain forbidden",
        "no usage automation",
        "no abuse automation before Phase 8",
        "no UI or Telegram",
    ):
        assert marker in text
