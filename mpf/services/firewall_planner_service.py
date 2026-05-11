from __future__ import annotations

from collections import Counter

from mpf.config import MPFConfig
from mpf.domain.firewall import FirewallChainIntent, FirewallLiveSnapshot, FirewallPlanChange, FirewallPlanMessage, FirewallPlanResult, FirewallRuleIntent
from mpf.repositories import firewall_planner_read_repo

_REQUIRED_POLICY_FIELDS = ("miners", "farms", "maxconn", "rate_per_min", "burst", "ips_mode")


def _policy_missing_or_incomplete(policy: dict | None) -> tuple[bool, list[str]]:
    if not policy:
        return True, list(_REQUIRED_POLICY_FIELDS)
    missing = [field for field in _REQUIRED_POLICY_FIELDS if policy.get(field) is None]
    return len(missing) > 0, missing


def _base_chains(plan: FirewallPlanResult, lanes: list[dict]) -> None:
    base = [("filter", "MPF_INPUT"), ("filter", "MPF_CUSTOMERS"), ("filter", "MPF_GUARD"), ("filter", "MPF_ACCT_IN"), ("filter", "MPF_ACCT_OUT"), ("nat", "MPF_NAT_PRE"), ("nat", "MPF_NAT_POST")]
    for idx, (table, chain) in enumerate(base):
        plan.chains.append(FirewallChainIntent(id=f"{table}:{chain}", table=table, chain=chain, owner="mpf", purpose="base", order=idx))
    for lane in lanes:
        if lane.get("enabled", False):
            lane_name = str(lane["name"])
            plan.chains.append(FirewallChainIntent(id=f"filter:MPFL_{lane_name}", table="filter", chain=f"MPFL_{lane_name}", owner="mpf", purpose="lane_dispatch", lane=lane_name, group="lane"))


def _offline_diff(plan: FirewallPlanResult, snapshot: FirewallLiveSnapshot | None) -> None:
    if snapshot is None:
        return
    desired_chains = {(c.table, c.chain) for c in plan.chains}
    live_chains = set(snapshot.chains)
    for missing in sorted(desired_chains - live_chains):
        plan.changes.append(FirewallPlanChange(kind="create", object_type="chain", object_id=f"{missing[0]}:{missing[1]}", detail="missing desired chain"))
    for extra in sorted([x for x in live_chains - desired_chains if x[1].startswith("MPF")]):
        plan.warnings.append(FirewallPlanMessage(code="unexpected_mpf_chain", message=f"unexpected MPF-owned chain in snapshot: {extra[0]}:{extra[1]}", severity="warning"))

    desired_rule_keys = [r.rule_key for r in plan.rules]
    for key, count in Counter(desired_rule_keys).items():
        if count > 1:
            plan.errors.append(FirewallPlanMessage(code="duplicate_rule_key", message=f"duplicate desired rule key: {key}", severity="error"))

    desired_rules = {r.rule_key: r for r in plan.rules}
    live_by_key = {r.rule_key: r for r in snapshot.rules}
    for key, desired in desired_rules.items():
        live = live_by_key.get(key)
        if live is None:
            plan.changes.append(FirewallPlanChange(kind="create", object_type="rule", object_id=key, detail="missing desired rule"))
            continue
        if desired.rule_kind == "customer_nat_redirect":
            desired_target = desired.action_json.get("target_backend")
            live_target = live.action_json.get("target_backend")
            if desired_target != live_target:
                plan.errors.append(FirewallPlanMessage(code="nat_target_mismatch", message=f"rule {key} NAT target mismatch desired={desired_target} live={live_target}", severity="error"))
        if desired.match_json != live.match_json or desired.action_json != live.action_json:
            plan.changes.append(FirewallPlanChange(kind="update", object_type="rule", object_id=key, detail="rule match/action drift"))
        else:
            plan.changes.append(FirewallPlanChange(kind="keep", object_type="rule", object_id=key, detail="rule already matches desired intent"))

    for extra in sorted([r for r in snapshot.rules if r.rule_key.startswith("mpf:") and r.rule_key not in desired_rules], key=lambda x: x.rule_key):
        code = "unexpected_mpf_rule"
        if ":deleted:" in extra.rule_key:
            code = "stale_deleted_customer_rule"
        plan.warnings.append(FirewallPlanMessage(code=code, message=f"unexpected MPF-owned rule in snapshot: {extra.rule_key}", severity="warning"))


