from __future__ import annotations

import json
from dataclasses import dataclass
from ipaddress import ip_address
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service

_ALLOWED_FARM5_BASELINE_VERSION = "0.1.168"

_VISIBILITY_PRIORITY = [
    "canary_customer_db_visibility", "usage_counters_visibility", "reject_counters_visibility", "active_recent_sessions_visibility",
    "unique_ips_visibility", "unique_workers_visibility", "abuse_coverage_visibility", "final_check_report_visibility", "rollback_or_restore_plan_visibility",
]
_EVIDENCE_PRIORITY = [
    "conntrack_assured", "stratum_subscribe_ok", "stratum_authorize_ok", "stratum_set_difficulty_seen", "stratum_notify_seen", "forwarder_pool_seen", "bridge_loopback_seen",
]


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
        kwargs = {f: data[f] for f in cls.__dataclass_fields__ if f in data}
        obj = cls(**kwargs)
        if obj.canary_nat_rule_count is None:
            obj.canary_nat_rule_count = 0
        return obj


def _parse_current_state_block(text: str) -> dict[str, str] | None:
    marker = "## Current State"
    start = text.find(marker)
    if start < 0:
        return None
    code_start = text.find("```text", start)
    if code_start < 0:
        return None
    code_end = text.find("```", code_start + 7)
    if code_end < 0:
        return None
    lines = text[code_start + 7 : code_end].strip().splitlines()
    parsed: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed or None


def _validate_canary_target(target: str) -> list[str]:
    blockers: list[str] = []
    host, sep, port = target.rpartition(":")
    if not sep or not host:
        return ["invalid_canary_target_format"]
    if port != "60010":
        blockers.append("wrong_canary_target_port")
    if host.lower() == "localhost":
        blockers.append("localhost_canary_target_forbidden")
        return blockers
    try:
        ip = ip_address(host)
    except ValueError:
        blockers.append("non_private_canary_target_forbidden")
        return blockers
    if ip.is_loopback:
        blockers.append("loopback_canary_target_forbidden")
    if ip.is_unspecified or ip.is_link_local or ip.is_multicast or ip.is_global:
        blockers.append("non_private_canary_target_forbidden")
    if not ip.is_private:
        blockers.append("non_private_canary_target_forbidden")
    return sorted(set(blockers))


