from mpf.domain.firewall import FirewallLiveRuleSnapshot, FirewallLiveSnapshot
from mpf.services.firewall_planner_service import build_plan


def _policy() -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": "open"}


def _plan(snapshot: FirewallLiveSnapshot | None = None):
    return build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[{"customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}],
        live_snapshot=snapshot,
    )


def test_every_rule_references_existing_chain_and_nat_uses_nat_chain() -> None:
    p = _plan()
    chains = {(c.table, c.chain) for c in p.chains}
    for r in p.rules:
        assert (r.table, r.chain) in chains
    nat = [r for r in p.rules if r.rule_kind == "customer_nat_redirect"][0]
    assert (nat.table, nat.chain) == ("nat", "MPF_NAT_PRE")
    assert nat.action_json["target_backend"] == 60010


def test_missing_and_unexpected_chain_detected() -> None:
    p = _plan(FirewallLiveSnapshot(chains=[("filter", "MPF_INPUT"), ("filter", "MPF_EXTRA")], rules=[]))
    assert any(c.object_type == "chain" and c.kind == "create" for c in p.changes)
    assert any(w.code == "unexpected_mpf_chain" for w in p.warnings)


def test_missing_and_unexpected_rule_and_stale_deleted_detected() -> None:
    snap = FirewallLiveSnapshot(
        chains=[("filter", "MPF_INPUT"), ("filter", "MPF_CUSTOMERS"), ("filter", "MPF_GUARD"), ("filter", "MPF_ACCT_IN"), ("filter", "MPF_ACCT_OUT"), ("nat", "MPF_NAT_PRE"), ("nat", "MPF_NAT_POST"), ("filter", "MPFL_BTC"), ("filter", "MPFC_20001"), ("filter", "MPFO_20001")],
        rules=[
            FirewallLiveRuleSnapshot(rule_key="mpf:legacy:extra", table="filter", chain="MPF_CUSTOMERS"),
            FirewallLiveRuleSnapshot(rule_key="mpf:deleted:c9:customer_nat_redirect", table="nat", chain="MPF_NAT_PRE"),
        ],
    )
    p = _plan(snap)
    assert any(c.object_type == "rule" and c.kind == "create" for c in p.changes)
    assert any(w.code == "unexpected_mpf_rule" for w in p.warnings)
    assert any(w.code == "stale_deleted_customer_rule" for w in p.warnings)


def test_nat_target_mismatch_is_error_and_not_applyable() -> None:
    snap = FirewallLiveSnapshot(
        chains=[("filter", "MPF_INPUT"), ("filter", "MPF_CUSTOMERS"), ("filter", "MPF_GUARD"), ("filter", "MPF_ACCT_IN"), ("filter", "MPF_ACCT_OUT"), ("nat", "MPF_NAT_PRE"), ("nat", "MPF_NAT_POST"), ("filter", "MPFL_BTC"), ("filter", "MPFC_20001"), ("filter", "MPFO_20001")],
        rules=[FirewallLiveRuleSnapshot(rule_key="mpf:c1:customer_nat_redirect", table="nat", chain="MPF_NAT_PRE", action_json={"target_backend": 60011}, match_json={"port": 20001})],
    )
    p = _plan(snap)
    assert p.applyable is False
    assert any(e.code == "nat_target_mismatch" for e in p.errors)
