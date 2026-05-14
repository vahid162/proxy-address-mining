from mpf.services.firewall_gate_review_service import build_gate_review_report
from mpf.services.firewall_planner_service import build_plan


def _plan(source: str = "db_readonly"):
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    p.planner_customer_source = source
    p.db_customer_input_loaded = source == "db_readonly"
    return p


def test_gate_review_core_flags_and_decision_states() -> None:
    report = build_gate_review_report(plan=_plan())
    assert report.inspection_only is True
    assert report.artifact_only is True
    assert report.live_apply_allowed is False
    assert report.applyable is False
    assert report.final_decision == "BLOCKED"
    assert report.apply_gate_readiness_summary["final_decision"] == "BLOCKED"
    assert set(report.allowed_decision_states) == {"BLOCKED", "READY_FOR_FUTURE_GATE_REVIEW", "REJECTED_NEEDS_REWORK"}
    live = report.live_snapshot_read_summary
    assert live["component"] == "firewall_live_snapshot_read"
    assert live["final_decision"] == "BLOCKED"
    assert live["authorization_status"] == "NOT_AUTHORIZED"
    for key in (
        "live_firewall_read_executed",
        "iptables_save_executed",
        "subprocess_executed",
        "firewall_mutation",
        "db_mutation",
        "customer_nat_changed",
        "customer_firewall_rules_changed",
        "production_traffic_changed",
    ):
        assert live[key] is False


def test_gate_review_risk_ids_and_summary_are_deterministic() -> None:
    report = build_gate_review_report(plan=_plan())
    assert [r.risk_id for r in report.risks] == [f"R-{i:03d}" for i in range(1, 19)]
    assert report.risk_summary == {"total": 18, "critical": 9, "high": 6, "medium": 3, "low": 0, "blockers": 9, "warnings": 9}


def test_gate_review_contains_key_risks() -> None:
    report = build_gate_review_report(plan=_plan())
    titles = {r.title for r in report.risks}
    assert "Backend direct external exposure" in titles
    assert "Internal backend reachability failure" in titles
    assert "Hidden fallback from DB-backed input to config-only" in titles
    assert "Final decision/verdict accidentally OK while apply is forbidden" in titles
    assert "applyable accidentally true while apply is forbidden" in titles
    assert "Abuse coverage weakened" in titles
    assert "Public v2rayA UI exposure" in titles
    assert "Public backend exposure" in titles


def test_db_readonly_source_has_no_config_only_warning() -> None:
    report = build_gate_review_report(plan=_plan("db_readonly"))
    item = next(c for c in report.checklist if c.key == "config_source_warning")
    assert item.status == "PASS"
    assert report.checklist_summary["warn"] == 0


def test_config_only_source_has_warning() -> None:
    report = build_gate_review_report(plan=_plan("config_only"))
    item = next(c for c in report.checklist if c.key == "config_source_warning")
    assert item.status == "WARN"
    assert report.checklist_summary["warn"] == 1


def test_gate_review_contains_live_snapshot_read_summary() -> None:
    report = build_gate_review_report(plan=_plan())
    assert report.final_decision == "BLOCKED"
    live = report.live_snapshot_read_summary
    assert live["authorization_status"] == "NOT_AUTHORIZED"
    assert live["live_firewall_read_executed"] is False
    assert live["iptables_save_executed"] is False
    assert live["subprocess_executed"] is False
    assert isinstance(report.live_snapshot_read_summary, dict)


def test_gate_review_compacts_no_customer_scaffold_summary_keys() -> None:
    full_report = {
        "component": "firewall_no_customer_apply_scaffold",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_AUTHORIZED_FOR_APPLY",
        "execution_allowed": False,
        "apply_decision": "BLOCKED",
        "verify_decision": "BLOCKED",
        "rollback_decision": "BLOCKED",
    }
    report = build_gate_review_report(plan=_plan(), no_customer_apply_scaffold=full_report)
    summary = report.apply_gate_readiness_summary["no_customer_apply_scaffold_summary"]
    assert summary["no_customer_apply_scaffold_present"] is True
    assert summary["no_customer_apply_scaffold_final_decision"] == "BLOCKED"
    assert summary["no_customer_apply_scaffold_authorization_status"] == "NOT_AUTHORIZED_FOR_APPLY"
    assert summary["no_customer_apply_scaffold_execution_allowed"] is False
    assert summary["no_customer_apply_scaffold_apply_decision"] == "BLOCKED"
    assert summary["no_customer_apply_scaffold_verify_decision"] == "BLOCKED"
    assert summary["no_customer_apply_scaffold_rollback_decision"] == "BLOCKED"
    assert "component" not in summary
