from mpf.services.firewall_planner_service import build_plan
from mpf.services.firewall_restore_payload_renderer import render_restore_contract


def _policy(ips_mode: str = "open") -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": ips_mode}


def test_render_empty_deterministic_sections() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    c = render_restore_contract(p)
    assert c.renderable is True
    assert "*filter" in c.restore_payload.payload and "*nat" in c.restore_payload.payload
    assert c.restore_payload.payload.count("COMMIT") == 2


def test_active_customer_renders_nat_redirect_in_nat_pre() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}])
    c = render_restore_contract(p)
    assert "-A MPF_NAT_PRE -p tcp --dport 20001" in c.restore_payload.payload
    assert '--comment "mpf:c1:customer_nat_redirect"' in c.restore_payload.payload


def test_payload_hash_and_ordering_deterministic() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}])
    c1 = render_restore_contract(p)
    c2 = render_restore_contract(p)
    assert c1.restore_payload.payload == c2.restore_payload.payload
    assert c1.restore_payload.payload_sha256 == c2.restore_payload.payload_sha256


def test_paused_placeholder_is_comment_only() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "p1", "lane": "BTC", "port": 21001, "status": "paused"}])
    c = render_restore_contract(p)
    assert "# mpf:planned-only customer_pause_reject" in c.restore_payload.payload


def test_validation_fails_for_plan_errors() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"customer_key": "x", "lane": "LTC", "port": 20001, "status": "active", "policy": _policy()}])
    c = render_restore_contract(p)
    assert c.renderable is False
    assert c.restore_payload is None
