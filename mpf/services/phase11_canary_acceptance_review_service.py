from __future__ import annotations

import json
from dataclasses import dataclass, field
from ipaddress import ip_address
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service

@dataclass(slots=True)
class Phase11CanaryAcceptanceEvidence:
    farm5_baseline_version: str | None = None
    evidence_source: str | None = None
    evidence_reference: str | None = None
    nat_counter_packets: int | None = None
    nat_counter_bytes: int | None = None
    conntrack_assured: bool = False
    stratum_subscribe_ok: bool = False
    stratum_authorize_ok: bool = False
    stratum_set_difficulty_seen: bool = False
    stratum_notify_seen: bool = False
    forwarder_pool_seen: bool = False
    bridge_loopback_seen: bool = False
    proxy_doctor_ok: bool = False
    bridge_healthy: bool = False
    bridge_reachable_from_forwarder: bool = False
    canary_nat_rule_present: bool = False
    canary_nat_rule_count: int = 0
    canary_nat_target: str | None = None
    mpf_nat_pre_exists: bool = False
    prerouting_hook_present: bool = False
    no_extra_customer_nat_rules: bool = False
    no_unexpected_mpf_firewall_references: bool = False
    rollback_reference: str | None = None
    restore_reference: str | None = None
    canary_customer_db_visible: bool = False
    usage_visibility_ok: bool = False
    reject_visibility_ok: bool = False
    session_visibility_ok: bool = False
    unique_ip_visibility_ok: bool = False
    worker_visibility_ok: bool = False
    abuse_coverage_ok: bool = False
    final_check_report_ok: bool = False
    v2raya_ui_local_only: bool = False
    btc_backend_local_only: bool = False
    bridge_no_host_publish: bool = False
    forwarder_uses_bridge_upstream: bool = False
    direct_v2raya_20170_blocked: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Phase11CanaryAcceptanceEvidence":
        kwargs = {}
        for f in cls.__dataclass_fields__:
            if f in data:
                kwargs[f] = data[f]
        obj = cls(**kwargs)
        if obj.canary_nat_rule_count is None:
            obj.canary_nat_rule_count = 0
        return obj


def _is_public_ip(host: str) -> bool:
    try:
        ip = ip_address(host)
        return ip.is_global
    except ValueError:
        return False


