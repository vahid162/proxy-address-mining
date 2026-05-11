from __future__ import annotations

from mpf.db import DBQueryResult
from mpf.repositories import firewall_planner_read_repo
from mpf.services import firewall_planner_service
from mpf.config import load_config
from tests.test_smoke import example_config_path


def test_db_repo_maps_lanes_customers_and_policy_fields(monkeypatch) -> None:
    cfg = load_config(example_config_path())

    def fake_query(config, sql):
        if "from lanes" in sql:
            return DBQueryResult(True, [{"name": "BTC", "enabled": "t", "backend_port": "60010"}], "OK")
        return DBQueryResult(
            True,
            [{
                "id": "1", "customer_key": "cust-1", "lane": "BTC", "port": "20001", "status": "active",
                "miners": "1", "farms": "2", "maxconn": "3", "rate_per_min": "4", "burst": "5", "ips_mode": "whitelist",
                "abuse_exempt": True, "abuse_exempt_reason": "maint", "abuse_exempt_until": "2030-01-01", "abuse_exempt_by": "ops",
            }],
            "OK",
        )

    monkeypatch.setattr(firewall_planner_read_repo, "query_database", fake_query)
    load = firewall_planner_read_repo.load_firewall_planner_input(cfg)
    assert load.ok is True
    assert load.lanes[0]["backend_port"] == 60010
    policy = load.customers[0]["policy"]
    assert policy["miners"] == 1
    assert policy["farms"] == 2
    assert policy["maxconn"] == 3
    assert policy["rate_per_min"] == 4
    assert policy["burst"] == 5
    assert policy["ips_mode"] == "whitelist"
    assert policy["abuse_exempt_reason"] == "maint"


def test_db_read_failure_is_not_silent_fallback(monkeypatch) -> None:
    cfg = load_config(example_config_path())

    monkeypatch.setattr(
        firewall_planner_read_repo,
        "query_database",
        lambda config, sql: DBQueryResult(False, [], "db unavailable"),
    )
    try:
        firewall_planner_service.build_plan_from_db(cfg)
        assert False
    except RuntimeError as exc:
        assert "failed to load lanes" in str(exc)