def build_plan(*, lanes: list[dict], customers: list[dict], backend_exposed: bool = False, planner_customer_source: str = "unknown", db_customer_input_loaded: bool = False, live_snapshot: FirewallLiveSnapshot | None = None) -> FirewallPlanResult:
    plan = FirewallPlanResult(planner_customer_source=planner_customer_source, db_customer_input_loaded=db_customer_input_loaded)
    _base_chains(plan, lanes)

    known_lanes = {str(lane["name"]): lane for lane in lanes}
    enabled_lanes = [lane for lane in lanes if lane.get("enabled", False)]
    enabled_lane_names = {str(lane["name"]) for lane in enabled_lanes}
    backend_ports = [int(lane["backend_port"]) for lane in enabled_lanes]

    for port, count in Counter(backend_ports).items():
        if count > 1:
            plan.errors.append(FirewallPlanMessage(code="lane_backend_collision", message=f"backend_port collision: {port}", severity="error"))

    if backend_exposed:
        plan.errors.append(FirewallPlanMessage(code="backend_exposure", message="backend public exposure risk detected", severity="error"))

    active_customers = [c for c in customers if c.get("status") == "active"]
    for port, count in Counter(int(c["port"]) for c in active_customers).items():
        if count > 1:
            plan.errors.append(FirewallPlanMessage(code="customer_port_collision", message=f"customer port collision: {port}", severity="error"))
        if port in backend_ports:
            plan.errors.append(FirewallPlanMessage(code="customer_backend_port_collision", message=f"customer port collides with backend port: {port}", severity="error"))

    if not db_customer_input_loaded:
        plan.warnings.append(FirewallPlanMessage(code="planner_customer_source", message=f"planner_customer_source={planner_customer_source}; db_customer_input_loaded=false", severity="warning"))

    for lane in enabled_lanes:
        lane_name = str(lane["name"])
        backend_port = int(lane["backend_port"])
        plan.lane_backend_coverage.append(lane_name)
        plan.rules.append(FirewallRuleIntent(id=f"guard:{lane_name}", table="filter", chain="MPF_GUARD", rule_key=f"mpf:backend_guard:{lane_name}:{backend_port}", rule_kind="backend_guard", priority=10, lane=lane_name, backend_port=backend_port, safety_role="backend_guard", match_json={"dest_port": backend_port}, action_json={"policy": "block_external_preserve_internal"}, detail="backend guard intent only"))

    for customer in customers:
        status = customer.get("status")
        customer_key = str(customer.get("customer_key"))
        if status == "deleted":
            continue
        if status in {"paused", "expired"}:
            plan.warnings.append(FirewallPlanMessage(code="inactive_placeholder", message=f"customer {customer_key} status={status} is represented as non-active intent", severity="warning")); continue
        if status != "active":
            plan.warnings.append(FirewallPlanMessage(code="unsupported_status", message=f"customer {customer_key} has unsupported status={status}", severity="warning")); continue

        lane_name = str(customer["lane"])
        if lane_name not in known_lanes:
            plan.errors.append(FirewallPlanMessage(code="customer_unknown_lane", message=f"customer {customer_key} references unknown lane={lane_name}", severity="error")); continue
        if lane_name not in enabled_lane_names:
            plan.errors.append(FirewallPlanMessage(code="customer_disabled_lane", message=f"customer {customer_key} references disabled lane={lane_name}", severity="error")); continue

        policy = customer.get("policy")
        incomplete, missing = _policy_missing_or_incomplete(policy if isinstance(policy, dict) else None)
        if policy is None:
            plan.errors.append(FirewallPlanMessage(code="missing_current_policy", message=f"customer {customer_key} has no current policy", severity="error")); continue
        if incomplete:
            plan.errors.append(FirewallPlanMessage(code="incomplete_current_policy", message=f"customer {customer_key} current policy incomplete: missing={','.join(missing)}", severity="error")); continue

        cport = int(customer["port"])
        backend_port = int(known_lanes[lane_name]["backend_port"])
        plan.customer_coverage.append(customer_key)
        plan.affected_customers.append(customer_key)
        plan.customer_policy_references.append(f"{customer_key}:policy")
        plan.accounting_coverage[customer_key] = True
        plan.chains.extend([
            FirewallChainIntent(id=f"filter:MPFC_{cport}", table="filter", chain=f"MPFC_{cport}", owner="mpf", purpose="customer_filter", lane=lane_name, customer_key=customer_key, customer_port=cport, group="customer"),
            FirewallChainIntent(id=f"filter:MPFO_{cport}", table="filter", chain=f"MPFO_{cport}", owner="mpf", purpose="customer_policy", lane=lane_name, customer_key=customer_key, customer_port=cport, group="customer"),
        ])
        kinds = ["customer_dispatch", "customer_connlimit_reject", "customer_hashlimit_reject", "customer_accounting_in", "customer_accounting_out", "customer_nat_redirect"]
        if policy.get("ips_mode") == "whitelist":
            kinds.append("customer_whitelist_allow")
        for i, kind in enumerate(kinds):
            is_nat = kind == "customer_nat_redirect"
            plan.rules.append(FirewallRuleIntent(id=f"{customer_key}:{kind}", table="nat" if is_nat else "filter", chain="MPF_NAT_PRE" if is_nat else f"MPFC_{cport}", rule_key=f"mpf:{customer_key}:{kind}", rule_kind=kind, priority=100 + i, lane=lane_name, customer_key=customer_key, customer_id=customer.get("id"), customer_port=cport, backend_port=backend_port, accounting_role="customer_usage" if "accounting" in kind else None, match_json={"port": cport}, action_json={"target_backend": backend_port} if is_nat else {"intent": kind}, detail=f"planned intent {kind}"))
        plan.changes.append(FirewallPlanChange(kind="create", object_type="rule_intent", object_id=f"customer:{customer_key}", detail="planned structured customer intents"))

    desired_chain_keys = {(c.table, c.chain) for c in plan.chains}
    for r in plan.rules:
        if (r.table, r.chain) not in desired_chain_keys:
            plan.errors.append(FirewallPlanMessage(code="rule_chain_missing", message=f"rule {r.rule_key} references missing chain {r.table}:{r.chain}", severity="error"))

    if not active_customers:
        plan.changes.append(FirewallPlanChange(kind="keep", object_type="planner", object_id="no_active_customers", detail="no active customer forwarding intents"))

    _offline_diff(plan, live_snapshot)
    plan.finalize()
    return plan


