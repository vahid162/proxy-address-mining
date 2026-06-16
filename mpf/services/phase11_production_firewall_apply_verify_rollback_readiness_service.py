"""Read-only Phase 11 production firewall completion evidence contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mpf import __version__

READY = "production_firewall_apply_verify_rollback_ready"
MISSING_OR_PARTIAL = "missing_or_partial"
BLOCKED = "BLOCKED_PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_load_error": str(exc)}
    return data if isinstance(data, dict) else {"_load_error": "json_root_not_object"}


def _first_existing(evidence_dir: Path, names: tuple[str, ...]) -> tuple[Path | None, dict[str, Any]]:
    for name in names:
        path = evidence_dir / name
        if path.exists():
            return path, _load_json(path)
    return None, {}


def _as_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else ([] if value in (None, "") else [value])


def build_production_firewall_apply_verify_rollback_readiness_report(evidence_dir: Path | str | None) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    evidence_path = Path(evidence_dir) if evidence_dir is not None else None
    files: dict[str, str | None] = {}
    if evidence_path is None:
        blockers.extend([
            "firewall_completion_evidence_dir_missing",
            "firewall_apply_evidence_missing",
            "firewall_post_apply_verify_missing",
            "firewall_rollback_contract_missing",
            "firewall_restore_point_or_backup_missing",
        ])
        gate: dict[str, Any] = {}
        package: dict[str, Any] = {}
        apply: dict[str, Any] = {}
        verify: dict[str, Any] = {}
        rollback: dict[str, Any] = {}
    elif not evidence_path.exists() or not evidence_path.is_dir():
        blockers.extend([
            "firewall_completion_evidence_dir_not_found",
            "firewall_apply_evidence_missing",
            "firewall_post_apply_verify_missing",
            "firewall_rollback_contract_missing",
            "firewall_restore_point_or_backup_missing",
        ])
        gate = package = apply = verify = rollback = {}
    else:
        gate_path, gate = _first_existing(evidence_path, ("current-controlled-artifact-gate-with-target.json", "current-controlled-artifact-gate.json"))
        package_path, package = _first_existing(evidence_path, ("controlled-artifact-reapply-package.json", "firewall-apply-package.json", "package.json"))
        apply_path, apply = _first_existing(evidence_path, ("controlled-artifact-reapply-execute.json", "firewall-apply-evidence.json", "apply-evidence.json"))
        verify_path, verify = _first_existing(evidence_path, ("controlled-artifact-reapply-verify.json", "firewall-post-apply-verify.json", "post-apply-verify.json"))
        rollback_path, rollback = _first_existing(evidence_path, ("controlled-artifact-reapply-rollback.json", "firewall-rollback-contract.json", "rollback-contract.json", "rollback-evidence.json"))
        files = {"artifact_gate": str(gate_path.name) if gate_path else None, "package": str(package_path.name) if package_path else None, "apply": str(apply_path.name) if apply_path else None, "post_apply_verify": str(verify_path.name) if verify_path else None, "rollback": str(rollback_path.name) if rollback_path else None}
        if not gate_path or gate.get("_load_error"):
            blockers.append("firewall_artifact_gate_not_clean")
        if not apply_path or apply.get("_load_error"):
            blockers.append("firewall_apply_evidence_missing")
        if not verify_path or verify.get("_load_error"):
            blockers.append("firewall_post_apply_verify_missing")
        if not rollback_path or rollback.get("_load_error"):
            blockers.append("firewall_rollback_contract_missing")
        if not package_path or package.get("_load_error"):
            blockers.append("firewall_package_evidence_missing")

    unknown = _as_list(gate.get("unknown_mpf_artifacts"))
    duplicate_count = int(gate.get("duplicate_nat_redirect_count") or 0) if str(gate.get("duplicate_nat_redirect_count") or "0").isdigit() else 1
    public_exposure = bool(gate.get("forbidden_public_runtime_exposure") or gate.get("backend_public_exposure"))
    gate_clean = bool(gate) and not gate.get("_load_error") and not unknown and duplicate_count == 0 and not public_exposure
    if gate and not gate_clean:
        blockers.append("firewall_artifact_gate_not_clean")
    if unknown:
        blockers.append("firewall_unknown_mpf_artifacts_detected")
    if duplicate_count:
        blockers.append("firewall_duplicate_nat_redirects_detected")
    if public_exposure:
        blockers.append("firewall_public_exposure_detected")

    scope = apply.get("accepted_customer_ports") or apply.get("customer_ports") or package.get("accepted_customer_ports") or package.get("customer_ports")
    if not scope:
        blockers.append("firewall_evidence_scope_mismatch")
    if not (package.get("package_id") and package.get("package_sha256")):
        blockers.append("firewall_package_identity_missing")
    if not (apply.get("operator") or apply.get("operator_id")) or not apply.get("reason"):
        blockers.append("firewall_operator_or_reason_missing")
    if not (apply.get("restore_point_id") or apply.get("backup_id") or apply.get("backup_sha256") or package.get("backup_requirements")):
        blockers.append("firewall_restore_point_or_backup_missing")
    if not (package.get("preflight_ready") is True or package.get("final_decision") in {"CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY", "READY_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"}):
        blockers.append("firewall_preflight_not_ready")
    if apply and apply.get("firewall_apply_performed") is not True:
        blockers.append("firewall_apply_evidence_missing")
    if verify and not (verify.get("post_apply_verify_ready") is True or str(verify.get("final_decision", "")).endswith("VERIFY_READY")):
        blockers.append("firewall_post_apply_verify_missing")
    if rollback and not (rollback.get("rollback_contract_ready") is True or rollback.get("rollback_plan_ready") is True or rollback.get("restore_contract_ready") is True):
        blockers.append("firewall_rollback_contract_missing")
    for mutation_key, blocker in (("docker_restart_performed", "firewall_forbidden_docker_mutation_detected"), ("systemd_restart_performed", "firewall_forbidden_systemd_mutation_detected"), ("conntrack_flush_performed", "firewall_forbidden_conntrack_mutation_detected")):
        if apply.get(mutation_key) is True or verify.get(mutation_key) is True or rollback.get(mutation_key) is True:
            blockers.append(blocker)

    blockers = sorted(set(blockers))
    ready = not blockers
    return {
        "component": "phase11_production_firewall_apply_verify_rollback_readiness",
        "repository_version": __version__,
        "evidence_dir": str(evidence_path) if evidence_path else None,
        "evidence_files": files,
        "surface_package_preflight_ready": bool(package) and "firewall_package_evidence_missing" not in blockers and "firewall_preflight_not_ready" not in blockers,
        "production_firewall_apply_verify_rollback": READY if ready else MISSING_OR_PARTIAL,
        "artifact_gate_clean": gate_clean,
        "unknown_mpf_artifacts": unknown,
        "duplicate_nat_redirect_count": duplicate_count,
        "forbidden_public_runtime_exposure": public_exposure,
        "phase12_start_allowed": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "blockers": blockers,
        "warnings": warnings,
        "final_decision": "PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE_READY" if ready else BLOCKED,
        "next_required_step": "production_firewall_apply_verify_rollback",
    }
