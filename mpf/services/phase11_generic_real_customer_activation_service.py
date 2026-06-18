"""Generic Phase 11 real-customer activation service contracts.

The service is deliberately fail-closed and mock-friendly: CI tests inject a
repository/backend resolver/snapshot/apply adapter and no real firewall command
is executed unless an operator supplies every execute confirmation.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from typing import Any, Protocol

from mpf import __version__
from mpf.services.phase11_controlled_backend_target_service import build_controlled_backend_target_report, expected_backend_target_from_report

READY = "production_generic_real_customer_activation_ready"
PACKAGE_READY = "generic_real_customer_activation_package_ready"
PREFLIGHT_READY = "generic_real_customer_activation_preflight_ready"
APPLY_PENDING_RUNTIME = "generic_real_customer_activation_apply_executed_pending_runtime_evidence"
RUNTIME_READY = "generic_real_customer_activation_runtime_evidence_ready"
MISSING = "missing_or_partial"

RESERVED_PORTS = {22, 80, 443, 2015, 5432, 60010}
MUTATION_FLAGS = {
    "firewall_mutation_performed": False,
    "nat_mutation_performed": False,
    "db_mutation_performed": False,
    "conntrack_mutation_performed": False,
    "docker_restart_performed": False,
    "systemd_restart_performed": False,
    "mutation_performed": False,
}


class ActivationRepository(Protocol):
    def get_customer(self, customer_key: str) -> dict[str, Any] | None: ...
    def get_lane(self, lane: str) -> dict[str, Any] | None: ...
    def get_current_policy(self, customer_key: str) -> dict[str, Any] | None: ...
    def find_active_port_conflicts(self, lane: str, port: int, customer_key: str) -> list[dict[str, Any]]: ...
    def list_active_customers(self) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class StaticActivationRepository:
    customers: dict[str, dict[str, Any]]
    lanes: dict[str, dict[str, Any]]
    policies: dict[str, dict[str, Any]]

    def get_customer(self, customer_key: str) -> dict[str, Any] | None:
        return self.customers.get(customer_key)

    def get_lane(self, lane: str) -> dict[str, Any] | None:
        return self.lanes.get(lane)

    def get_current_policy(self, customer_key: str) -> dict[str, Any] | None:
        return self.policies.get(customer_key)

    def find_active_port_conflicts(self, lane: str, port: int, customer_key: str) -> list[dict[str, Any]]:
        return [c for key, c in self.customers.items() if key != customer_key and c.get("lane") == lane and c.get("status") == "active" and c.get("deleted_at") is None and int(c.get("public_port", -1)) == port]

    def list_active_customers(self) -> list[dict[str, Any]]:
        return [c for c in self.customers.values() if c.get("status") == "active" and c.get("deleted_at") is None]


def _base(component: str, customer_key: str | None = None) -> dict[str, Any]:
    return {"component": component, "repository_version": __version__, "customer_key": customer_key, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no", **MUTATION_FLAGS}


def _target_string(report: dict[str, Any]) -> str | None:
    return expected_backend_target_from_report(report) or (f"{report.get('resolved_ipv4') or report.get('target_host')}:{report.get('target_port')}" if (report.get('resolved_ipv4') or report.get('target_host')) and report.get('target_port') else None)


def _eligibility(repo: ActivationRepository, customer_key: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    customer = repo.get_customer(customer_key)
    if not customer:
        return None, None, None, ["customer_missing"]
    lane_name = str(customer.get("lane") or "").lower()
    lane = repo.get_lane(lane_name)
    policy = repo.get_current_policy(customer_key)
    if customer.get("status") != "active": blockers.append("customer_not_active")
    if customer.get("deleted_at") is not None: blockers.append("customer_deleted")
    if customer.get("paused") is True: blockers.append("customer_paused")
    if customer.get("expired") is True or customer.get("expires_at") == "expired": blockers.append("customer_expired")
    if not lane: blockers.append("lane_missing")
    elif lane.get("enabled") is not True: blockers.append("lane_disabled")
    if lane_name != "btc": blockers.append("lane_not_btc")
    try:
        port = int(customer.get("public_port"))
    except Exception:
        port = -1
    if port < 1024 or port > 65535: blockers.append("customer_port_invalid")
    if port in RESERVED_PORTS: blockers.append("customer_port_reserved")
    if repo.find_active_port_conflicts(lane_name, port, customer_key): blockers.append("duplicate_active_port_conflict")
    if not policy: blockers.append("current_policy_missing")
    else:
        for key in ("miners", "farms", "maxconn", "rate", "burst"):
            val = policy.get(key, policy.get("rate_per_min") if key == "rate" else None)
            if not isinstance(val, int) or val <= 0:
                blockers.append(f"policy_{key}_invalid")
    return customer, lane, policy, sorted(set(blockers))


def _snapshot_blockers(snapshot: dict[str, Any] | None, port: int | None = None) -> list[str]:
    if snapshot is None:
        return []
    blockers: list[str] = []
    if snapshot.get("unknown_mpf_artifacts"):
        blockers.append("unknown_live_mpf_artifact")
    conflicts = snapshot.get("conflicting_ports") or []
    if port is not None and port in conflicts:
        blockers.append("live_conflicting_artifact_for_target_port")
    if snapshot.get("duplicate_dnat_ports") and port in snapshot.get("duplicate_dnat_ports"):
        blockers.append("duplicate_dnat_for_target_port")
    return blockers


def build_activation_package(repo: ActivationRepository, customer_key: str, *, backend_resolver=None, live_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    report = _base("phase11_generic_real_customer_activation_package", customer_key)
    customer, lane, policy, blockers = _eligibility(repo, customer_key)
    port = int(customer.get("public_port", -1)) if customer else None
    blockers += _snapshot_blockers(live_snapshot, port)
    backend_report = backend_resolver() if backend_resolver else build_controlled_backend_target_report()
    backend_target = _target_string(backend_report)
    if not backend_target:
        blockers.append("backend_target_resolution_failed")
    if backend_report.get("backend_public_exposure") is True or backend_report.get("forbidden_public_runtime_exposure") is True:
        blockers.append("backend_public_exposure_forbidden")
    if blockers:
        return {**report, "production_generic_real_customer_activation": MISSING, "blockers": sorted(set(blockers)), "final_decision": "BLOCKED_GENERIC_REAL_CUSTOMER_ACTIVATION_PACKAGE", "next_required_step": "production_generic_real_customer_activation"}
    package = {
        "customer_key": customer_key,
        "lane": customer["lane"],
        "public_port": port,
        "resolved_backend_target": backend_target,
        "precondition_fingerprint": hashlib.sha256(json.dumps({"customer": customer, "policy": policy, "backend_target": backend_target}, sort_keys=True, default=str).encode()).hexdigest(),
        "expected_artifact_summary": {"dnat": f"tcp dpt:{port} -> {backend_target}", "comments": [f"mpf customer={customer_key} port={port}"]},
        "rollback_artifact_metadata": {"scope": "selected_customer_only", "requires_pre_apply_snapshot": True},
    }
    payload = f"*nat\n-A PREROUTING -p tcp --dport {port} -m comment --comment \"MPF customer={customer_key} port={port}\" -j DNAT --to-destination {backend_target}\nCOMMIT\n*filter\n-N MPFC_{port}\n-A DOCKER-USER -p tcp -m conntrack --ctorigdstport {port} -m comment --comment \"MPF customer={customer_key} port={port}\" -j MPFC_{port}\n-A MPFC_{port} -j RETURN\nCOMMIT\n"
    package_id = f"phase11-generic-activation-{customer_key}-{port}-{uuid.uuid4().hex[:12]}"
    package["package_id"] = package_id
    package["restore_payload"] = payload
    package["package_sha256"] = hashlib.sha256(json.dumps(package, sort_keys=True, default=str).encode()).hexdigest()
    return {**report, "production_generic_real_customer_activation": PACKAGE_READY, "package": package, **package, "backend_target_report": backend_report, "blockers": [], "final_decision": "GENERIC_REAL_CUSTOMER_ACTIVATION_PACKAGE_READY", "next_required_step": "generic_real_customer_activation_preflight"}


def preflight_activation_package(package: dict[str, Any], *, live_snapshot: dict[str, Any] | None, confirmed_package_sha256: str | None, operator_context: str | None) -> dict[str, Any]:
    report = _base("phase11_generic_real_customer_activation_preflight", str(package.get("customer_key")))
    blockers: list[str] = []
    if not live_snapshot: blockers.append("iptables_snapshot_required")
    if not operator_context: blockers.append("operator_context_required")
    if not confirmed_package_sha256 or confirmed_package_sha256 != package.get("package_sha256"): blockers.append("package_hash_confirmation_mismatch")
    blockers += _snapshot_blockers(live_snapshot, int(package.get("public_port", -1)) if package.get("public_port") else None)
    if blockers:
        return {**report, "production_generic_real_customer_activation": MISSING, "blockers": sorted(set(blockers)), "final_decision": "BLOCKED_GENERIC_REAL_CUSTOMER_ACTIVATION_PREFLIGHT", "next_required_step": "generic_real_customer_activation_preflight"}
    return {**report, "production_generic_real_customer_activation": PREFLIGHT_READY, "blockers": [], "final_decision": "GENERIC_REAL_CUSTOMER_ACTIVATION_PREFLIGHT_READY", "next_required_step": "generic_real_customer_activation_apply"}


def apply_activation_package(package: dict[str, Any], *, execute: bool = False, confirmed_package_sha256: str | None = None, confirmed_customer_key: str | None = None, confirmed_public_port: int | None = None, pre_apply_snapshot_path: str | None = None, rollback_artifact_path: str | None = None, operator_lock_id: str | None = None, restore_runner=None) -> dict[str, Any]:
    report = _base("phase11_generic_real_customer_activation_apply", str(package.get("customer_key")))
    blockers = []
    if not execute: blockers.append("execute_flag_required")
    if os.environ.get("CI") and restore_runner is None: blockers.append("real_iptables_restore_forbidden_in_ci")
    if confirmed_package_sha256 != package.get("package_sha256"): blockers.append("package_hash_confirmation_mismatch")
    if confirmed_customer_key != package.get("customer_key"): blockers.append("target_customer_confirmation_mismatch")
    if int(confirmed_public_port or -1) != int(package.get("public_port", -2)): blockers.append("target_port_confirmation_mismatch")
    if not pre_apply_snapshot_path: blockers.append("pre_apply_iptables_save_snapshot_required")
    if not rollback_artifact_path: blockers.append("rollback_artifact_required")
    if not operator_lock_id: blockers.append("operator_lock_or_restore_point_required")
    if blockers:
        return {**report, "production_generic_real_customer_activation": MISSING, "blockers": blockers, "final_decision": "BLOCKED_GENERIC_REAL_CUSTOMER_ACTIVATION_APPLY", "next_required_step": "generic_real_customer_activation_apply"}
    if restore_runner:
        restore_runner(package["restore_payload"], test=True, noflush=True)
        restore_runner(package["restore_payload"], test=False, noflush=True)
    return {**report, "production_generic_real_customer_activation": APPLY_PENDING_RUNTIME, "firewall_mutation_performed": True, "nat_mutation_performed": True, "mutation_performed": True, "iptables_restore_test_invoked": True, "iptables_restore_invoked": True, "blockers": [], "final_decision": "GENERIC_REAL_CUSTOMER_ACTIVATION_APPLY_EXECUTED_PENDING_RUNTIME_EVIDENCE", "next_required_step": "generic_real_customer_activation_verify"}


def verify_activation(package: dict[str, Any], live_snapshot: dict[str, Any]) -> dict[str, Any]:
    report = _base("phase11_generic_real_customer_activation_verify", str(package.get("customer_key")))
    port = int(package.get("public_port"))
    target = package.get("resolved_backend_target")
    dnats = live_snapshot.get("dnat_by_port", {}).get(str(port), [])
    blockers = []
    if len(dnats) != 1: blockers.append("dnat_count_not_exactly_one")
    elif dnats[0] != target: blockers.append("stale_or_loopback_dnat_target")
    if str(dnats[0] if dnats else "").startswith("127."): blockers.append("stale_or_loopback_dnat_target")
    if f"MPFC_{port}" not in live_snapshot.get("chains", []): blockers.append("customer_filter_chain_missing")
    blockers += _snapshot_blockers(live_snapshot, port)
    if live_snapshot.get("backend_public_exposure") is True: blockers.append("backend_public_exposure_forbidden")
    status = RUNTIME_READY if not blockers else MISSING
    return {**report, "production_generic_real_customer_activation": status, "blockers": sorted(set(blockers)), "final_decision": "GENERIC_REAL_CUSTOMER_ACTIVATION_VERIFY_READY" if not blockers else "BLOCKED_GENERIC_REAL_CUSTOMER_ACTIVATION_VERIFY", "next_required_step": "generic_real_customer_activation_runtime_evidence" if not blockers else "generic_real_customer_activation_verify"}


def runtime_evidence(package: dict[str, Any], *, external_reachable: bool | None = None, backend_public_exposed: bool = False, appears_in_reports: bool = False) -> dict[str, Any]:
    blockers = []
    if external_reachable is not True: blockers.append("external_miner_path_evidence_missing")
    if backend_public_exposed: blockers.append("backend_public_exposure_forbidden")
    if not appears_in_reports: blockers.append("customer_report_usage_surface_missing")
    evidence = {"customer_key": package.get("customer_key"), "public_port": package.get("public_port"), "resolved_backend_target": package.get("resolved_backend_target"), "collected_at": datetime.now(UTC).isoformat(), "external_reachable": external_reachable, "backend_public_exposed": backend_public_exposed, "appears_in_reports": appears_in_reports}
    return {**_base("phase11_generic_real_customer_activation_runtime_evidence", str(package.get("customer_key"))), "production_generic_real_customer_activation": READY if not blockers else MISSING, "evidence": evidence, "evidence_sha256": hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest(), "blockers": blockers, "final_decision": "PRODUCTION_GENERIC_REAL_CUSTOMER_ACTIVATION_READY" if not blockers else "BLOCKED_GENERIC_REAL_CUSTOMER_ACTIVATION_RUNTIME_EVIDENCE", "next_required_step": "final_phase11_operational_completion_acceptance" if not blockers else "generic_real_customer_activation_runtime_evidence"}


def rollback_readiness(package: dict[str, Any], *, pre_apply_snapshot_path: str | None = None) -> dict[str, Any]:
    blockers = [] if pre_apply_snapshot_path else ["pre_apply_snapshot_required"]
    return {**_base("phase11_generic_real_customer_activation_rollback_readiness", str(package.get("customer_key"))), "rollback_scope": "selected_customer_only", "public_port": package.get("public_port"), "blockers": blockers, "final_decision": "GENERIC_REAL_CUSTOMER_ACTIVATION_ROLLBACK_READINESS_READY" if not blockers else "BLOCKED_GENERIC_REAL_CUSTOMER_ACTIVATION_ROLLBACK_READINESS", "next_required_step": "generic_real_customer_activation_runtime_evidence" if not blockers else "generic_real_customer_activation_rollback_readiness"}


def abuse_coverage_readiness(repo: ActivationRepository, customer_key: str) -> dict[str, Any]:
    active_keys = {str(c.get("customer_key")) for c in repo.list_active_customers() if str(c.get("lane", "")).lower() == "btc"}
    blockers = [] if customer_key in active_keys else ["activated_customer_missing_from_abuse_coverage"]
    return {**_base("phase11_generic_real_customer_activation_abuse_coverage", customer_key), "active_enabled_lane_customer_keys": sorted(active_keys), "abuse_hard_execution_enabled_by_this_pr": False, "production_generic_real_customer_activation_abuse_coverage": "ready" if not blockers else MISSING, "blockers": blockers, "final_decision": "GENERIC_REAL_CUSTOMER_ACTIVATION_ABUSE_COVERAGE_READY" if not blockers else "BLOCKED_GENERIC_REAL_CUSTOMER_ACTIVATION_ABUSE_COVERAGE"}


def readiness_from_evidence(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence and evidence.get("production_generic_real_customer_activation") == READY and evidence.get("final_decision") == "PRODUCTION_GENERIC_REAL_CUSTOMER_ACTIVATION_READY" and not evidence.get("blockers"):
        status = READY
        decision = "PRODUCTION_GENERIC_REAL_CUSTOMER_ACTIVATION_READY"
        blockers: list[str] = []
        next_step = "final_phase11_operational_completion_acceptance"
    else:
        status = MISSING
        decision = "BLOCKED_PRODUCTION_GENERIC_REAL_CUSTOMER_ACTIVATION_EVIDENCE"
        blockers = ["production_generic_real_customer_activation_evidence_missing_or_partial"]
        next_step = "production_generic_real_customer_activation"
    return {**_base("phase11_generic_real_customer_activation_readiness"), "production_generic_real_customer_activation": status, "blockers": blockers, "final_decision": decision, "next_required_step": next_step}

class ConfigActivationRepository:
    """Repository adapter that reads customers/lanes through existing services."""

    def __init__(self, config: Any):
        from mpf.services import customer_read_service, lane_service
        self.config = config
        self.customer_read_service = customer_read_service
        self.lane_service = lane_service

    def get_customer(self, customer_key: str) -> dict[str, Any] | None:
        res = self.customer_read_service.show_customer(self.config, customer_key=customer_key)
        if not res.ok or not res.customer:
            return None
        c = res.customer
        return {"customer_key": c.customer_key, "lane": c.lane, "public_port": c.port, "status": c.status, "deleted_at": c.deleted_at, "expired": c.status == "expired", "paused": c.status == "paused"}

    def get_lane(self, lane: str) -> dict[str, Any] | None:
        res = self.lane_service.list_lane_status(self.config)
        if not res.ok:
            return None
        for rec in res.lanes:
            if str(rec.name).lower() == lane.lower():
                return {"enabled": bool(rec.enabled), "backend_port": rec.backend_port}
        return None

    def get_current_policy(self, customer_key: str) -> dict[str, Any] | None:
        res = self.customer_read_service.show_customer(self.config, customer_key=customer_key)
        if not res.ok or not res.customer:
            return None
        c = res.customer
        if c.miners is None or c.farms is None or c.maxconn is None or c.rate_per_min is None or c.burst is None:
            return None
        return {"miners": c.miners, "farms": c.farms, "maxconn": c.maxconn, "rate": c.rate_per_min, "burst": c.burst}

    def find_active_port_conflicts(self, lane: str, port: int, customer_key: str) -> list[dict[str, Any]]:
        res = self.customer_read_service.list_customer_status(self.config, lane=lane, status="active", include_deleted=False, limit=1000)
        if not res.ok:
            return [{"blocker": "active_port_conflict_scan_failed"}]
        return [{"customer_key": c.customer_key, "public_port": c.port} for c in res.customers if c.customer_key != customer_key and int(c.port) == int(port)]

    def list_active_customers(self) -> list[dict[str, Any]]:
        res = self.customer_read_service.list_customer_status(self.config, status="active", include_deleted=False, limit=1000)
        if not res.ok:
            return []
        return [{"customer_key": c.customer_key, "lane": c.lane, "status": c.status, "deleted_at": c.deleted_at} for c in res.customers]
