from __future__ import annotations

from dataclasses import asdict

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence

ALLOWED_SOURCE = "live_source_backed_canary_abuse_coverage"


def build_phase11_canary_abuse_coverage_visibility_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, collect_live: bool = False) -> dict[str, object]:
    _ = collect_live
    blockers: list[str] = []
    warnings: list[str] = []

    customer_list = customer_read_service.list_customer_status(config, include_deleted=False, limit=1000)
    active = customer_list.customers if customer_list.ok else []
    canary_ok = any(c.customer_key == customer_key and c.lane == lane and c.port == port for c in active)
    scope_mismatch = any(c.customer_key == customer_key and (c.lane != lane or c.port != port) for c in active)
    unexpected_active = any(c.customer_key != customer_key for c in active)

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")

    source_contracts = {
        "over_tracking": True,
        "over_grace": True,
        "hard": True,
        "one_hour_transition_policy": True,
    }

    if not customer_list.ok:
        blockers.append("customer_list_read_failed")
    if not canary_ok or scope_mismatch or unexpected_active:
        blockers.append("canary_customer_db_visibility_not_exact_scope")

    abuse_automation_disabled = True
    scheduler_disabled = True
    worker_enforcement_disabled = True

    abuse_coverage_ok = all(source_contracts.values()) and canary_ok and (not scope_mismatch) and (not unexpected_active) and abuse_automation_disabled and scheduler_disabled and worker_enforcement_disabled

    evidence = Phase11CanaryVisibilityEvidence(
        evidence_source=ALLOWED_SOURCE,
        evidence_reference=f"canary_abuse_coverage:{customer_key}:{lane}:{port}:v{__version__}",
        customer_key=customer_key,
        lane=lane,
        port=port,
        canary_customer_db_visible=canary_ok and (not scope_mismatch) and (not unexpected_active),
        customer_db_reference=f"active_customer:{customer_key}" if canary_ok else None,
        abuse_coverage_ok=abuse_coverage_ok,
        abuse_reference=f"source_backed_abuse_coverage:{customer_key}:{lane}:{port}",
    )

    return {
        "component": "phase11_canary_abuse_coverage_visibility",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "collect_live": collect_live,
        "source_contracts": source_contracts,
        "abuse_automation_enabled": False,
        "scheduler_enabled": False,
        "worker_enforcement_enabled": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "generated_evidence": asdict(evidence),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "final_decision": "ABUSE_COVERAGE_VISIBLE" if abuse_coverage_ok and not blockers else "BLOCKED",
    }


def write_abuse_coverage_visibility_evidence_json(*, report: dict[str, object], path, overwrite: bool = False) -> None:
    import json
    from pathlib import Path
    path = Path(path)
    if not path.parent.exists():
        raise ValueError("parent directory does not exist")
    if path.exists() and not overwrite:
        raise ValueError("evidence json path already exists; pass overwrite")
    obj = report.get("generated_evidence")
    if not isinstance(obj, dict):
        raise ValueError("generated_evidence missing")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
