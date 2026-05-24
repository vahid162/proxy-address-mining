from __future__ import annotations

import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service


def build_phase11_single_customer_firewall_plan_gate_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []

    expected_version = str(kwargs.get("expected_version", __version__))
    farm5_baseline_version = str(kwargs.get("farm5_baseline_version", "0.1.168"))
    staging_execute_json = Path(str(kwargs.get("staging_execute_json", "")))
    candidate_customer_key = str(kwargs.get("candidate_customer_key", "")).strip()
    candidate_lane = str(kwargs.get("candidate_lane", "")).strip().lower()
    candidate_public_port = kwargs.get("candidate_public_port")
    candidate_backend_target = str(kwargs.get("candidate_backend_target", "")).strip()
    operator = str(kwargs.get("operator", "")).strip()
    reason = str(kwargs.get("reason", "")).strip()

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")
    if farm5_baseline_version != "0.1.168":
        blockers.append("farm5_baseline_version_mismatch")
    if candidate_customer_key != "limited-btc-001":
        blockers.append("candidate_customer_key_invalid")
    if candidate_lane != "btc":
        blockers.append("candidate_lane_invalid")
    if candidate_public_port != 20101:
        blockers.append("candidate_public_port_invalid")
    if candidate_backend_target != "172.18.0.3:60010":
        blockers.append("candidate_backend_target_invalid")

    if kwargs.get("operator_confirmed") is not True or not operator or not reason:
        blockers.append("operator_not_confirmed")
    if kwargs.get("i_understand_plan_only") is not True:
        blockers.append("plan_only_boundary_not_confirmed")
    if kwargs.get("i_understand_no_firewall_apply") is not True:
        blockers.append("no_firewall_apply_boundary_not_confirmed")
    if kwargs.get("i_understand_no_nat_apply") is not True:
        blockers.append("no_nat_apply_boundary_not_confirmed")
    if kwargs.get("i_understand_no_production_traffic") is not True:
        blockers.append("no_production_traffic_boundary_not_confirmed")
    if kwargs.get("i_understand_no_miner_traffic_yet") is not True:
        blockers.append("no_miner_traffic_boundary_not_confirmed")
    if kwargs.get("i_confirm_restore_point_required_before_apply") is not True:
        blockers.append("restore_point_requirement_not_confirmed")
    if kwargs.get("i_confirm_lock_required_before_apply") is not True:
        blockers.append("lock_requirement_not_confirmed")
    if kwargs.get("i_confirm_rollback_plan_required_before_apply") is not True:
        blockers.append("rollback_plan_requirement_not_confirmed")
    if kwargs.get("i_confirm_restart_test_required_before_traffic") is not True:
        blockers.append("restart_test_requirement_not_confirmed")
    if kwargs.get("i_confirm_abuse_1h_required_before_traffic") is not True:
        blockers.append("abuse_1h_requirement_not_confirmed")

    data: dict[str, object] | None = None
    if not staging_execute_json.exists() or not staging_execute_json.is_file():
        blockers.append("staging_execute_json_missing")
    else:
        try:
            data = json.loads(staging_execute_json.read_text(encoding="utf-8"))
        except Exception:
            blockers.append("staging_execute_json_invalid")

    if data is not None:
        required = {
            "component": "phase11_single_customer_staging", "expected_version": "0.1.200", "repository_version": "0.1.200",
            "mode": "execute-db-only", "candidate_customer_key": "limited-btc-001", "candidate_lane": "btc",
            "candidate_public_port": 20101, "candidate_backend_target": "172.18.0.3:60010", "phase11e_single_customer_staging_ready": True,
            "phase11e_db_staging_allowed": True, "no_onboarding_authorized": True, "next_required_step": "phase11e_firewall_plan_gate_pr",
            "final_decision": "PHASE11_SINGLE_CUSTOMER_DB_STAGING_EXECUTED",
        }
        if any(data.get(k) != v for k, v in required.items()) or data.get("blockers") != [] or data.get("warnings") != []:
            blockers.append("staging_execute_not_executed")
        if any(data.get(k) is not False for k in ("phase11_accepted", "limited_onboarding_allowed", "production_traffic_enabled")):
            blockers.append("staging_safety_boundary_open")
        if any(data.get(k) is True for k in ("firewall_mutation_performed", "nat_mutation_performed", "conntrack_mutation_performed", "docker_mutation_performed")):
            blockers.append("staging_firewall_or_nat_mutation_detected")
        created = data.get("customer_created") is True
        idem = bool(isinstance(data.get("staging_plan"), dict) and data.get("staging_plan", {}).get("customer_exists") is True)
        if not (created or idem):
            blockers.append("staging_execute_not_executed")
        if data.get("db_mutation_performed") is False and not idem:
            blockers.append("staging_execute_not_executed")

    firewall_plan_summary: dict[str, object] = {}
    if not blockers:
        try:
            customers = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
        except Exception:
            customers = customer_read_service.CustomerList(ok=False, message="exception", customers=[])
        if not customers.ok:
            blockers.append("db_read_failed")
        else:
            rows = customers.customers
            staged = [r for r in rows if r.customer_key == "limited-btc-001"]
            port_conflicts = [r for r in rows if r.port == 20101 and r.customer_key != "limited-btc-001"]
            if len(staged) == 0:
                blockers.append("staged_customer_missing")
            elif len(staged) > 1:
                blockers.append("staged_customer_duplicate")
            else:
                s = staged[0]
                if s.lane != "btc" or s.port != 20101:
                    blockers.append("staged_customer_scope_mismatch")
                status = str(getattr(s, "status", "")).strip().lower()
                if status != "paused":
                    blockers.append("staged_customer_not_safe_status")
            if port_conflicts:
                blockers.append("candidate_port_collision")

            if not blockers:
                firewall_plan_summary = {
                    "intended_chain": "MPFC_20101",
                    "intended_nat_chain": "MPF_NAT_PRE",
                    "intended_public_port": 20101,
                    "intended_backend_target": "172.18.0.3:60010",
                    "intended_customer_key": "limited-btc-001",
                    "intended_lane": "btc",
                    "intended_rules": [
                        "DNAT 20101 -> 172.18.0.3:60010",
                        "Customer connlimit/hashlimit reject policy rules (plan-only summary)",
                    ],
                    "safety": {
                        "iptables_restore_authorized": False,
                        "apply_command_approved": False,
                        "mutation_performed": False,
                        "existing_canary_20001_artifact_modified": False,
                        "production_traffic_enabled": False,
                    },
                }

    blockers = sorted(set(blockers))
    ready = not blockers
    firewall_plan_generated = ready and bool(firewall_plan_summary)
    return {
        "component": "phase11_single_customer_firewall_plan_gate",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": candidate_customer_key,
        "candidate_lane": candidate_lane,
        "candidate_public_port": candidate_public_port,
        "candidate_backend_target": candidate_backend_target,
        "phase11e_firewall_plan_gate_ready": ready,
        "firewall_plan_generated": firewall_plan_generated,
        "firewall_apply_allowed": False,
        "nat_apply_allowed": False,
        "iptables_restore_authorized": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "mutation_performed": False,
        "firewall_plan_summary": firewall_plan_summary,
        "blockers": blockers,
        "warnings": warnings,
        "next_required_step": "phase11e_firewall_apply_gate_pr" if ready else "none",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_PLAN_GATE_READY" if ready else "BLOCKED",
    }
