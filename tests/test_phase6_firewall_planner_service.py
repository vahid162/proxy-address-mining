from __future__ import annotations

from mpf.services.firewall_planner_service import build_plan


def _valid_policy() -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": "open"}


def test_empty_active_customer_set_produces_valid_no_customer_plan() -> None:
    result = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    assert result.applyable is True
    assert any(c.object_id == "no_active_customers" for c in result.changes)


def test_active_deleted_and_paused_handling() -> None:
    result = build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[
            {"customer_key": "a", "lane": "BTC", "port": 20001, "status": "active", "policy": _valid_policy()},
            {"customer_key": "d", "lane": "BTC", "port": 20002, "status": "deleted"},
            {"customer_key": "p", "lane": "BTC", "port": 20003, "status": "paused"},
        ],
    )
    assert "a" in result.customer_coverage
    assert all(r.customer_key != "d" for r in result.rules)
    assert any(w.code == "inactive_placeholder" for w in result.warnings)


def test_collisions_and_exposure_make_plan_not_applyable() -> None:
    result = build_plan(
        lanes=[
            {"name": "BTC", "enabled": True, "backend_port": 60010},
            {"name": "BTC2", "enabled": True, "backend_port": 60010},
        ],
        customers=[
            {"customer_key": "a", "lane": "BTC", "port": 20001, "status": "active", "policy": _valid_policy()},
            {"customer_key": "b", "lane": "BTC", "port": 20001, "status": "active", "policy": _valid_policy()},
        ],
        backend_exposed=True,
    )
    assert result.applyable is False
    codes = {e.code for e in result.errors}
    assert {"lane_backend_collision", "customer_port_collision", "backend_exposure"} <= codes


def test_customer_port_collision_with_backend_port_is_error() -> None:
    result = build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[{"customer_key": "x", "lane": "BTC", "port": 60010, "status": "active", "policy": _valid_policy()}],
    )
    assert result.applyable is False
    assert any(e.code == "customer_backend_port_collision" for e in result.errors)


def test_active_customer_on_disabled_lane_is_error_and_no_intent() -> None:
    result = build_plan(
        lanes=[{"name": "BTC", "enabled": False, "backend_port": 60010}],
        customers=[{"customer_key": "x", "lane": "BTC", "port": 20001, "status": "active", "policy": _valid_policy()}],
    )
    assert result.applyable is False
    assert any(e.code == "customer_disabled_lane" for e in result.errors)
    assert all(r.customer_key != "x" for r in result.rules)


def test_active_customer_on_unknown_lane_is_error_and_no_intent() -> None:
    result = build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[{"customer_key": "x", "lane": "LTC", "port": 20001, "status": "active", "policy": _valid_policy()}],
    )
    assert result.applyable is False
    assert any(e.code == "customer_unknown_lane" for e in result.errors)
    assert all(r.customer_key != "x" for r in result.rules)


def test_active_customer_missing_policy_is_error_and_no_intent() -> None:
    result = build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[{"customer_key": "x", "lane": "BTC", "port": 20001, "status": "active"}],
    )
    assert result.applyable is False
    assert any(e.code == "missing_current_policy" for e in result.errors)
    assert all(r.customer_key != "x" for r in result.rules)


def test_active_customer_incomplete_policy_is_error_and_no_intent() -> None:
    result = build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[{"customer_key": "x", "lane": "BTC", "port": 20001, "status": "active", "policy": {"miners": 1}}],
    )
    assert result.applyable is False
    assert any(e.code == "incomplete_current_policy" for e in result.errors)
    assert all(r.customer_key != "x" for r in result.rules)


def test_active_customer_with_enabled_lane_and_complete_policy_gets_intent() -> None:
    result = build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[{"customer_key": "x", "lane": "BTC", "port": 20001, "status": "active", "policy": _valid_policy()}],
    )
    assert result.applyable is True
    assert any(r.customer_key == "x" for r in result.rules)
