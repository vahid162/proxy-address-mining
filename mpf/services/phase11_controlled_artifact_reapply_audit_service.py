from __future__ import annotations

import json
from typing import Any

from mpf.config import MPFConfig


class ControlledArtifactReapplyAuditRepo:
    """PostgreSQL operational metadata repository for the controlled reapply path.

    The repository writes only operational evidence rows. It never mutates lanes,
    customers, policies, pins, abuse, block, or pause domain tables.
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

    def record_intent(self, package: dict[str, object], operator: str, reason: str) -> None:
        metadata = {
            "phase11_controlled_artifact_reapply": True,
            "package_id": package.get("package_id"),
            "package_sha256": package.get("package_sha256"),
            "payload_sha256": package.get("payload_sha256"),
            "rollback_plan": package.get("rollback_plan"),
            "operator": operator,
            "reason": reason,
        }
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into firewall_snapshots (source, snapshot_text, snapshot_hash, metadata_json)
                    values (%s, %s, %s, %s::jsonb)
                    returning id
                    """,
                    ("phase11_controlled_artifact_reapply_pre", str((package.get("plan") or {}).get("iptables_save_text", "")), package.get("iptables_save_sha256"), json.dumps(metadata)),
                )
                snapshot_id = cur.fetchone()[0]
                cur.execute(
                    """
                    insert into backups (backup_type, path, checksum, metadata_json, created_by)
                    values (%s, %s, %s, %s::jsonb, %s)
                    returning id
                    """,
                    ("firewall", str((package.get("backup_requirements") or {}).get("base_dir", "")), package.get("package_sha256"), json.dumps(metadata), operator),
                )
                backup_id = cur.fetchone()[0]
                cur.execute(
                    """
                    insert into restore_points (restore_type, subject_type, subject_id, snapshot_id, backup_id, metadata_json, created_by, reason, checksum)
                    values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                    returning id
                    """,
                    ("firewall", "phase11_controlled_artifact_reapply", str(package.get("package_id")), snapshot_id, backup_id, json.dumps(metadata), operator, reason, package.get("package_sha256")),
                )
                restore_point_id = cur.fetchone()[0]
                cur.execute(
                    """
                    insert into firewall_applies (action, status, apply_mode, backend, restore_point_id, snapshot_before_id, plan_json, summary, created_by, correlation_id)
                    values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                    """,
                    ("phase11_controlled_artifact_reapply", "prepared", "controlled", "iptables", restore_point_id, snapshot_id, json.dumps(package.get("plan", {})), "prepared controlled artifact reapply intent", operator, str(package.get("package_id"))),
                )
                cur.execute("insert into events (event_type, subject_type, subject_id, metadata_json) values (%s, %s, %s, %s::jsonb)", ("firewall_apply_prepared", "phase11_controlled_artifact_reapply", str(package.get("package_id")), json.dumps(metadata)))
                cur.execute("insert into audit_log (actor, action, subject_type, subject_id, metadata_json) values (%s, %s, %s, %s, %s::jsonb)", (operator, "phase11_controlled_artifact_reapply_prepared", "firewall", str(package.get("package_id")), json.dumps(metadata)))

    def record_result(self, package: dict[str, object], decision: str) -> None:
        metadata = {"package_id": package.get("package_id"), "decision": decision, "rollback_required": decision not in {"CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"}}
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("insert into events (event_type, subject_type, subject_id, metadata_json) values (%s, %s, %s, %s::jsonb)", ("firewall_apply_result", "phase11_controlled_artifact_reapply", str(package.get("package_id")), json.dumps(metadata)))
                cur.execute("insert into audit_log (actor, action, subject_type, subject_id, metadata_json) values (%s, %s, %s, %s, %s::jsonb)", ("mpf", "phase11_controlled_artifact_reapply_result", "firewall", str(package.get("package_id")), json.dumps(metadata)))
                cur.execute("update firewall_applies set status=%s, summary=%s where correlation_id=%s", (decision, f"controlled artifact reapply result: {decision}", str(package.get("package_id"))))