def build_plan_from_db(config: MPFConfig) -> FirewallPlanResult:
    load = firewall_planner_read_repo.load_firewall_planner_input(config)
    if not load.ok:
        raise RuntimeError(load.message)
    return build_plan(lanes=load.lanes, customers=load.customers, planner_customer_source="db_readonly", db_customer_input_loaded=True)


def build_plan_from_db_with_live_snapshot(config: MPFConfig, snapshot: FirewallLiveSnapshot) -> FirewallPlanResult:
    load = firewall_planner_read_repo.load_firewall_planner_input(config)
    if not load.ok:
        raise RuntimeError(load.message)
    return build_plan(
        lanes=load.lanes,
        customers=load.customers,
        planner_customer_source="db_readonly",
        db_customer_input_loaded=True,
        live_snapshot=snapshot,
    )


def build_plan_from_config(config: MPFConfig) -> FirewallPlanResult:
    lanes = [{"name": lane_name, "enabled": lane.enabled, "backend_port": lane.backend_port} for lane_name, lane in sorted(config.lanes.items())]
    plan = build_plan(lanes=lanes, customers=[], planner_customer_source="config_only", db_customer_input_loaded=False)
    plan.warnings.append(FirewallPlanMessage(code="config_only_source", message="explicit config-only source requested; PostgreSQL planner input disabled", severity="warning"))
    return plan


def build_plan_from_config_with_live_snapshot(config: MPFConfig, snapshot: FirewallLiveSnapshot) -> FirewallPlanResult:
    lanes = [{"name": lane_name, "enabled": lane.enabled, "backend_port": lane.backend_port} for lane_name, lane in sorted(config.lanes.items())]
    plan = build_plan(lanes=lanes, customers=[], planner_customer_source="config_only", db_customer_input_loaded=False, live_snapshot=snapshot)
    plan.warnings.append(FirewallPlanMessage(code="config_only_source", message="explicit config-only source requested; PostgreSQL planner input disabled", severity="warning"))
    plan.finalize()
    return plan
