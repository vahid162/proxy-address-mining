from __future__ import annotations

from collections import Counter

from mpf.config import MPFConfig
from mpf.domain.firewall import FirewallPlanChange, FirewallPlanMessage, FirewallPlanResult, FirewallRuleIntent
from mpf.repositories import firewall_planner_read_repo


def build_plan(
    *,
    lanes: list[dict],
    customers: list[dict],
    backend_exposed: bool = False,
    planner_customer_source: str = "unknown",
    db_customer_input_loaded: bool = False,
) -> FirewallPlanResult:
    plan = FirewallPlanResult()
    plan.planner_customer_source = planner_customer_source
    plan.db_customer_input_loaded = db_customer_input_loaded

    enabled_lanes = [lane for lane in lanes if lane.get("enabled", False)]
    backend_ports = [int(lane["backend_port"]) for lane in enabled_lanes]
    backend_counts = Counter(backend_ports)
    for port, count in backend_counts.items():
        if count > 1:
            plan.errors.append(FirewallPlanMessage(code="lane_backend_collision", message=f"backend_port collision: {port}", severity="error"))

    if backend_exposed:
        plan.errors.append(FirewallPlanMessage(code="backend_exposure", message="backend public exposure risk detected", severity="error"))

    active_customers = [c for c in customers if c.get("status") == "active"]
    port_counts = Counter(int(c["port"]) for c in active_customers)
    for port, count in port_counts.items():
        if count > 1:
            plan.errors.append(FirewallPlanMessage(code="customer_port_collision", message=f"customer port collision: {port}", severity="error"))
        if port in backend_ports:
            plan.errors.append(FirewallPlanMessage(code="customer_backend_port_collision", message=f"customer port collides with backend port: {port}", severity="error"))

    if not db_customer_input_loaded:
        plan.warnings.append(FirewallPlanMessage(code="planner_customer_source", message=f"planner_customer_source={planner_customer_source}; db_customer_input_loaded=false", severity="warning"))

    for customer in customers:
        status = customer.get("status")
        if status == "deleted":
            continue
        if status in {"paused", "expired"}:
            plan.warnings.append(FirewallPlanMessage(code="inactive_placeholder", message=f"customer {customer.get('customer_key')} status={status} is represented as non-active intent", severity="warning"))
            continue
        if status != "active":
            plan.warnings.append(FirewallPlanMessage(code="unsupported_status", message=f"customer {customer.get('customer_key')} has unsupported status={status}", severity="warning"))
            continue
        lane_name = str(customer["lane"])
        customer_key = str(customer["customer_key"])
        plan.customer_coverage.append(customer_key)
        plan.affected_customers.append(customer_key)
        plan.customer_policy_references.append(f"{customer_key}:policy")
        plan.rules.append(FirewallRuleIntent(id=f"customer:{customer_key}", table="nat", chain=f"MPF_{lane_name}_CUSTOMERS", action="forward_intent", lane=lane_name, customer_key=customer_key, detail=f"port={customer['port']}"))
        plan.changes.append(FirewallPlanChange(kind="create", object_type="rule_intent", object_id=f"customer:{customer_key}", detail="planned customer forwarding intent"))

    for lane in enabled_lanes:
        plan.lane_backend_coverage.append(str(lane["name"]))

    if not active_customers:
        plan.changes.append(FirewallPlanChange(kind="keep", object_type="planner", object_id="no_active_customers", detail="no active customer forwarding intents"))

    plan.finalize()
    return plan


def build_plan_from_db(config: MPFConfig) -> FirewallPlanResult:
    load = firewall_planner_read_repo.load_firewall_planner_input(config)
    if not load.ok:
        raise RuntimeError(load.message)
    return build_plan(lanes=load.lanes, customers=load.customers, planner_customer_source="db_readonly", db_customer_input_loaded=True)


def build_plan_from_config(config: MPFConfig) -> FirewallPlanResult:
    lanes = [{"name": lane_name, "enabled": lane.enabled, "backend_port": lane.backend_port} for lane_name, lane in sorted(config.lanes.items())]
    plan = build_plan(lanes=lanes, customers=[], planner_customer_source="config_only", db_customer_input_loaded=False)
    plan.warnings.append(FirewallPlanMessage(code="config_only_source", message="explicit config-only source requested; PostgreSQL planner input disabled", severity="warning"))
    return plan
