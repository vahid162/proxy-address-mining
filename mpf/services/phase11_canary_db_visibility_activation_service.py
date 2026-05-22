from __future__ import annotations

from mpf import __version__
from mpf.config import MPFConfig
from mpf.domain.customers import CustomerCreateRequest, CustomerLifecycleInput, CustomerPolicyInput
from mpf.domain.production import Phase11CanaryDbVisibilityActivationRequest
from mpf.services import customer_mutation_service, customer_read_service


def build_phase11_canary_db_visibility_activation_report(config: MPFConfig, request: Phase11CanaryDbVisibilityActivationRequest) -> dict[str, object]:
    validation_errors = request.validate(expected_repo_version=__version__)
    rows = customer_read_service.list_customer_status(config, include_deleted=True, limit=1000)
    active = [c for c in rows.customers if c.deleted_at is None and c.status != "deleted"]
    all_rows = rows.customers

    exact_active = [c for c in active if c.customer_key == request.customer_key and c.lane == request.lane and c.port == request.port]
    exact_deleted = [c for c in all_rows if c.customer_key == request.customer_key and c.lane == request.lane and c.port == request.port and (c.deleted_at is not None or c.status == "deleted")]
    key_collision = any(c.customer_key == request.customer_key and (c.lane != request.lane or c.port != request.port) for c in all_rows)
    port_collision = any(c.port == request.port and c.customer_key != request.customer_key for c in all_rows)
    unexpected_active = any(c.customer_key != request.customer_key for c in active)
    blockers: list[str] = []
    planned_action = "none"
    final_decision = "BLOCKED"
    execution_result: dict[str, object] = {"status": "not_executed"}
    mutation = False

    if rows.ok is False:
        blockers.append("customer_list_read_failed")
    if key_collision:
        blockers.append("canary_customer_key_collision")
    if port_collision:
        blockers.append("canary_port_collision")
    if unexpected_active:
        blockers.append("unexpected_active_customer_present")
    if any(c.customer_key == request.customer_key and c.deleted_at is None and (c.lane != request.lane or c.port != request.port) for c in active):
        blockers.append("active_canary_scope_mismatch")
    if any(c.customer_key == request.customer_key and (c.deleted_at is not None or c.status == 'deleted') and (c.lane != request.lane or c.port != request.port) for c in all_rows):
        blockers.append("deleted_canary_scope_mismatch")

    if not blockers:
        if exact_active:
            final_decision = "DB_VISIBILITY_ALREADY_PRESENT"
        elif exact_deleted:
            planned_action = "restore_deleted_exact_canary_customer"
            final_decision = "DB_VISIBILITY_PLAN_READY"
        elif not all_rows:
            planned_action = "create_exact_canary_customer"
            final_decision = "DB_VISIBILITY_PLAN_READY"
        else:
            planned_action = "blocked_manual_review_required"
            blockers.append("blocked_manual_review_required")

    if request.requested_action == "execute" and not validation_errors and not blockers and final_decision == "DB_VISIBILITY_PLAN_READY":
        if planned_action == "create_exact_canary_customer":
            res = customer_mutation_service.create_customer(
                config,
                CustomerCreateRequest(
                    lane=request.lane,
                    name=request.name,
                    port=request.port,
                    status="active",
                    policy=CustomerPolicyInput(miners=request.miners, farms=request.farms, maxconn=request.maxconn, rate_per_min=request.rate_per_min, burst=request.burst, ips_mode=request.ips_mode, ip_whitelist=request.ip_whitelist, reason=request.reason),
                    lifecycle=CustomerLifecycleInput(activation_mode="manual", service_days=30, lifecycle_note=request.reason),
                    customer_key=request.customer_key,
                ),
                dry_run=False,
            )
        else:
            res = customer_mutation_service.restore_phase11_exact_canary_db_visibility_customer(
                config, customer_key=request.customer_key, lane=request.lane, port=request.port, name=request.name,
                miners=request.miners, farms=request.farms, maxconn=request.maxconn, rate_per_min=request.rate_per_min, burst=request.burst, ips_mode=request.ips_mode, reason=request.reason, dry_run=False
            )
        execution_result = {"ok": res.ok, "message": res.message}
        mutation = bool(res.ok)
        final_decision = "DB_VISIBILITY_EXECUTED" if res.ok else "BLOCKED"
        if not res.ok:
            blockers.append("execute_failed")

    status = "AUTHORIZED_FOR_EXECUTE" if request.requested_action == "execute" and not validation_errors and not blockers else "PLAN_ONLY_OR_BLOCKED"
    visible = final_decision in {"DB_VISIBILITY_ALREADY_PRESENT", "DB_VISIBILITY_EXECUTED"}
    return {
        "component": "phase11_canary_db_visibility_activation",
        "expected_version": request.expected_version,
        "repository_version": __version__,
        "customer_key": request.customer_key,
        "lane": request.lane,
        "public_port": request.port,
        "requested_action": request.requested_action,
        "mutation_performed": mutation,
        "db_mutation_performed": mutation,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "production_traffic_enabled": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "no_onboarding_authorized": True,
        "customer_onboarding_scope": "exact_canary_db_only",
        "final_decision": "BLOCKED" if validation_errors or blockers and final_decision != "DB_VISIBILITY_ALREADY_PRESENT" else final_decision,
        "authorization_status": status,
        "validation_errors": validation_errors,
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "pre_state": {"active_count": len(active), "all_count": len(all_rows), "exact_active": len(exact_active), "exact_deleted": len(exact_deleted)},
        "planned_action": planned_action,
        "execution_result": execution_result,
        "rollback_plan": "soft-delete canary-btc-001 via customer delete service path",
        "post_visibility_summary": {"canary_customer_db_visibility": "PRESENT" if visible else "MISSING"},
        "next_required_step": "usage_counters_visibility" if visible else "canary_customer_db_visibility",
    }
