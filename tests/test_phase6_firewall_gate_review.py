from mpf.services.firewall_gate_review_service import build_gate_review_report
from mpf.services.firewall_planner_service import build_plan


def _plan():
    return build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])


def test_gate_review_core_flags_and_decision_states() -> None:
    report = build_gate_review_report(plan=_plan())
    assert report.inspection_only is True
    assert report.artifact_only is True
    assert report.live_apply_allowed is False
    assert report.applyable is False
    assert report.final_decision == "BLOCKED"
    assert set(report.allowed_decision_states) == {"BLOCKED", "READY_FOR_FUTURE_GATE_REVIEW", "REJECTED_NEEDS_REWORK"}


def test_gate_review_has_required_summaries_and_safety_flags() -> None:
    report = build_gate_review_report(plan=_plan())
    assert report.evidence_summary
    assert report.risk_summary
    assert report.checklist_summary
    assert report.rollback_readiness_summary
    assert report.canary_readiness_summary
    assert report.abuse_requirement_summary
    assert report.safety_flags["live_firewall_read"] is False
    assert report.safety_flags["live_firewall_write"] is False
    assert report.safety_flags["iptables_save_executed"] is False
    assert report.safety_flags["iptables_restore_executed"] is False
    assert report.safety_flags["lock_acquired"] is False
    assert report.safety_flags["database_write"] is False
    assert report.safety_flags["filesystem_write"] is False


def test_gate_review_rows_are_deterministic() -> None:
    report = build_gate_review_report(plan=_plan())
    assert [r.risk_id for r in report.risks] == ["R-001", "R-002", "R-003"]
    assert [c.key for c in report.checklist] == ["phase_gate", "evidence_bundle", "risk_matrix", "config_source_warning"]
