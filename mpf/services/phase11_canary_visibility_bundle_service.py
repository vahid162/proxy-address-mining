from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service, phase11_live_canary_evidence_collector_service, phase11_canary_usage_visibility_service
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence


@dataclass(slots=True)
class Phase11CanaryVisibilityEvidence:
    captured_at: str | None = None
    captured_by: str | None = None
    evidence_source: str | None = None
    evidence_reference: str | None = None
    customer_key: str | None = None
    lane: str | None = None
    port: int | None = None
    backend_target: str | None = None
    canary_customer_db_visible: bool = False
    customer_db_reference: str | None = None
    usage_visibility_ok: bool = False
    usage_reference: str | None = None
    total_connections: int | None = None
    accepted_connections: int | None = None
    total_bytes: int | None = None
    total_shares: int | None = None
    last_seen_at: str | None = None
    sample_window_seconds: int | None = None
    source_query_or_artifact: str | None = None
    reject_visibility_ok: bool = False
    reject_reference: str | None = None
    session_visibility_ok: bool = False
    session_reference: str | None = None
    unique_ip_visibility_ok: bool = False
    unique_ip_reference: str | None = None
    worker_visibility_ok: bool = False
    worker_reference: str | None = None
    abuse_coverage_ok: bool = False
    abuse_reference: str | None = None
    final_check_report_ok: bool = False
    final_check_report_reference: str | None = None
    rollback_or_restore_plan_ok: bool = False
    rollback_reference: str | None = None
    restore_reference: str | None = None
    conntrack_assured: bool = False
    stratum_subscribe_ok: bool = False
    stratum_authorize_ok: bool = False
    stratum_set_difficulty_seen: bool = False
    stratum_notify_seen: bool = False
    forwarder_pool_seen: bool = False
    bridge_loopback_seen: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Phase11CanaryVisibilityEvidence":
        kwargs = {f: data[f] for f in cls.__dataclass_fields__ if f in data}
        return cls(**kwargs)


def _item(status: str, source: str, reference: str | None, details: list[str], blockers: list[str]) -> dict[str, object]:
    return {"status": status, "source": source, "reference": reference, "details": details, "blockers": blockers}


def load_phase11_canary_visibility_evidence_json(path: Path) -> Phase11CanaryVisibilityEvidence:
    return Phase11CanaryVisibilityEvidence.from_dict(json.loads(path.read_text(encoding="utf-8")))


