"""Non-destructive Phase 11 backup/restore drill readiness checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mpf import __version__

READY = "backup_restore_drill_ready"
MISSING = "missing_or_partial"

_MUTATION_FLAGS = {
    "mutation_performed": False,
    "db_mutation_performed": False,
    "firewall_apply_performed": False,
    "conntrack_flush_performed": False,
    "docker_restart_performed": False,
    "systemd_restart_performed": False,
}
_GATE_FLAGS = {
    "phase12_start_allowed": False,
    "worker_enforcement_allowed": "no",
    "ui_allowed": "no",
    "telegram_allowed": "no",
}
_REQUIRED_FILES = (
    "manifest.json",
    "SHA256SUMS.txt",
    "phase-status.txt",
    "db-status.txt",
    "production-customer-lifecycle-execution-evidence.json",
    "production-firewall-apply-verify-rollback-readiness.json",
    "production-controls-pause-block-expire-readiness.json",
)
_READY_EVIDENCE = {
    "production-firewall-apply-verify-rollback-readiness.json": (
        "production_firewall_apply_verify_rollback",
        "production_firewall_apply_verify_rollback_ready",
    ),
    "production-controls-pause-block-expire-readiness.json": (
        "production_controls_pause_block_expire",
        "production_controls_pause_block_expire_ready",
    ),
}


def _base_report(evidence_dir: Path | str | None, blockers: list[str], warnings: list[str], checked: list[dict[str, Any]]) -> dict[str, Any]:
    ready = not blockers
    return {
        "component": "phase11_backup_restore_drill_readiness",
        "repository_version": __version__,
        "backup_restore_drill": READY if ready else MISSING,
        "backup_restore_drill_ready": ready,
        "evidence_dir": str(evidence_dir) if evidence_dir is not None else None,
        "checked_artifacts": checked,
        "blockers": blockers,
        "warnings": warnings,
        "final_decision": "BACKUP_RESTORE_DRILL_READY" if ready else "BLOCKED_BACKUP_RESTORE_DRILL",
        "next_required_step": "full_cli_production_operations" if ready else "backup_restore_drill",
        **_MUTATION_FLAGS,
        **_GATE_FLAGS,
    }


def _read_json(path: Path, blockers: list[str]) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - fail closed on evidence parse errors.
        blockers.append(f"invalid_json:{path.name}:{exc}")
        return None
    if not isinstance(data, dict):
        blockers.append(f"json_root_not_object:{path.name}")
        return None
    return data


def _validate_sha256s(evidence_path: Path, blockers: list[str], checked: list[dict[str, Any]]) -> None:
    sums = evidence_path / "SHA256SUMS.txt"
    if not sums.exists():
        return
    for line_number, raw in enumerate(sums.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            blockers.append(f"sha256_manifest_malformed_line:{line_number}")
            continue
        expected, rel = parts
        rel = rel.lstrip("*")
        target = (evidence_path / rel).resolve()
        try:
            target.relative_to(evidence_path.resolve())
        except ValueError:
            blockers.append(f"sha256_manifest_path_escapes_evidence_dir:{rel}")
            continue
        if not target.exists():
            blockers.append(f"sha256_manifest_artifact_missing:{rel}")
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        ok = actual == expected
        checked.append({"path": rel, "kind": "sha256_manifest_entry", "present": True, "sha256_ok": ok})
        if not ok:
            blockers.append(f"sha256_mismatch:{rel}")


def build_phase11_backup_restore_drill_readiness_report(evidence_dir: Path | str | None) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    checked: list[dict[str, Any]] = []
    if evidence_dir is None:
        blockers.append("evidence_dir_missing")
        return _base_report(evidence_dir, blockers, warnings, checked)
    root = Path(evidence_dir)
    if not root.is_dir():
        blockers.append("evidence_dir_not_found")
        return _base_report(evidence_dir, blockers, warnings, checked)

    for name in _REQUIRED_FILES:
        p = root / name
        checked.append({"path": name, "kind": "required_evidence", "present": p.is_file()})
        if not p.is_file():
            blockers.append(f"required_evidence_missing:{name}")

    manifest = _read_json(root / "manifest.json", blockers) if (root / "manifest.json").is_file() else None
    if manifest is not None:
        for field in ("files", "mutation_flags", "source_evidence_mutation_flags"):
            if field not in manifest:
                blockers.append(f"manifest_missing_{field}")
        backup_fields = ("backup_roots", "backup_root", "backup_dir", "backup_artifacts", "lifecycle_execution_evidence")
        if not any(manifest.get(field) for field in backup_fields):
            blockers.append("manifest_missing_backup_artifact_or_root_reference")

    for filename, (key, value) in _READY_EVIDENCE.items():
        path = root / filename
        if not path.is_file():
            continue
        data = _read_json(path, blockers)
        if data is None:
            continue
        if data.get(key) != value:
            blockers.append(f"readiness_not_ready:{filename}")
        if data.get("blockers") not in ([], None):
            blockers.append(f"readiness_has_blockers:{filename}")
        for flag, expected in {**_MUTATION_FLAGS, **_GATE_FLAGS}.items():
            if data.get(flag, expected) != expected:
                blockers.append(f"unsafe_flag:{filename}:{flag}")

    lifecycle = root / "production-customer-lifecycle-execution-evidence.json"
    if lifecycle.is_file():
        data = _read_json(lifecycle, blockers)
        if data is not None:
            if not (data.get("backup_artifact") or data.get("backup_path") or data.get("restore_point") or data.get("restore_point_id")):
                blockers.append("lifecycle_evidence_missing_backup_or_restore_point_reference")

    phase_status = root / "phase-status.txt"
    if phase_status.is_file():
        text = phase_status.read_text(encoding="utf-8", errors="replace")
        for required in ("phase12_start_allowed: no", "worker_enforcement_allowed: no", "ui_allowed: no", "telegram_allowed: no"):
            if required not in text:
                blockers.append(f"phase_status_missing_closed_gate:{required}")

    _validate_sha256s(root, blockers, checked)
    if not (root / "restore-drill-target-isolation.json").is_file():
        warnings.append("restore_drill_target_isolation_evidence_not_separate_file; using manifest/source contracts only")
    return _base_report(evidence_dir, blockers, warnings, checked)


run_phase11_backup_restore_drill_readiness_report = build_phase11_backup_restore_drill_readiness_report
