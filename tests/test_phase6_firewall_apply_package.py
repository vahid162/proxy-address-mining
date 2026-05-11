from mpf.services.firewall_apply_package_service import build_apply_package_report
from mpf.services.firewall_planner_service import build_plan


def _policy() -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": "open"}


def test_package_offline_flags_and_readiness() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    report = build_apply_package_report(plan)
    assert report.artifact_only is True
    assert report.inspection_only is True
    assert report.live_apply_allowed is False
    assert report.applyable is False
    assert report.readiness == "blocked_for_live_apply"


def test_package_includes_payload_and_contract_requirements() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}])
    report = build_apply_package_report(plan)
    assert report.planner_customer_source == "unknown"
    assert report.db_customer_input_loaded is False
    assert report.payload_sha256
    assert report.payload_line_count > 0
    assert report.apply_readiness_contract is not None
    assert report.apply_readiness_contract.restore_point_contract.restore_point_required is True
    assert report.apply_readiness_contract.lock_contract.lock_required_for_apply is True
    assert report.apply_readiness_contract.verify_contract.verify_required_after_apply is True
    assert report.apply_readiness_contract.rollback_contract.rollback_artifact_required is True


def test_package_safety_flags_and_deterministic_hash() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    r1 = build_apply_package_report(plan)
    r2 = build_apply_package_report(plan)
    assert r1.payload_sha256 == r2.payload_sha256
    assert r1.payload_line_count == r2.payload_line_count
    assert r1.safety_flags["live_firewall_read"] is False
    assert r1.safety_flags["live_firewall_write"] is False
    assert r1.safety_flags["iptables_save_executed"] is False
    assert r1.safety_flags["iptables_restore_executed"] is False
    assert r1.safety_flags["lock_acquired"] is False
    assert r1.safety_flags["restore_point_written"] is False
    assert r1.safety_flags["database_write"] is False
    assert r1.safety_flags["filesystem_write"] is False


def test_plan_error_visible_in_package_errors() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"customer_key": "x", "lane": "LTC", "port": 20001, "status": "active", "policy": _policy()}])
    report = build_apply_package_report(plan)
    assert report.applyable is False
    assert report.error_count > 0
