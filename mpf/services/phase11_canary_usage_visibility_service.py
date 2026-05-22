from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service, phase11_live_canary_evidence_collector_service
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence


@dataclass(slots=True)
class Phase11CanaryUsageVisibilityEvidence:
    captured_at: str | None = None
    captured_by: str | None = None
    evidence_source: str | None = None
    evidence_reference: str | None = None
    customer_key: str | None = None
    lane: str | None = None
    port: int | None = None
    backend_target: str | None = None
    usage_visibility_ok: bool = False
    usage_reference: str | None = None
    total_connections: int | None = None
    accepted_connections: int | None = None
    total_bytes: int | None = None
    total_shares: int | None = None
    last_seen_at: str | None = None
    sample_window_seconds: int | None = None
    source_query_or_artifact: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Phase11CanaryUsageVisibilityEvidence":
        kwargs = {f: data[f] for f in cls.__dataclass_fields__ if f in data}
        return cls(**kwargs)


def load_phase11_canary_usage_visibility_evidence_json(path: Path) -> Phase11CanaryUsageVisibilityEvidence:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("evidence json must be an object")
    return Phase11CanaryUsageVisibilityEvidence.from_dict(data)


def build_phase11_canary_usage_visibility_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, collect_live: bool = False, evidence: Phase11CanaryUsageVisibilityEvidence | None = None) -> dict[str, object]:
    evidence = evidence or Phase11CanaryUsageVisibilityEvidence()
    warnings: list[str] = []
    blockers: list[str] = []

    live_ev = Phase11CanaryAcceptanceEvidence()
    if collect_live:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version)
        live_ev = Phase11CanaryAcceptanceEvidence.from_dict(live.get("evidence", {}))

    customer_list = customer_read_service.list_customer_status(config, include_deleted=False, limit=1000)
    active_customers = customer_list.customers if customer_list.ok else []
    customer_db_visible = any(c.customer_key == customer_key and c.lane == lane and c.port == port for c in active_customers)
    if not customer_list.ok:
        warnings.append("customer_list_read_failed")

    expected_target = live_ev.canary_nat_target
    exact_scope_ok = (
        evidence.customer_key == customer_key
        and evidence.lane == lane
        and evidence.port == port
        and (not evidence.backend_target or not expected_target or evidence.backend_target == expected_target)
    )

    has_counter = any((evidence.total_connections or 0) > 0 for _ in [0]) or any([
        (evidence.accepted_connections or 0) > 0,
        (evidence.total_bytes or 0) > 0,
        (evidence.total_shares or 0) > 0,
    ])

    status = "MISSING"
    source = evidence.evidence_source or "missing_source_backed_canary_usage_counters"
    reference = evidence.usage_reference or evidence.evidence_reference
    details = ["source-backed exact-scope canary usage evidence is required"]
    usage_blockers: list[str] = ["missing_source_backed_canary_usage_counters"]

    if not customer_db_visible:
        status = "BLOCKED"
        usage_blockers = ["missing_canary_customer_db_visibility"]
        details = ["canary DB visibility is required first"]
    elif evidence.usage_visibility_ok and not reference:
        warnings.append("usage_visibility_ok_true_without_reference")
    elif evidence.usage_visibility_ok and not exact_scope_ok:
        status = "BLOCKED"
        usage_blockers = ["usage_visibility_evidence_scope_mismatch"]
        blockers.append("usage_visibility_evidence_scope_mismatch")
    elif evidence.usage_visibility_ok and reference and exact_scope_ok and has_counter:
        status = "PRESENT"
        source = evidence.evidence_source or "usage_evidence"
        details = ["exact-scope source-backed canary usage evidence present"]
        usage_blockers = []

    final_decision = "USAGE_VISIBILITY_READY" if status == "PRESENT" and not blockers else ("BLOCKED" if status == "BLOCKED" or blockers else "MISSING_USAGE_VISIBILITY")
    next_required_step = "none" if final_decision == "USAGE_VISIBILITY_READY" else ("canary_customer_db_visibility" if "missing_canary_customer_db_visibility" in usage_blockers else "usage_counters_visibility")

    return {
        "component": "phase11_canary_usage_visibility",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "backend_target": expected_target,
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
        "source": source,
        "reference": reference,
        "customer_db_visible": customer_db_visible,
        "usage_counters_visibility": {"status": status, "source": source, "reference": reference, "details": details, "blockers": usage_blockers},
        "runtime_evidence": {
            "nat_counter_packets": live_ev.nat_counter_packets,
            "nat_counter_bytes": live_ev.nat_counter_bytes,
            "canary_nat_rule_present": live_ev.canary_nat_rule_present,
            "canary_nat_target": live_ev.canary_nat_target,
            "proxy_doctor_ok": live_ev.proxy_doctor_ok,
        },
        "blockers": sorted(set(blockers + usage_blockers)),
        "warnings": sorted(set(warnings)),
        "next_required_step": next_required_step,
        "final_decision": final_decision,
    }
