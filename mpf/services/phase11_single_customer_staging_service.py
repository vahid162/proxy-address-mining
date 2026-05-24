from __future__ import annotations

import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.domain.customer_lifecycle import CustomerLifecycleInput
from mpf.domain.customers import CustomerCreateRequest, CustomerPolicyInput
from mpf.services import customer_mutation_service, customer_read_service


def build_phase11_single_customer_staging_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []

    expected_version = str(kwargs.get("expected_version", __version__))
    farm5_baseline_version = str(kwargs.get("farm5_baseline_version", "0.1.168"))
    mode = str(kwargs.get("mode", "plan")).strip()
    gate_json = Path(str(kwargs.get("execution_gate_json", "")))
    candidate_customer_key = str(kwargs.get("candidate_customer_key", "")).strip()
    candidate_lane = str(kwargs.get("candidate_lane", "")).strip().lower()
    candidate_public_port = kwargs.get("candidate_public_port")
    candidate_backend_target = str(kwargs.get("candidate_backend_target", "")).strip()
    candidate_description = str(kwargs.get("candidate_description", "")).strip()
    operator = str(kwargs.get("operator", "")).strip()
    reason = str(kwargs.get("reason", "")).strip()

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")
    if farm5_baseline_version != "0.1.168":
        blockers.append("farm5_baseline_version_mismatch")
    if mode not in {"plan", "execute-db-only"}:
        blockers.append("mode_invalid")
    if candidate_customer_key != "limited-btc-001":
        blockers.append("candidate_customer_key_invalid")
    if candidate_lane != "btc":
        blockers.append("candidate_lane_invalid")
    if candidate_public_port != 20101:
        blockers.append("candidate_public_port_invalid")
    if candidate_backend_target != "172.18.0.3:60010":
        blockers.append("candidate_backend_target_invalid")
    if not candidate_description:
        blockers.append("candidate_description_missing")

    if kwargs.get("operator_confirmed") is not True or not operator or not reason:
        blockers.append("operator_not_confirmed")
    if kwargs.get("i_understand_db_only_staging") is not True:
        blockers.append("db_only_boundary_not_confirmed")
    if kwargs.get("i_understand_no_firewall_apply") is not True:
        blockers.append("no_firewall_apply_boundary_not_confirmed")
    if kwargs.get("i_understand_no_nat_apply") is not True:
        blockers.append("no_nat_apply_boundary_not_confirmed")
    if kwargs.get("i_understand_no_production_traffic") is not True:
        blockers.append("no_production_traffic_boundary_not_confirmed")
    if kwargs.get("i_understand_single_customer_limit") is not True:
        blockers.append("single_customer_limit_not_confirmed")
    if kwargs.get("i_confirm_port_not_live_until_firewall_gate") is not True:
        blockers.append("port_not_live_boundary_not_confirmed")
    if kwargs.get("i_confirm_rollback_plan_required") is not True:
        blockers.append("rollback_plan_requirement_not_confirmed")
    if kwargs.get("i_confirm_restart_test_required_before_traffic") is not True:
        blockers.append("restart_test_requirement_not_confirmed")
    if kwargs.get("i_confirm_abuse_1h_required_before_traffic") is not True:
        blockers.append("abuse_1h_requirement_not_confirmed")

    data: dict[str, object] | None = None
    if not gate_json.exists() or not gate_json.is_file():
        blockers.append("execution_gate_json_missing")
    else:
        try:
            data = json.loads(gate_json.read_text(encoding="utf-8"))
        except Exception:
            blockers.append("execution_gate_json_invalid")
    if data is not None:
        required = {
            "component": "phase11_limited_onboarding_execution_gate", "expected_version": "0.1.199", "repository_version": "0.1.199",
            "candidate_customer_key": "limited-btc-001", "candidate_lane": "btc", "candidate_public_port": 20101,
            "candidate_backend_target": "172.18.0.3:60010", "phase11e_execution_gate_ready": True, "phase11e_execution_allowed": False,
            "customer_created": False, "no_onboarding_authorized": True, "next_required_step": "phase11e_single_customer_execution_pr",
            "final_decision": "PHASE11E_LIMITED_ONBOARDING_EXECUTION_GATE_READY",
        }
        if any(data.get(k) != v for k, v in required.items()) or data.get("blockers") != [] or data.get("warnings") != []:
            blockers.append("execution_gate_not_ready")
        if any(data.get(k) is not False for k in ("phase11_accepted", "limited_onboarding_allowed", "production_traffic_enabled")):
            blockers.append("execution_gate_safety_boundary_open")
        if any(data.get(k) is True for k in ("mutation_performed", "db_mutation_performed", "firewall_mutation_performed", "nat_mutation_performed", "conntrack_mutation_performed", "docker_mutation_performed")):
            blockers.append("execution_gate_mutation_flag_detected")

    customer_created = False
    customer_updated = False
    db_mutation = False
    staging_plan: dict[str, object] = {}
    if not blockers:
        customers = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
        if not customers.ok:
            blockers.append("db_staging_service_error")
        else:
            rows = customers.customers
            existing_key = [r for r in rows if r.customer_key == "limited-btc-001"]
            any_20101 = [r for r in rows if r.port == 20101 and r.customer_key != "limited-btc-001"]
            if any_20101:
                blockers.append("candidate_port_collision")
            if len(existing_key) > 1:
                blockers.append("existing_customer_limit_exceeded")
            if existing_key:
                e = existing_key[0]
                if e.lane != "btc" or e.port != 20101:
                    blockers.append("candidate_conflicts_with_existing_customer")
                staging_plan = {"customer_exists": True, "customer_id": e.id, "customer_key": e.customer_key, "action": "idempotent"}
            else:
                staging_plan = {"customer_exists": False, "customer_key": "limited-btc-001", "lane": "btc", "port": 20101, "action": "create_db_only_staging_customer"}
                if mode == "execute-db-only":
                    try:
                        req = CustomerCreateRequest(
                            customer_key="limited-btc-001", lane="btc", name="limited-btc-001 (Phase11E DB-only staging)",
                            port=20101, status="paused",
                            policy=CustomerPolicyInput(miners=1, farms=1, maxconn=1, rate_per_min=60, burst=10, ips_mode="any", reason="phase11e db-only staging"),
                            lifecycle=CustomerLifecycleInput(activation_mode="first_connect", lifecycle_note=f"DB-only staging: {candidate_description}"),
                        )
                        res = customer_mutation_service.create_db_only_customer(config, req)
                        if not res.ok:
                            blockers.append("db_staging_service_error")
                            warnings.append(res.message)
                        else:
                            customer_created = True
                            db_mutation = True
                    except Exception:
                        blockers.append("db_staging_service_error")

    blockers = sorted(set(blockers))
    ready = not blockers
    idempotent_existing = bool(staging_plan.get("customer_exists") is True and staging_plan.get("action") == "idempotent")
    allowed = ready and mode == "execute-db-only" and (customer_created or idempotent_existing)
    return {
        "component": "phase11_single_customer_staging", "expected_version": expected_version, "repository_version": __version__, "mode": mode,
        "candidate_customer_key": candidate_customer_key, "candidate_lane": candidate_lane, "candidate_public_port": candidate_public_port,
        "candidate_backend_target": candidate_backend_target, "phase11e_single_customer_staging_ready": ready,
        "phase11e_db_staging_allowed": allowed, "customer_created": customer_created, "customer_updated": customer_updated,
        "db_mutation_performed": db_mutation, "firewall_mutation_performed": False, "nat_mutation_performed": False,
        "conntrack_mutation_performed": False, "docker_mutation_performed": False, "mutation_performed": db_mutation,
        "phase11_accepted": False, "limited_onboarding_allowed": False, "production_traffic_enabled": False, "no_onboarding_authorized": True,
        "staging_plan": staging_plan, "blockers": blockers, "warnings": warnings,
        "next_required_step": "phase11e_firewall_plan_gate_pr" if allowed else ("run_execute_db_only_staging_on_farm5" if ready else "none"),
        "final_decision": "PHASE11_SINGLE_CUSTOMER_DB_STAGING_EXECUTED" if allowed else ("PHASE11_SINGLE_CUSTOMER_STAGING_PLAN_READY" if ready else "BLOCKED"),
    }
