from __future__ import annotations

from mpf.repositories import firewall_planner_read_repo as repo


def test_firewall_planner_read_repo_loads_enabled_customer_ip_pins(monkeypatch):
    calls = []

    def fake_query_database(config, sql):
        calls.append(sql)
        if "from lanes" in sql:
            return type("R", (), {"ok": True, "rows": [{"name": "btc", "enabled": True, "backend_port": 60010}], "message": "OK"})()
        if "from customers" in sql:
            return type("R", (), {"ok": True, "rows": [{"id": 1, "customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "status": "active", "miners": 1, "farms": 1, "maxconn": 10, "rate_per_min": 60, "burst": 10, "ips_mode": "whitelist", "abuse_exempt": False, "abuse_exempt_reason": None, "abuse_exempt_until": None, "abuse_exempt_by": None}], "message": "OK"})()
        if "from customer_ip_pins" in sql:
            return type("R", (), {"ok": True, "rows": [{"customer_id": 1, "id": 11, "ip_cidr": "203.0.113.10/32", "enabled": True}, {"customer_id": 1, "id": 12, "ip_cidr": "198.51.100.1/32", "enabled": False}], "message": "OK"})()
        raise AssertionError(sql)

    monkeypatch.setattr(repo, "query_database", fake_query_database)
    loaded = repo.load_firewall_planner_input(type("Cfg", (), {})())
    assert loaded.ok is True
    assert "from customer_ip_pins" in calls[2]
    customer = loaded.customers[0]
    assert customer["ip_whitelist"] == ["203.0.113.10/32"]
    assert customer["ip_pin_identity"] == [{"id": 11, "ip_cidr": "203.0.113.10/32"}]
    assert len(customer["ip_pins"]) == 2