def build_phase11_canary_acceptance_review_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, evidence: Phase11CanaryAcceptanceEvidence | None = None) -> dict[str, object]:
    evidence = evidence or Phase11CanaryAcceptanceEvidence()
    blockers: list[str] = []
    warnings: list[str] = []
    missing_visibility: list[str] = []
    missing_evidence: list[str] = []

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")

    if customer_key != "canary-btc-001": blockers.append("customer_key_must_be_canary-btc-001")
    if lane != "btc": blockers.append("lane_must_be_btc")
    if port != 20001: blockers.append("port_must_be_20001")

    # DB visibility
    customer_rows = customer_read_service.list_customer_status(config, include_deleted=False, limit=1000).rows
    active_keys = [r.customer_key for r in customer_rows]
    if any(k != customer_key for k in active_keys):
        blockers.append("unexpected_active_customer_present")
    if customer_key not in active_keys and not evidence.canary_customer_db_visible:
        missing_visibility.append("canary_customer_db_visibility")

    # NAT gates
    if not evidence.mpf_nat_pre_exists: blockers.append("missing_mpf_nat_pre")
    if not evidence.prerouting_hook_present: blockers.append("missing_prerouting_to_mpf_nat_pre")
    if not evidence.canary_nat_rule_present: blockers.append("missing_canary_nat_rule")
    if evidence.canary_nat_rule_count != 1: blockers.append("duplicate_or_missing_canary_nat_rule")
    if not evidence.no_extra_customer_nat_rules: blockers.append("extra_customer_nat_rule_detected")
    if not evidence.no_unexpected_mpf_firewall_references: blockers.append("unexpected_mpf_firewall_reference_detected")

    backend_target = evidence.canary_nat_target
    if backend_target:
        host = backend_target.split(":")[0]
        if backend_target == "127.0.0.1:60010": blockers.append("loopback_canary_target_forbidden")
        if _is_public_ip(host): blockers.append("public_canary_target_forbidden")
    else:
        missing_evidence.append("canary_nat_target")

    # Runtime/traffic evidence
    if not evidence.proxy_doctor_ok: missing_evidence.append("proxy_doctor_ok")
    if not evidence.bridge_healthy: blockers.append("bridge_unhealthy_or_missing")
    if not evidence.bridge_reachable_from_forwarder: blockers.append("bridge_not_reachable_from_forwarder")
    if not evidence.v2raya_ui_local_only: blockers.append("v2raya_ui_not_local_only")
    if not evidence.btc_backend_local_only: blockers.append("btc_backend_not_local_only")
    if not evidence.bridge_no_host_publish: blockers.append("bridge_host_publish_detected")
    if not evidence.forwarder_uses_bridge_upstream: blockers.append("forwarder_not_using_bridge_upstream")
    if not evidence.direct_v2raya_20170_blocked: blockers.append("direct_v2raya_20170_not_blocked")

    if not (isinstance(evidence.nat_counter_packets, int) and evidence.nat_counter_packets > 0): missing_evidence.append("nat_counter_packets_gt_zero")
    for flag, key in [
        (evidence.conntrack_assured, "conntrack_assured"),
        (evidence.stratum_subscribe_ok, "stratum_subscribe_ok"),
        (evidence.stratum_authorize_ok, "stratum_authorize_ok"),
        (evidence.stratum_set_difficulty_seen, "stratum_set_difficulty_seen"),
        (evidence.stratum_notify_seen, "stratum_notify_seen"),
        (evidence.forwarder_pool_seen, "forwarder_pool_seen"),
        (evidence.bridge_loopback_seen, "bridge_loopback_seen"),
    ]:
        if not flag: missing_evidence.append(key)

    vis_map = {
        "usage_counters_visibility": evidence.usage_visibility_ok,
        "reject_counters_visibility": evidence.reject_visibility_ok,
        "active_recent_sessions_visibility": evidence.session_visibility_ok,
        "unique_ips_visibility": evidence.unique_ip_visibility_ok,
        "unique_workers_visibility": evidence.worker_visibility_ok,
        "abuse_coverage_visibility": evidence.abuse_coverage_ok,
        "final_check_report_visibility": evidence.final_check_report_ok,
        "rollback_or_restore_plan_visibility": bool(evidence.rollback_reference or evidence.restore_reference),
        "canary_customer_db_visibility": evidence.canary_customer_db_visible or (customer_key in active_keys),
    }
    for k, ok in vis_map.items():
        if not ok and k not in missing_visibility:
            missing_visibility.append(k)

    for bool_field in ("proxy_doctor_ok","bridge_healthy","stratum_subscribe_ok","stratum_authorize_ok"):
        if getattr(evidence, bool_field) and not evidence.evidence_reference:
            warnings.append(f"{bool_field}_true_without_reference")

    blockers.extend([f"missing_visibility:{x}" for x in missing_visibility])
    blockers.extend([f"missing_evidence:{x}" for x in missing_evidence])

    ready = not blockers
    return {
        "component": "phase11_canary_acceptance_review",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "backend_target": backend_target,
        "final_decision": "ACCEPTANCE_REVIEW_READY" if ready else "BLOCKED",
        "final_decision_reason": "all required gates satisfied" if ready else "blocked_by_missing_or_failed_gates",
        "mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "production_traffic_enabled": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "no_onboarding_authorized": True,
        "controlled_canary_artifact_present": bool(evidence.mpf_nat_pre_exists and evidence.prerouting_hook_present and evidence.canary_nat_rule_count == 1 and evidence.canary_nat_rule_present and evidence.no_extra_customer_nat_rules and evidence.no_unexpected_mpf_firewall_references),
        "current_phase_gate_strict_result": "CRITICAL_EXPECTED_FOR_CANARY_ARTIFACT" if evidence.canary_nat_rule_present else "CRITICAL",
        "current_phase_gate_generalized_success": False,
        "safety_flags": {
            "firewall_apply_allowed": False, "abuse_automation_allowed": False, "ui_allowed": False, "telegram_allowed": False,
            "scheduler_allowed": False, "worker_enforcement_allowed": False, "production_traffic_allowed": False,
        },
        "blockers": blockers,
        "warnings": warnings,
        "missing_visibility_primitives": sorted(set(missing_visibility)),
        "missing_evidence_primitives": sorted(set(missing_evidence)),
        "next_required_step": "implement_or_evidence_missing_visibility_primitives_starting_with_canary_customer_db_visibility" if missing_visibility else "collect_missing_evidence_primitives",
    }


def load_phase11_canary_acceptance_evidence_json(path: Path) -> Phase11CanaryAcceptanceEvidence:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("evidence json must be an object")
    return Phase11CanaryAcceptanceEvidence.from_dict(data)
