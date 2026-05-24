from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from mpf import __version__

_ALLOWED_EXPECTED_VERSIONS = {__version__, "0.1.198"}
from mpf.config import MPFConfig
from mpf.domain.abuse_dry_run_evaluator import AbuseDryRunInput
from mpf.domain.taxonomy import AbuseStatus
from mpf.services import customer_read_service
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence

ALLOWED_SOURCE = "live_source_backed_canary_abuse_coverage"
_ALLOWED_FARM5_BASELINE = "0.1.168"


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
    parsed: dict[str, str] = {}
    for line in text[code_start + 7 : code_end].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed or None


def build_phase11_canary_abuse_coverage_visibility_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, collect_live: bool = False) -> dict[str, object]:
    _ = collect_live
    blockers: list[str] = []
    warnings: list[str] = []

    if expected_version not in _ALLOWED_EXPECTED_VERSIONS:
        blockers.append("expected_version_mismatch")
    if farm5_baseline_version != _ALLOWED_FARM5_BASELINE:
        blockers.append("farm5_baseline_version_not_allowed")

    customer_list = customer_read_service.list_customer_status(config, include_deleted=False, limit=1000)
    active = customer_list.customers if customer_list.ok else []
    canary_ok = any(c.customer_key == customer_key and c.lane == lane and c.port == port for c in active)
    scope_mismatch = any(c.customer_key == customer_key and (c.lane != lane or c.port != port) for c in active)
    unexpected_active = any(c.customer_key != customer_key for c in active)

    if not customer_list.ok:
        blockers.append("customer_list_read_failed")
    if not canary_ok or scope_mismatch or unexpected_active:
        blockers.append("canary_customer_db_visibility_not_exact_scope")

    taxonomy_states = {AbuseStatus.OVER_TRACKING.value, AbuseStatus.OVER_GRACE.value, AbuseStatus.HARD.value}
    source_contracts = {
        "over_tracking": "over_tracking" in taxonomy_states,
        "over_grace": "over_grace" in taxonomy_states,
        "hard": "hard" in taxonomy_states,
        "one_hour_transition_policy": AbuseDryRunInput.threshold_seconds == 3600,
    }
    if not source_contracts["over_tracking"]:
        blockers.append("missing_abuse_state_coverage:over_tracking")
    if not source_contracts["over_grace"]:
        blockers.append("missing_abuse_state_coverage:over_grace")
    if not source_contracts["hard"]:
        blockers.append("missing_abuse_state_coverage:hard")
    if not source_contracts["one_hour_transition_policy"]:
        blockers.append("missing_one_hour_abuse_transition_policy")

    phase_status_path = Path(__file__).resolve().parents[2] / "docs" / "PHASE_STATUS.md"
    current_state = _parse_current_state_block(phase_status_path.read_text(encoding="utf-8")) if phase_status_path.exists() else None
    abuse_automation_disabled = bool(current_state and current_state.get("abuse_automation_allowed") == "no")
    scheduler_disabled = bool(current_state and current_state.get("restore_lock_record_execution_allowed") == "controlled_boundary_only")
    worker_enforcement_disabled = bool(current_state and "Phase 10" in current_state.get("current_accepted_phase", "") and "Phase 11" in current_state.get("current_working_phase", ""))
    production_traffic_disabled = bool(current_state and current_state.get("production_traffic") == "none")

    if not abuse_automation_disabled:
        blockers.append("abuse_automation_not_proven_disabled")
    if not scheduler_disabled:
        blockers.append("scheduler_not_proven_disabled")
    if not worker_enforcement_disabled:
        blockers.append("worker_enforcement_not_proven_disabled")
    if not production_traffic_disabled:
        blockers.append("production_traffic_not_proven_disabled")

    abuse_coverage_ok = (
        not blockers
        and canary_ok
        and (not scope_mismatch)
        and (not unexpected_active)
        and all(source_contracts.values())
        and abuse_automation_disabled
        and scheduler_disabled
        and worker_enforcement_disabled
    )

    evidence_reference = f"canary_abuse_coverage:{customer_key}:{lane}:{port}:v{__version__}"
    evidence = Phase11CanaryVisibilityEvidence(
        evidence_source=ALLOWED_SOURCE,
        evidence_reference=evidence_reference,
        customer_key=customer_key,
        lane=lane,
        port=port,
        canary_customer_db_visible=canary_ok and (not scope_mismatch) and (not unexpected_active),
        customer_db_reference=f"active_customer:{customer_key}" if canary_ok else None,
        abuse_coverage_ok=abuse_coverage_ok,
        abuse_reference=f"source_backed_abuse_coverage:{customer_key}:{lane}:{port}",
        abuse_evidence_source=ALLOWED_SOURCE,
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
        "abuse_automation_enabled": not abuse_automation_disabled,
        "scheduler_enabled": not scheduler_disabled,
        "worker_enforcement_enabled": not worker_enforcement_disabled,
        "production_traffic_enabled": not production_traffic_disabled,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "generated_evidence": asdict(evidence),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "final_decision": "ABUSE_COVERAGE_VISIBLE" if abuse_coverage_ok else "BLOCKED",
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
