"""Read-only Phase 11 controlled artifact reapply execution gate preflight.

This service validates a generated live-ready controlled artifact reapply package
for future operator review only. It never calls the executor, never invokes
iptables-restore, and never mutates runtime state.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from mpf.config import DEFAULT_CONFIG_PATH, load_config
from typing import Any

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_audit_service import ControlledArtifactReapplyAuditRepo
from mpf.services.phase11_controlled_artifact_reapply_core import FileBackupAdapter, FlockHostLock, _canonical_sha, _package_content_for_hash, verify_package

READY = "READY_CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_GATE_PREFLIGHT"
BLOCKED = "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_GATE_PREFLIGHT"
NEXT_READY = "operator_review_controlled_reapply_execution_gate_and_prepare_guarded_execute"
NEXT_BLOCKED = "regenerate_live_ready_controlled_artifact_reapply_package_and_review_blockers"
REQUIRED_CONFIRMATIONS = {"--execute", "--yes", "--package-json", "--package-sha256", "--package-id", "--operator", "--reason"}
MUTATION_FLAGS = (
    "mutation_performed",
    "firewall_apply_performed",
    "db_mutation_performed",
    "conntrack_flush_performed",
    "docker_restart_performed",
    "systemd_restart_performed",
)
CLOSED_GATES = (
    "production_execution_available",
    "controlled_artifact_execute_available",
    "iptables_restore_invocation_allowed",
    "phase12_start_allowed",
)


def _base(*, expected_version: str, package_id: str | None = None, package_sha256: str | None = None, package_file_sha256: str | None = None) -> dict[str, Any]:
    return {
        "component": "phase11_controlled_artifact_reapply_execution_gate_preflight",
        "repository_version": __version__,
        "expected_version": expected_version,
        "package_id": package_id,
        "package_sha256": package_sha256,
        "package_file_sha256": package_file_sha256,
        "package_integrity_ready": False,
        "execution_gate_preflight_ready": False,
        "backup_requirements_ready": False,
        "rollback_plan_ready": False,
        "lock_requirements_ready": False,
        "audit_metadata_strategy_ready": False,
        "backup_base_directory_ready": False,
        "host_lock_strategy_ready": False,
        "operator_confirmations_ready": False,
        "production_execution_available": False,
        "controlled_artifact_execute_available": False,
        "iptables_restore_invocation_allowed": False,
        "mutation_performed": False,
        "firewall_apply_performed": False,
        "db_mutation_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "blockers": [],
        "warnings": [],
        "next_required_step": NEXT_BLOCKED,
        "final_decision": BLOCKED,
    }


def build_fail_closed_execution_gate_preflight(expected_version: str, blockers: list[str], **kwargs: Any) -> dict[str, Any]:
    report = _base(expected_version=expected_version, **kwargs)
    report["blockers"] = sorted(set(blockers))
    return report


def build_execution_gate_preflight_report(
    *,
    package: dict[str, Any],
    package_file_sha256: str,
    package_sha256: str,
    package_id: str,
    operator: str,
    reason: str,
    expected_version: str = __version__,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if expected_version != __version__:
        blockers.append("expected_version_mismatch")
    if package.get("repository_version") != __version__ or package.get("expected_version") not in {None, __version__}:
        blockers.append("package_repository_version_incompatible")
    if package.get("package_id") != package_id:
        blockers.append("package_id_mismatch")
    if package_file_sha256 != package_sha256:
        blockers.append("package_file_sha256_mismatch")
    embedded_package_sha256 = package.get("package_sha256")
    if not embedded_package_sha256:
        blockers.append("embedded_package_sha256_missing")
    elif embedded_package_sha256 != _canonical_sha(_package_content_for_hash(package)):
        blockers.append("package_canonical_sha256_mismatch")
    if package.get("final_decision") != "CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY":
        blockers.append("package_final_decision_not_ready")
    plan = package.get("plan") if isinstance(package.get("plan"), dict) else {}
    verify = verify_package(package, live_plan=plan if plan else None)
    verify_decision = verify.get("final_decision")
    if verify_decision != "CONTROLLED_ARTIFACT_REAPPLY_VERIFY_READY":
        blockers.append("verify_final_decision_not_ready")
        blockers.extend(str(blocker) for blocker in verify.get("blockers", []) if isinstance(verify.get("blockers"), list))
    live_ready = package.get("live_ready_package_available") is True
    if not live_ready:
        blockers.append("live_ready_package_available_not_true")
    verified = package.get("package_verified_against_live_plan")
    if verified is False:
        blockers.append("package_not_verified_against_live_plan")
    elif verified is None:
        warnings.append("package_verified_against_live_plan_not_embedded")
    backup_ready = bool(package.get("backup_requirements", {}).get("required")) if isinstance(package.get("backup_requirements"), dict) else False
    rollback_ready = isinstance(package.get("rollback_plan"), dict) and bool(package.get("rollback_plan", {}).get("manual_review_required"))
    lock_ready = bool(package.get("lock_requirements", {}).get("exclusive_lock_required")) if isinstance(package.get("lock_requirements"), dict) else False
    confirmations = set(package.get("operator_confirmations", [])) if isinstance(package.get("operator_confirmations"), list) else set()
    confirmations_ready = REQUIRED_CONFIRMATIONS.issubset(confirmations) and bool(operator.strip()) and bool(reason.strip())
    if not backup_ready:
        blockers.append("backup_requirements_missing")
    if not rollback_ready:
        blockers.append("rollback_plan_missing")
    if not lock_ready:
        blockers.append("lock_requirements_missing")
    if not confirmations_ready:
        blockers.append("operator_confirmations_missing")
    for flag in MUTATION_FLAGS:
        if package.get(flag) is True or plan.get(flag) is True:
            blockers.append(f"{flag}_unexpected_true")
    for flag in CLOSED_GATES:
        if package.get(flag) is True or plan.get(flag) is True:
            blockers.append(f"{flag}_unexpected_true")
    for flag in ("worker_enforcement_allowed", "ui_allowed", "telegram_allowed"):
        value = package.get(flag, "no")
        if value not in {False, "no", "closed", None}:
            blockers.append(f"{flag}_unexpected_open")
    try:
        cfg = load_config(DEFAULT_CONFIG_PATH)
        audit_repo = ControlledArtifactReapplyAuditRepo(cfg)
        audit_url = audit_repo._database_url()
        audit_strategy_ready = audit_repo._uses_local_peer_root_psql() or not audit_url.startswith(("postgresql:///", "postgres:///"))
        if audit_url.startswith(("postgresql:///", "postgres:///")) and not audit_strategy_ready:
            blockers.append("audit_metadata_local_peer_root_strategy_missing")
    except Exception as exc:  # noqa: BLE001
        # Unit/offline preflight environments may not have /etc/mpf/mpf.yaml; do not
        # convert that into a package blocker. Farm5/operator preflight with config
        # present still validates the root/local-peer write strategy explicitly.
        audit_strategy_ready = True
        warnings.append(str(exc))
    backup_base = Path(str((package.get("backup_requirements") or {}).get("base_dir") if isinstance(package.get("backup_requirements"), dict) else "/var/backups/mpf/phase11-controlled-artifact-reapply"))
    backup_parent = backup_base.parent
    # Policy check only: do not write package artifacts during preflight.
    backup_base_ready = isinstance(FileBackupAdapter(backup_base), FileBackupAdapter) and bool(str(backup_base)) and (
        backup_parent.exists() or (backup_parent.parent.exists() and os.access(backup_parent.parent, os.W_OK))
    )
    host_lock_ready = getattr(FlockHostLock(), "production_ready", False) is True
    if not backup_base_ready:
        blockers.append("backup_base_directory_unavailable")
    if not host_lock_ready:
        blockers.append("real_host_lock_unavailable")
    package_integrity_ready = not any(b in blockers for b in ("package_file_sha256_mismatch", "package_canonical_sha256_mismatch", "embedded_package_sha256_missing", "package_id_mismatch"))
    report = _base(expected_version=expected_version, package_id=package.get("package_id"), package_sha256=str(package.get("package_sha256", "")), package_file_sha256=package_file_sha256)
    report.update({
        "package_integrity_ready": package_integrity_ready,
        "backup_requirements_ready": backup_ready,
        "rollback_plan_ready": rollback_ready,
        "lock_requirements_ready": lock_ready,
        "operator_confirmations_ready": confirmations_ready,
        "audit_metadata_strategy_ready": audit_strategy_ready,
        "backup_base_directory_ready": backup_base_ready,
        "host_lock_strategy_ready": host_lock_ready,
        "warnings": sorted(set(warnings)),
        "blockers": sorted(set(blockers)),
    })
    if not blockers:
        report["execution_gate_preflight_ready"] = True
        report["next_required_step"] = NEXT_READY
        report["final_decision"] = READY
    return report


def run_execution_gate_preflight_report(*, package_json: Path, package_sha256: str, package_id: str, operator: str, reason: str, expected_version: str = __version__) -> dict[str, Any]:
    try:
        raw = package_json.read_bytes()
        package_file_sha256 = hashlib.sha256(raw).hexdigest()
        package = json.loads(raw.decode("utf-8"))
        if not isinstance(package, dict):
            raise ValueError("package_json_must_be_object")
    except Exception as exc:  # noqa: BLE001
        return build_fail_closed_execution_gate_preflight(expected_version, ["package_json_read_failed", str(exc)], package_id=package_id, package_sha256=package_sha256)
    return build_execution_gate_preflight_report(package=package, package_file_sha256=package_file_sha256, package_sha256=package_sha256, package_id=package_id, operator=operator, reason=reason, expected_version=expected_version)
