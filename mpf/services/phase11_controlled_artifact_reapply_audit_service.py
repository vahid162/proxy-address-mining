from __future__ import annotations

import hashlib
import json
from typing import Any

from mpf.config import MPFConfig

_SUCCESS_DECISION = "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"
_STATUS_BY_DECISION = {
    "FAILED_PRE_APPLY": "failed_pre_apply",
    "FAILED_APPLY": "failed_apply",
    "FAILED_POST_APPLY_VERIFICATION": "failed_verify",
    _SUCCESS_DECISION: "verified",
}


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class ControlledArtifactReapplyAuditRepo:
    """Schema-faithful PostgreSQL operational metadata repository.

    It only writes operational metadata tables and uses the real Phase 2 schema
    column names from ``mpf.models``. Domain state tables are never mutated here.
    """

    production_ready = True

    def __init__(self, config: MPFConfig) -> None:
        self.config = config

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(f"psycopg_unavailable:{exc}") from exc
        return psycopg.connect(self.config.database.url, connect_timeout=5)

    def record_intent(self, package: dict[str, object], operator: str, reason: str, *, backup_result: dict[str, object], pre_iptables_save: str) -> dict[str, object]:
        correlation_id = str(package.get("package_id"))[:64]
        backup_dir = str(backup_result.get("backup_dir") or "")
        manifest_hash = _sha(_json(backup_result.get("manifest", {})))
        metadata = {
            "package_id": package.get("package_id"),
            "package_sha256": package.get("package_sha256"),
            "payload_sha256": package.get("payload_sha256"),
            "backup_dir": backup_dir,
            "backup_manifest_sha256": manifest_hash,
            "rollback_plan": package.get("rollback_plan"),
        }
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into firewall_snapshots (backend, iptables_save_text, checksum, created_by, reason)
                    values (%s, %s, %s, %s, %s)
                    returning id
                    """,
                    ("iptables", pre_iptables_save, _sha(pre_iptables_save), operator, reason),
                )
                snapshot_before_id = cur.fetchone()[0]
                backup_metadata = {
                    "package_id": package.get("package_id"),
                    "backup_manifest_sha256": manifest_hash,
                    "canonical_package_sha256": package.get("package_sha256"),
                    "payload_sha256": package.get("payload_sha256"),
                    "backup_dir": backup_dir,
                }
                cur.execute(
                    """
                    insert into backups (backup_type, path, checksum, status, created_by, verified_at, error_message, metadata_json)
                    values (%s, %s, %s, %s, %s, now(), %s, %s::jsonb)
                    returning id
                    """,
                    ("firewall", backup_dir, manifest_hash, "prepared", operator, None, _json(backup_metadata)),
                )
                backup_id = cur.fetchone()[0]
                cur.execute(
                    """
                    insert into restore_points (restore_type, subject_type, subject_id, snapshot_id, backup_id, metadata_json, created_by, reason, checksum)
                    values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                    returning id
                    """,
                    ("firewall", "phase11_controlled_artifact_reapply", None, snapshot_before_id, backup_id, _json(metadata), operator, reason, str(package.get("package_sha256"))),
                )
                restore_point_id = cur.fetchone()[0]
                plan_json = {"full_decision": "prepared", "package": metadata, "plan": package.get("plan", {})}
                cur.execute(
                    """
                    insert into firewall_applies (action, status, apply_mode, backend, restore_point_id, snapshot_before_id, snapshot_after_id, plan_json, summary, started_at, created_by, error_message, correlation_id)
                    values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, now(), %s, %s, %s)
                    returning id
                    """,
                    ("phase11_reapply", "prepared", "controlled", "iptables", restore_point_id, snapshot_before_id, None, _json(plan_json), "Phase 11 controlled artifact reapply prepared", operator, None, correlation_id),
                )
                firewall_apply_id = cur.fetchone()[0]
                event_data = {**metadata, "firewall_apply_id": firewall_apply_id, "restore_point_id": restore_point_id, "backup_id": backup_id}
                cur.execute(
                    """
                    insert into events (event_type, severity, subject_type, subject_id, message, data_json, created_by, correlation_id)
                    values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                    """,
                    ("firewall_apply_prepared", "info", "firewall_apply", firewall_apply_id, "Phase 11 controlled artifact reapply prepared", _json(event_data), operator, correlation_id),
                )
                cur.execute(
                    """
                    insert into audit_log (actor_type, actor_id, action, resource_type, resource_id, before_json, after_json, reason, correlation_id)
                    values (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                    """,
                    ("operator", operator, "phase11_controlled_artifact_reapply_prepared", "firewall_apply", firewall_apply_id, None, _json(event_data), reason, correlation_id),
                )
        return {"snapshot_before_id": snapshot_before_id, "backup_id": backup_id, "restore_point_id": restore_point_id, "firewall_apply_id": firewall_apply_id, "correlation_id": correlation_id, "backup_dir": backup_dir, "backup_manifest_sha256": manifest_hash}

    def record_result(
        self,
        package: dict[str, object],
        decision: str,
        *,
        backup_result: dict[str, object] | None = None,
        post_iptables_save: str = "",
        error_details: dict[str, object] | None = None,
        partial_apply_possible: bool = False,
        rollback_required: bool = False,
    ) -> dict[str, object]:
        correlation_id = str(package.get("package_id"))[:64]
        short_status = _STATUS_BY_DECISION.get(decision, "audit_failed")
        summary = f"Phase 11 controlled artifact reapply result: {decision}"
        data = {
            "package_id": package.get("package_id"),
            "full_decision": decision,
            "short_status": short_status,
            "backup_dir": (backup_result or {}).get("backup_dir"),
            "partial_apply_possible": partial_apply_possible,
            "rollback_required": rollback_required,
            "error_details": error_details or {},
        }
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into firewall_snapshots (backend, iptables_save_text, checksum, created_by, reason)
                    values (%s, %s, %s, %s, %s)
                    returning id
                    """,
                    ("iptables", post_iptables_save, _sha(post_iptables_save), "mpf", summary),
                )
                snapshot_after_id = cur.fetchone()[0]
                cur.execute(
                    """
                    update firewall_applies
                    set status=%s, snapshot_after_id=%s, plan_json=%s::jsonb, summary=%s, finished_at=now(), error_message=%s
                    where correlation_id=%s
                    returning id
                    """,
                    (short_status, snapshot_after_id, _json(data), summary, _json(error_details or {}) if error_details else None, correlation_id),
                )
                row = cur.fetchone()
                firewall_apply_id = row[0] if row else None
                cur.execute(
                    """
                    insert into events (event_type, severity, subject_type, subject_id, message, data_json, created_by, correlation_id)
                    values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                    """,
                    ("firewall_apply_result", "error" if rollback_required else "info", "firewall_apply", firewall_apply_id, summary, _json(data), "mpf", correlation_id),
                )
                cur.execute(
                    """
                    insert into audit_log (actor_type, actor_id, action, resource_type, resource_id, before_json, after_json, reason, correlation_id)
                    values (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                    """,
                    ("system", "mpf", "phase11_controlled_artifact_reapply_result", "firewall_apply", firewall_apply_id, None, _json(data), summary, correlation_id),
                )
        return {"snapshot_after_id": snapshot_after_id, "firewall_apply_id": firewall_apply_id, "correlation_id": correlation_id, "short_status": short_status}
