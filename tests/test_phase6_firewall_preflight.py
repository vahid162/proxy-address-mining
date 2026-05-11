from mpf.services.firewall_planner_service import build_plan
from mpf.services.firewall_preflight_service import build_preflight_report
from mpf.services.firewall_snapshot_parser import parse_iptables_save_text
from mpf.services.firewall_rollback_artifact_renderer import render_rollback_artifact_from_snapshot


def _policy() -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": "open"}


def test_preflight_core_flags_and_blocked_verdict() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    report = build_preflight_report(plan)
    assert report.artifact_only is True
    assert report.inspection_only is True
    assert report.live_apply_allowed is False
    assert report.applyable is False
    assert report.readiness == "blocked_for_live_apply"
    assert report.final_verdict == "BLOCKED"


def test_preflight_optional_rollback_snapshot_statuses() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}])
    no_snap = build_preflight_report(plan)
    assert no_snap.rollback_artifact_present is False
    snap = parse_iptables_save_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n")
    rollback = render_rollback_artifact_from_snapshot(snap, source="offline_snapshot_file")
    with_snap = build_preflight_report(plan, rollback_artifact=rollback)
    assert with_snap.rollback_artifact_present is True
    assert with_snap.rollback_artifact_renderable is True
    assert with_snap.restore_point_required is True
    assert with_snap.lock_required_for_apply is True
    assert with_snap.verify_required_after_apply is True
    assert with_snap.rollback_artifact_required is True


def test_preflight_safety_flags_and_deterministic_order() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    r1 = build_preflight_report(plan)
    r2 = build_preflight_report(plan)
    assert [c.key for c in r1.checks] == [c.key for c in r2.checks]
    assert r1.safety_flags["live_firewall_read"] is False
    assert r1.safety_flags["live_firewall_write"] is False
    assert r1.safety_flags["iptables_save_executed"] is False
    assert r1.safety_flags["iptables_restore_executed"] is False
    assert r1.safety_flags["lock_acquired"] is False
    assert r1.safety_flags["database_write"] is False
    assert r1.safety_flags["filesystem_write"] is False
