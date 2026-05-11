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
    assert all(not (r.customer_key == "p" and r.rule_kind == "customer_nat_redirect") for r in p.rules)
    assert all(r.customer_key != "d" for r in p.rules)


def test_paused_and_expired_generate_placeholder_only() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "p1", "lane": "BTC", "port": 21001, "status": "paused"}, {"id": 2, "customer_key": "e1", "lane": "BTC", "port": 21002, "status": "expired"}])
    kinds = {r.rule_kind for r in p.rules}
    assert "customer_pause_reject" in kinds
    assert "customer_expired_reject" in kinds
    assert not any(r.rule_kind == "customer_nat_redirect" and r.customer_key in {"p1", "e1"} for r in p.rules)


def test_whitelist_missing_sources_warns_and_not_open() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "w1", "lane": "BTC", "port": 22001, "status": "active", "policy": _policy("whitelist")}])
    wl = [r for r in p.rules if r.customer_key == "w1" and r.rule_kind == "customer_whitelist_allow"][0]
    assert wl.action_json.get("whitelist_required") is True
    assert wl.match_json.get("sources") == []
    assert any(w.code == "whitelist_missing_sources" for w in p.warnings)


def test_open_customer_has_no_whitelist_intent() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "o1", "lane": "BTC", "port": 22002, "status": "active", "policy": _policy("open")}])
    assert all(r.rule_kind != "customer_whitelist_allow" for r in p.rules if r.customer_key == "o1")