def build_phase11_canary_visibility_bundle_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, collect_live: bool = False, evidence: Phase11CanaryVisibilityEvidence | None = None) -> dict[str, object]:
    warnings: list[str] = []
    blockers: list[str] = []
    missing_visibility: list[str] = []
    missing_evidence: list[str] = []
    evidence = evidence or Phase11CanaryVisibilityEvidence()

    live_ev = Phase11CanaryAcceptanceEvidence()
    if collect_live:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version)
        live_ev = Phase11CanaryAcceptanceEvidence.from_dict(live.get("evidence", {}))
    expected_backend_target = live_ev.canary_nat_target

    customer_list = customer_read_service.list_customer_status(config, include_deleted=False, limit=1000)
    active_customers = customer_list.customers if customer_list.ok else []
    active_keys = [c.customer_key for c in active_customers]
    visible = any(c.customer_key == customer_key and c.lane == lane and c.port == port for c in active_customers)
    canary_scope_mismatch = any(c.customer_key == customer_key and (c.lane != lane or c.port != port) for c in active_customers)
    unexpected = any(c.customer_key != customer_key for c in active_customers)

    visibility = {}
    if unexpected:
        visibility["canary_customer_db_visibility"] = _item("BLOCKED", "customer_read_service", None, ["unexpected active customer exists"], ["unexpected_active_customer_present"])
    elif canary_scope_mismatch:
        visibility["canary_customer_db_visibility"] = _item("BLOCKED", "customer_read_service", f"active_customer:{customer_key}", ["active non-deleted canary row has wrong lane/port scope"], ["canary_customer_db_scope_mismatch"])
    elif visible:
        visibility["canary_customer_db_visibility"] = _item("PRESENT", "customer_read_service", f"active_customer:{customer_key}", ["active non-deleted canary row found"], [])
    else:
        if not customer_list.ok:
            warnings.append("customer_list_read_failed")
        visibility["canary_customer_db_visibility"] = _item("MISSING", "customer_read_service", None, ["no active non-deleted canary row found"], ["missing_non_deleted_canary_customer"])

    positive_requested = any([
        evidence.usage_visibility_ok, evidence.reject_visibility_ok, evidence.session_visibility_ok, evidence.unique_ip_visibility_ok,
        evidence.worker_visibility_ok, evidence.abuse_coverage_ok, evidence.final_check_report_ok, evidence.rollback_or_restore_plan_ok,
    ])
    exact_scope_ok = (
        evidence.customer_key == customer_key
        and evidence.lane == lane
        and evidence.port == port
        and (not evidence.backend_target or not expected_backend_target or evidence.backend_target == expected_backend_target)
    )
    if positive_requested and not exact_scope_ok:
        blockers.append("visibility_evidence_scope_mismatch")

    def from_evidence(name: str, ok: bool, ref: str | None, blocker: str):
        if ok and ref and exact_scope_ok:
            return _item("PRESENT", "visibility_evidence_json", ref, ["source-backed evidence present"], [])
        if ok and not ref:
            warnings.append(f"{name}_true_without_reference")
        return _item("MISSING", "phase9_surface_or_missing", ref, ["report-only surface does not satisfy canary source-backed visibility"], [blocker])

    usage_report = phase11_canary_usage_visibility_service.build_phase11_canary_usage_visibility_report(
        config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live,
        evidence=phase11_canary_usage_visibility_service.Phase11CanaryUsageVisibilityEvidence(
            captured_at=evidence.captured_at, captured_by=evidence.captured_by, evidence_source=evidence.evidence_source, evidence_reference=evidence.evidence_reference,
            customer_key=evidence.customer_key, lane=evidence.lane, port=evidence.port, backend_target=evidence.backend_target,
            usage_visibility_ok=evidence.usage_visibility_ok, usage_reference=evidence.usage_reference,
            total_connections=evidence.total_connections, accepted_connections=evidence.accepted_connections, total_bytes=evidence.total_bytes,
            total_shares=evidence.total_shares, last_seen_at=evidence.last_seen_at, sample_window_seconds=evidence.sample_window_seconds,
            source_query_or_artifact=evidence.source_query_or_artifact,
        ),
    )
    visibility["usage_counters_visibility"] = usage_report["usage_counters_visibility"]
    warnings.extend(usage_report.get("warnings", []))
    blockers.extend(usage_report.get("blockers", []))
    visibility["reject_counters_visibility"] = from_evidence("reject_visibility_ok", evidence.reject_visibility_ok, evidence.reject_reference, "missing_source_backed_canary_reject_counters")
    visibility["active_recent_sessions_visibility"] = from_evidence("session_visibility_ok", evidence.session_visibility_ok, evidence.session_reference, "missing_source_backed_canary_sessions")
    visibility["unique_ips_visibility"] = from_evidence("unique_ip_visibility_ok", evidence.unique_ip_visibility_ok, evidence.unique_ip_reference, "missing_source_backed_canary_unique_ips")
    visibility["unique_workers_visibility"] = from_evidence("worker_visibility_ok", evidence.worker_visibility_ok, evidence.worker_reference, "missing_source_backed_canary_unique_workers")

    if visibility["canary_customer_db_visibility"]["status"] != "PRESENT":
        visibility["abuse_coverage_visibility"] = _item("MISSING", "phase9_abuse_visibility", None, ["canary DB visibility is required first"], ["missing_canary_customer_for_abuse_coverage"])
    else:
        visibility["abuse_coverage_visibility"] = from_evidence("abuse_coverage_ok", evidence.abuse_coverage_ok, evidence.abuse_reference, "missing_source_backed_canary_abuse_coverage")

    visibility["final_check_report_visibility"] = from_evidence("final_check_report_ok", evidence.final_check_report_ok, evidence.final_check_report_reference, "missing_source_backed_canary_final_check_report")
    if evidence.rollback_or_restore_plan_ok and (evidence.rollback_reference or evidence.restore_reference) and exact_scope_ok:
        visibility["rollback_or_restore_plan_visibility"] = _item("PRESENT", "visibility_evidence_json", evidence.rollback_reference or evidence.restore_reference, ["concrete rollback/restore reference present"], [])
    else:
        visibility["rollback_or_restore_plan_visibility"] = _item("MISSING", "artifact_or_docs", None, ["historical text without concrete machine reference is insufficient"], ["missing_canary_rollback_or_restore_reference"])

    runtime_evidence = {
        "nat_counter_packets": live_ev.nat_counter_packets,
        "nat_counter_bytes": live_ev.nat_counter_bytes,
        "canary_nat_rule_present": live_ev.canary_nat_rule_present,
        "canary_nat_rule_count": live_ev.canary_nat_rule_count,
        "canary_nat_target": live_ev.canary_nat_target,
        "mpf_nat_pre_exists": live_ev.mpf_nat_pre_exists,
        "prerouting_hook_present": live_ev.prerouting_hook_present,
        "no_extra_customer_nat_rules": live_ev.no_extra_customer_nat_rules,
        "no_unexpected_mpf_firewall_references": live_ev.no_unexpected_mpf_firewall_references,
        "proxy_doctor_ok": live_ev.proxy_doctor_ok,
        "bridge_healthy": live_ev.bridge_healthy,
        "bridge_reachable_from_forwarder": live_ev.bridge_reachable_from_forwarder,
        "v2raya_ui_local_only": live_ev.v2raya_ui_local_only,
        "btc_backend_local_only": live_ev.btc_backend_local_only,
        "bridge_no_host_publish": live_ev.bridge_no_host_publish,
        "forwarder_uses_bridge_upstream": live_ev.forwarder_uses_bridge_upstream,
        "direct_v2raya_20170_blocked": live_ev.direct_v2raya_20170_blocked,
        "conntrack_assured": evidence.conntrack_assured or live_ev.conntrack_assured,
        "stratum_subscribe_ok": evidence.stratum_subscribe_ok,
        "stratum_authorize_ok": evidence.stratum_authorize_ok,
        "stratum_set_difficulty_seen": evidence.stratum_set_difficulty_seen,
        "stratum_notify_seen": evidence.stratum_notify_seen,
        "forwarder_pool_seen": evidence.forwarder_pool_seen,
        "bridge_loopback_seen": evidence.bridge_loopback_seen,
    }

    for key, item in visibility.items():
        if item["status"] != "PRESENT":
            missing_visibility.append(key)
            blockers.extend(item["blockers"])

    for k in ["conntrack_assured", "stratum_subscribe_ok", "stratum_authorize_ok", "stratum_set_difficulty_seen", "stratum_notify_seen", "forwarder_pool_seen", "bridge_loopback_seen"]:
        if not runtime_evidence[k]:
            missing_evidence.append(k)

    final_decision = "VISIBILITY_READY" if not missing_visibility and not missing_evidence and not blockers else ("BLOCKED" if "visibility_evidence_scope_mismatch" in blockers or visibility["canary_customer_db_visibility"]["status"] == "BLOCKED" else "PARTIAL_VISIBILITY")
    next_step = missing_visibility[0] if missing_visibility else (missing_evidence[0] if missing_evidence else "none")

    return {
        "component": "phase11_canary_visibility_bundle",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "backend_target": runtime_evidence["canary_nat_target"],
        "mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "db_mutation_performed": False,
        "production_traffic_enabled": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "no_onboarding_authorized": True,
        "visibility": visibility,
        "runtime_evidence": runtime_evidence,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "missing_visibility_primitives": missing_visibility,
        "missing_evidence_primitives": missing_evidence,
        "next_required_step": next_step,
        "final_decision": final_decision,
    }