def build_phase11_canary_acceptance_review_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, evidence: Phase11CanaryAcceptanceEvidence | None = None) -> dict[str, object]:
    _ = config
    evidence = evidence or Phase11CanaryAcceptanceEvidence()
    blockers: list[str] = []
    warnings: list[str] = []
    missing_visibility: list[str] = []
    missing_evidence: list[str] = []

    root = Path(__file__).resolve().parents[2]
    phase_status_path = root / "docs" / "PHASE_STATUS.md"
    current_state = _parse_current_state_block(phase_status_path.read_text(encoding="utf-8")) if phase_status_path.exists() else None
    if current_state is None:
        blockers.append("phase_status_current_state_missing_or_malformed")
    else:
        if "Phase 10" not in current_state.get("current_accepted_phase", "") or "Phase 11" not in current_state.get("current_working_phase", ""):
            blockers.append("phase_status_not_phase10_phase11")
        if current_state.get("production_traffic") != "none":
            blockers.append("production_traffic_not_none")
        if current_state.get("firewall_apply_allowed") != "no":
            blockers.append("firewall_apply_not_no")
        if current_state.get("customer_onboarding_allowed") != "db_only":
            blockers.append("onboarding_not_db_only")
        if current_state.get("abuse_automation_allowed") != "no":
            blockers.append("abuse_automation_not_no")
        if current_state.get("ui_allowed") != "no":
            blockers.append("ui_not_no")
        if current_state.get("telegram_allowed") != "no":
            blockers.append("telegram_not_no")

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")
    if farm5_baseline_version != _ALLOWED_FARM5_BASELINE_VERSION:
        blockers.append("farm5_baseline_version_not_allowed")
    if evidence.farm5_baseline_version and evidence.farm5_baseline_version != farm5_baseline_version:
        blockers.append("farm5_baseline_version_mismatch_with_evidence")

    if customer_key != "canary-btc-001":
        blockers.append("customer_key_must_be_canary-btc-001")
    if lane != "btc":
        blockers.append("lane_must_be_btc")
    if port != 20001:
        blockers.append("port_must_be_20001")

    customer_list = customer_read_service.list_customer_status(config, include_deleted=False, limit=1000)
    if not customer_list.ok:
        blockers.append("customer_list_read_failed")
        warnings.append(f"customer_list_read_failed:{customer_list.message}")
        active_keys: list[str] = []
    else:
        active_keys = [r.customer_key for r in customer_list.customers]
    if any(k != customer_key for k in active_keys):
        blockers.append("unexpected_active_customer_present")
    if customer_key not in active_keys and not evidence.canary_customer_db_visible:
        missing_visibility.append("canary_customer_db_visibility")

    if not evidence.mpf_nat_pre_exists:
        blockers.append("missing_mpf_nat_pre")
    if not evidence.prerouting_hook_present:
        blockers.append("missing_prerouting_to_mpf_nat_pre")
    if not evidence.canary_nat_rule_present:
        blockers.append("missing_canary_nat_rule")
    if evidence.canary_nat_rule_count != 1:
        blockers.append("duplicate_or_missing_canary_nat_rule")
    if not evidence.no_extra_customer_nat_rules:
        blockers.append("extra_customer_nat_rule_detected")
    if not evidence.no_unexpected_mpf_firewall_references:
        blockers.append("unexpected_mpf_firewall_reference_detected")

    backend_target = evidence.canary_nat_target
    if backend_target:
        blockers.extend(_validate_canary_target(backend_target))
    else:
        missing_evidence.append("canary_nat_target")

    if not evidence.proxy_doctor_ok:
        missing_evidence.append("proxy_doctor_ok")
    if not evidence.bridge_healthy:
        blockers.append("bridge_unhealthy_or_missing")
    if not evidence.bridge_reachable_from_forwarder:
        blockers.append("bridge_not_reachable_from_forwarder")
    if not evidence.v2raya_ui_local_only:
        blockers.append("v2raya_ui_not_local_only")
    if not evidence.btc_backend_local_only:
        blockers.append("btc_backend_not_local_only")
    if not evidence.bridge_no_host_publish:
        blockers.append("bridge_host_publish_detected")
    if not evidence.forwarder_uses_bridge_upstream:
        blockers.append("forwarder_not_using_bridge_upstream")
    if not evidence.direct_v2raya_20170_blocked:
        blockers.append("direct_v2raya_20170_not_blocked")

    if not (isinstance(evidence.nat_counter_packets, int) and evidence.nat_counter_packets > 0):
        missing_evidence.append("nat_counter_packets_gt_zero")
    for flag, key in [
        (evidence.conntrack_assured, "conntrack_assured"),
        (evidence.stratum_subscribe_ok, "stratum_subscribe_ok"),
        (evidence.stratum_authorize_ok, "stratum_authorize_ok"),
        (evidence.stratum_set_difficulty_seen, "stratum_set_difficulty_seen"),
        (evidence.stratum_notify_seen, "stratum_notify_seen"),
        (evidence.forwarder_pool_seen, "forwarder_pool_seen"),
        (evidence.bridge_loopback_seen, "bridge_loopback_seen"),
    ]:
        if not flag:
            missing_evidence.append(key)
    if evidence.stratum_subscribe_ok and evidence.stratum_authorize_ok and not evidence.stratum_notify_seen:
        warnings.append("stratum_notify_not_observed")
    if evidence.stratum_subscribe_ok and evidence.stratum_authorize_ok and not evidence.stratum_set_difficulty_seen:
        warnings.append("stratum_set_difficulty_not_observed")
    if not evidence.forwarder_pool_seen:
        warnings.append("forwarder_pool_seen_not_proven")
    if not evidence.bridge_loopback_seen:
        warnings.append("bridge_loopback_seen_not_proven")

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
    for key, ok in vis_map.items():
        if not ok and key not in missing_visibility:
            missing_visibility.append(key)

    for bool_field in ("proxy_doctor_ok", "bridge_healthy", "stratum_subscribe_ok", "stratum_authorize_ok"):
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
            "firewall_apply_allowed": False,
            "abuse_automation_allowed": False,
            "ui_allowed": False,
            "telegram_allowed": False,
            "scheduler_allowed": False,
            "worker_enforcement_allowed": False,
            "production_traffic_allowed": False,
        },
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "missing_visibility_primitives": sorted(set(missing_visibility)),
        "missing_evidence_primitives": sorted(set(missing_evidence)),
        "next_required_step": (
            next((x for x in _VISIBILITY_PRIORITY if x in set(missing_visibility)), "none")
            if missing_visibility
            else (next((x for x in _EVIDENCE_PRIORITY if x in set(missing_evidence)), "none") if missing_evidence else "none")
        ),
    }


def load_phase11_canary_acceptance_evidence_json(path: Path) -> Phase11CanaryAcceptanceEvidence:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("evidence json must be an object")
    return Phase11CanaryAcceptanceEvidence.from_dict(data)
