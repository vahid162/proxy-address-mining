from mpf.domain.firewall import FirewallPlanMessage
from mpf.services.firewall_evidence_service import build_evidence_bundle_report
from mpf.services.firewall_planner_service import build_plan
from mpf.services.firewall_rollback_artifact_renderer import render_rollback_artifact_from_snapshot
from mpf.services.firewall_snapshot_parser import parse_iptables_save_text


def _policy() -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": "open"}


def test_evidence_bundle_core_flags() -> None:
    report = build_evidence_bundle_report(build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[]))
    assert report.artifact_only is True
    assert report.inspection_only is True
    assert report.live_apply_allowed is False
    assert report.applyable is False
    assert report.readiness == "blocked_for_live_apply"
    assert report.final_verdict == "BLOCKED"


def test_evidence_bundle_sections_and_summaries() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}])
    report = build_evidence_bundle_report(plan)
    assert report.plan_summary
    assert report.restore_summary
    assert report.apply_contract_summary
    assert report.package_summary
    assert report.preflight_summary
    assert [s.key for s in report.sections] == ["phase_gate", "planner", "diff_contract", "doctor_contract", "restore_payload", "apply_contract", "apply_package", "rollback_artifact", "preflight", "safety_flags", "abuse_future_requirement"]


def test_evidence_rollback_presence_depends_on_explicit_snapshot() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    no_rollback = build_evidence_bundle_report(plan)
    assert no_rollback.rollback_summary["present"] is False
    rollback = render_rollback_artifact_from_snapshot(parse_iptables_save_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n"), source="offline_snapshot_file")
    with_rollback = build_evidence_bundle_report(plan, rollback_artifact=rollback)
    assert with_rollback.rollback_summary["present"] is True


def test_evidence_dedupes_messages_and_safety_flags() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    plan.warnings.append(FirewallPlanMessage(code="dup", message="same", severity="warning"))
    plan.warnings.append(FirewallPlanMessage(code="dup", message="same", severity="warning"))
    plan.errors.append(FirewallPlanMessage(code="e", message="same", severity="error"))
    plan.errors.append(FirewallPlanMessage(code="e", message="same", severity="error"))
    report = build_evidence_bundle_report(plan)
    assert len([w for w in report.warnings if w.code == "dup"]) == 1
    assert len([e for e in report.errors if e.code == "e"]) == 1
    assert report.safety_flags["live_firewall_read"] is False
    assert report.safety_flags["live_firewall_write"] is False
    assert report.safety_flags["iptables_save_executed"] is False
    assert report.safety_flags["iptables_restore_executed"] is False
    assert report.safety_flags["lock_acquired"] is False
    assert report.safety_flags["database_write"] is False
    assert report.safety_flags["filesystem_write"] is False


def test_evidence_includes_and_dedupes_rollback_messages() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    rollback = render_rollback_artifact_from_snapshot(parse_iptables_save_text(""), source="offline_snapshot_file")
    rollback.warnings.append(FirewallPlanMessage(code="rw", message="rollback warn", severity="warning"))
    rollback.warnings.append(FirewallPlanMessage(code="rw", message="rollback warn", severity="warning"))
    rollback.errors.append(FirewallPlanMessage(code="re", message="rollback err", severity="error"))
    rollback.errors.append(FirewallPlanMessage(code="re", message="rollback err", severity="error"))
    report = build_evidence_bundle_report(plan, rollback_artifact=rollback)
    assert len([w for w in report.warnings if w.code == "rw"]) == 1
    assert len([e for e in report.errors if e.code == "re"]) == 1
