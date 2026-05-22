from __future__ import annotations

import getpass
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, UTC
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service, phase11_canary_usage_visibility_service, phase11_live_canary_evidence_collector_service
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence


def build_phase11_canary_usage_evidence_capture_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, collect_live: bool = False) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    live_ev = Phase11CanaryAcceptanceEvidence()
    if collect_live:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version)
        live_ev = Phase11CanaryAcceptanceEvidence.from_dict(live.get("evidence", {}))

    customers = customer_read_service.list_customer_status(config, include_deleted=False, limit=1000)
    active = customers.customers if customers.ok else []
    customer_db_visible = any(c.customer_key == customer_key and c.lane == lane and c.port == port for c in active)
    if not customer_db_visible:
        blockers.append("missing_canary_customer_db_visibility")
    if not live_ev.canary_nat_rule_present:
        blockers.append("missing_canary_nat_rule")
    if live_ev.canary_nat_rule_count != 1:
        blockers.append("canary_nat_rule_not_exactly_one")
    if not live_ev.no_extra_customer_nat_rules:
        blockers.append("extra_customer_nat_rules_present")
    if not live_ev.no_unexpected_mpf_firewall_references:
        blockers.append("unexpected_mpf_firewall_references")
    if not live_ev.proxy_doctor_ok:
        blockers.append("proxy_doctor_not_ok")

    has_nat_usage = (live_ev.nat_counter_packets or 0) > 0 or (live_ev.nat_counter_bytes or 0) > 0
    capture_ts = datetime.now(UTC).isoformat()
    ref_seed = f"{customer_key}:{lane}:{port}:{live_ev.canary_nat_target}:{live_ev.nat_counter_packets}:{live_ev.nat_counter_bytes}:{capture_ts}"
    evidence_reference = f"live_canary_usage:{customer_key}:{lane}:{port}:{hashlib.sha256(ref_seed.encode()).hexdigest()[:12]}"
    usage_ok = not blockers and has_nat_usage
    if not has_nat_usage:
        warnings.append("nat_counters_zero")

    usage_evidence = phase11_canary_usage_visibility_service.Phase11CanaryUsageVisibilityEvidence(
        captured_at=capture_ts,
        captured_by=getpass.getuser(),
        evidence_source="live_source_backed_canary_usage",
        evidence_reference=evidence_reference,
        customer_key=customer_key,
        lane=lane,
        port=port,
        backend_target=live_ev.canary_nat_target,
        usage_visibility_ok=usage_ok,
        usage_reference=evidence_reference if usage_ok else None,
        total_connections=None,
        accepted_connections=None,
        total_bytes=live_ev.nat_counter_bytes if has_nat_usage else 0,
        total_shares=None,
        last_seen_at=capture_ts if has_nat_usage else None,
        sample_window_seconds=None,
        source_query_or_artifact=f"iptables-save-nat-counter:MPF_NAT_PRE:{port}",
    )

    final_decision = "USAGE_EVIDENCE_READY" if usage_ok else ("BLOCKED" if blockers else "MISSING_USAGE_EVIDENCE")
    return {
        "component": "phase11_canary_usage_evidence_capture",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "backend_target": live_ev.canary_nat_target,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "production_traffic_enabled": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "no_onboarding_authorized": True,
        "customer_db_visible": customer_db_visible,
        "canary_nat_rule_present": live_ev.canary_nat_rule_present,
        "canary_nat_rule_count": live_ev.canary_nat_rule_count,
        "canary_nat_target": live_ev.canary_nat_target,
        "no_extra_customer_nat_rules": live_ev.no_extra_customer_nat_rules,
        "no_unexpected_mpf_firewall_references": live_ev.no_unexpected_mpf_firewall_references,
        "proxy_doctor_ok": live_ev.proxy_doctor_ok,
        "nat_counter_packets": live_ev.nat_counter_packets,
        "nat_counter_bytes": live_ev.nat_counter_bytes,
        "usage_evidence": asdict(usage_evidence),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "next_required_step": "reject_counters_visibility" if usage_ok else "usage_counters_visibility",
        "final_decision": final_decision,
    }


def write_usage_evidence_json(*, report: dict[str, object], path: Path, overwrite: bool = False) -> None:
    if not path.parent.exists():
        raise ValueError("parent directory does not exist")
    if path.exists() and not overwrite:
        raise ValueError("evidence json path already exists; pass overwrite")
    obj = report.get("usage_evidence")
    if not isinstance(obj, dict):
        raise ValueError("usage_evidence missing")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
