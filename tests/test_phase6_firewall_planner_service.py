from __future__ import annotations

from mpf.services.firewall_planner_service import build_plan


def test_empty_active_customer_set_produces_valid_no_customer_plan() -> None:
    result = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    assert result.applyable is True
    assert any(c.object_id == "no_active_customers" for c in result.changes)


def test_active_deleted_and_paused_handling() -> None:
    result = build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[
            {"customer_key": "a", "lane": "BTC", "port": 20001, "status": "active"},
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
            {"customer_key": "a", "lane": "BTC", "port": 20001, "status": "active"},
            {"customer_key": "b", "lane": "BTC", "port": 20001, "status": "active"},
        ],
        backend_exposed=True,
    )
    assert result.applyable is False
    codes = {e.code for e in result.errors}
    assert {"lane_backend_collision", "customer_port_collision", "backend_exposure"} <= codes
