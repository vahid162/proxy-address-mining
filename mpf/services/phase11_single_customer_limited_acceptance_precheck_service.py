from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

EXPECTED = {
    "candidate_customer_key": "limited-btc-001",
    "candidate_lane": "btc",
    "candidate_public_port": 20101,
    "candidate_backend_target": "172.18.0.3:60010",
}
SOURCE_VISIBILITY_VERSION = "0.1.218"
ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS = {SOURCE_VISIBILITY_VERSION, __version__}
REPORT_SAFE_FLAGS = [
    "production_traffic_enabled",
    "miner_traffic_allowed",
    "abuse_automation_enabled",
    "phase11_accepted",
    "db_activation_allowed",
    "mutation_performed",
]
VISIBILITY_SAFE_FLAGS = [
    "production_traffic_enabled",
    "miner_traffic_allowed",
    "phase11_accepted",
    "db_activation_allowed",
    "mutation_performed",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, blockers: list[str], missing: str, invalid: str) -> dict[str, object] | None:
    if not path.exists() or not path.is_file():
        blockers.append(missing)
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        blockers.append(invalid)
        return None
    if not isinstance(obj, dict):
        blockers.append(invalid)
        return None
    return obj


def _validate_visibility_bundle(obj: dict[str, object] | None, blockers: list[str]) -> None:
    if obj is None:
        return
    if obj.get("final_decision") != "PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY" or obj.get("visibility_bundle_ready") is not True:
        blockers.append("visibility_bundle_not_ready")
    for key, expected in EXPECTED.items():
        if obj.get(key) != expected:
            blockers.append(f"visibility_bundle_scope_mismatch:{key}")
    for flag in VISIBILITY_SAFE_FLAGS:
        if obj.get(flag) is not False:
            blockers.append("visibility_bundle_safety_boundary_open")
            break
    if obj.get("expected_version") != SOURCE_VISIBILITY_VERSION:
        blockers.append("unsupported_source_visibility_bundle_version")
    if str(obj.get("repository_version")) not in ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS:
        blockers.append("unsupported_source_visibility_bundle_repository_version")


def _validate_readiness_report(
    obj: dict[str, object] | None,
    blockers: list[str],
    *,
    report_name: str,
    ready_key: str,
    visibility_sha: str | None,
    expected_version: str,
) -> None:
    if obj is None:
        return
    if obj.get(ready_key) is not True:
        blockers.append(f"{report_name}_not_ready")
    if obj.get("expected_version") not in (expected_version, __version__):
        blockers.append(f"{report_name}_expected_version_mismatch")
    if obj.get("repository_version") != __version__:
        blockers.append(f"{report_name}_repository_version_mismatch")
    if obj.get("source_visibility_bundle_version") != SOURCE_VISIBILITY_VERSION:
        blockers.append(f"{report_name}_source_visibility_bundle_version_mismatch")
    if str(obj.get("source_visibility_bundle_repository_version")) not in ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS:
        blockers.append(f"{report_name}_source_visibility_bundle_repository_version_mismatch")
    if visibility_sha is not None and obj.get("visibility_bundle_sha256") != visibility_sha:
        blockers.append(f"{report_name}_visibility_bundle_sha256_mismatch")
    for key, expected in EXPECTED.items():
        if obj.get(key) != expected:
            blockers.append(f"{report_name}_scope_mismatch:{key}")
    for flag in REPORT_SAFE_FLAGS:
        if obj.get(flag) is not False:
            blockers.append(f"{report_name}_safety_boundary_open")
            break


def build_phase11_single_customer_limited_acceptance_precheck_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = str(kwargs.get("expected_version", __version__))
    visibility_sha = kwargs.get("visibility_bundle_json_sha256")
    visibility_sha_str = str(visibility_sha) if visibility_sha is not None else None

    for confirmation in [
        "operator_confirmed",
        "i_understand_precheck_only",
        "i_understand_no_customer_activation",
        "i_understand_no_production_traffic_acceptance",
        "i_understand_no_miner_traffic_acceptance",
        "i_understand_no_db_activation",
    ]:
        if kwargs.get(confirmation) is not True:
            blockers.append(f"missing_confirmation:{confirmation}")

    visibility_path = Path(str(kwargs.get("visibility_bundle_json", "")))
    abuse_path = Path(str(kwargs.get("abuse_1h_readiness_json", "")))
    restart_path = Path(str(kwargs.get("restart_container_order_readiness_json", "")))

    visibility = _load(visibility_path, blockers, "visibility_bundle_missing", "visibility_bundle_invalid")
    abuse = _load(abuse_path, blockers, "abuse_readiness_missing", "abuse_readiness_invalid")
    restart = _load(restart_path, blockers, "restart_readiness_missing", "restart_readiness_invalid")

    for obj, path, expected_sha, tag in [
        (visibility, visibility_path, visibility_sha, "visibility"),
        (abuse, abuse_path, kwargs.get("abuse_1h_readiness_json_sha256"), "abuse"),
        (restart, restart_path, kwargs.get("restart_container_order_readiness_json_sha256"), "restart"),
    ]:
        if obj is not None and expected_sha is not None and _sha(path) != str(expected_sha):
            blockers.append(f"{tag}_sha256_mismatch")

    if any(obj is None for obj in (visibility, abuse, restart)):
        blockers.append("required_input_missing_or_invalid")

    _validate_visibility_bundle(visibility, blockers)
    _validate_readiness_report(
        abuse,
        blockers,
        report_name="abuse_readiness",
        ready_key="abuse_1h_coverage_ready",
        visibility_sha=visibility_sha_str,
        expected_version=expected_version,
    )
    _validate_readiness_report(
        restart,
        blockers,
        report_name="restart_readiness",
        ready_key="restart_container_order_ready",
        visibility_sha=visibility_sha_str,
        expected_version=expected_version,
    )

    ready = len(blockers) == 0
    return {
        "component": "phase11_single_customer_limited_acceptance_precheck",
        "expected_version": expected_version,
        "source_visibility_bundle_version": visibility.get("expected_version") if isinstance(visibility, dict) else None,
        "source_visibility_bundle_repository_version": visibility.get("repository_version") if isinstance(visibility, dict) else None,
        "repository_version": __version__,
        "candidate_customer_key": EXPECTED["candidate_customer_key"],
        "candidate_lane": EXPECTED["candidate_lane"],
        "candidate_public_port": EXPECTED["candidate_public_port"],
        "candidate_backend_target": EXPECTED["candidate_backend_target"],
        "visibility_bundle_sha256": visibility_sha_str,
        "visibility_bundle_ready": bool(visibility and visibility.get("visibility_bundle_ready") is True),
        "abuse_1h_coverage_ready": bool(abuse and abuse.get("abuse_1h_coverage_ready") is True),
        "restart_container_order_ready": bool(restart and restart.get("restart_container_order_ready") is True),
        "limited_acceptance_precheck_ready": ready,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "abuse_automation_enabled": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "next_required_step": "explicit_limited_customer_activation_decision_pr" if ready else "resolve_missing_phase11e_readiness_gates",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_LIMITED_ACCEPTANCE_PRECHECK_READY" if ready else "BLOCKED",
    }
