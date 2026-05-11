from mpf.services.firewall_apply_contract_service import build_apply_readiness_contract
from mpf.services.firewall_planner_service import build_plan
from mpf.services.firewall_restore_payload_renderer import render_restore_contract


def _policy() -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": "open"}


def test_apply_contract_offline_flags_and_readiness() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    restore = render_restore_contract(plan)
    c = build_apply_readiness_contract(plan, restore)
    assert c.artifact_only is True
    assert c.live_apply_allowed is False
    assert c.applyable is False
    assert c.readiness == "blocked_for_live_apply"


def test_restore_lock_verify_rollback_contract_requirements() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}])
    restore = render_restore_contract(plan)
    c = build_apply_readiness_contract(plan, restore)
    assert c.restore_point_contract.restore_point_required is True
    assert c.restore_point_contract.filesystem_write_allowed is False
    assert c.restore_point_contract.database_write_allowed is False
    assert c.lock_contract.firewall_lock_path == "/run/mpf-firewall.lock"
    assert c.lock_contract.lock_acquire_allowed_now is False
    assert c.verify_contract.verify_required_after_apply is True
    assert c.verify_contract.live_verify_allowed_now is False
    assert c.rollback_contract.rollback_artifact_required is True
    assert c.rollback_contract.rollback_execution_allowed_now is False
    assert c.rollback_contract.rollback_must_not_guess_from_current_db is True


def test_safety_flags_remain_offline_and_no_writes() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    c = build_apply_readiness_contract(plan, render_restore_contract(plan))
    assert c.safety_flags["live_firewall_read"] is False
    assert c.safety_flags["live_firewall_write"] is False
    assert c.safety_flags["iptables_save_executed"] is False
    assert c.safety_flags["iptables_restore_executed"] is False
    assert c.safety_flags["lock_acquired"] is False
    assert c.safety_flags["database_write"] is False
    assert c.safety_flags["filesystem_write"] is False


def test_plan_errors_keep_applyable_false_even_if_renderable_false() -> None:
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"customer_key": "x", "lane": "LTC", "port": 20001, "status": "active", "policy": _policy()}])
    restore = render_restore_contract(plan)
    c = build_apply_readiness_contract(plan, restore)
    assert restore.renderable is False
    assert c.applyable is False
    assert len(c.errors) > 0
