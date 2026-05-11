from mpf.services.firewall_planner_service import build_plan


def _policy(ips_mode: str = "open") -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": ips_mode}


def test_base_chain_intents_present() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    chains = {(c.table, c.chain) for c in p.chains}
    assert ("filter", "MPF_INPUT") in chains
    assert ("nat", "MPF_NAT_PRE") in chains
    assert ("filter", "MPFL_BTC") in chains


def test_active_customer_generates_structured_rule_intents() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy("whitelist")}])
    kinds = {r.rule_kind for r in p.rules if r.customer_key == "c1"}
    assert {"customer_dispatch", "customer_connlimit_reject", "customer_hashlimit_reject", "customer_accounting_in", "customer_accounting_out", "customer_nat_redirect", "customer_whitelist_allow"} <= kinds
    assert p.accounting_coverage["c1"] is True


def test_deleted_or_paused_no_forwarding_nat() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"customer_key": "d", "lane": "BTC", "port": 1, "status": "deleted"}, {"customer_key": "p", "lane": "BTC", "port": 2, "status": "paused"}])
    assert all(r.customer_key not in {"d", "p"} for r in p.rules)
