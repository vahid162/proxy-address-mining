from __future__ import annotations

import hashlib
import json
import os
import subprocess
from urllib.parse import urlparse
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

    def _database_url(self) -> str:
        return str(self.config.database.url)

    def _local_peer_root_strategy_available(self) -> bool:
        return self._uses_local_peer_root_psql()

    def _uses_local_peer_root_psql(self) -> bool:
        url = self._database_url()
        parsed = urlparse(url)
        return os.geteuid() == 0 and parsed.scheme in {"postgresql", "postgres"} and not parsed.netloc and bool(parsed.path and parsed.path != "/")

    def _psql_dbname(self) -> str:
        parsed = urlparse(self._database_url())
        if not parsed.path or parsed.path == "/":
            raise RuntimeError("local_peer_database_name_missing")
        return parsed.path.lstrip("/")

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(f"psycopg_unavailable:{exc}") from exc
        return psycopg.connect(self._database_url(), connect_timeout=5)

    @staticmethod
    def _sql_literal(value: object) -> str:
        if value is None:
            return "NULL"
        return "'" + str(value).replace("'", "''") + "'"

    def _psql_json(self, sql: str) -> dict[str, object]:
        completed = subprocess.run(
            ["sudo", "-u", "mpf", "psql", "-X", "-v", "ON_ERROR_STOP=1", "-d", self._psql_dbname(), "-t", "-A"],
            input=sql, text=True, capture_output=True, check=False, shell=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"psql_operational_metadata_write_failed:{completed.stderr.strip() or completed.stdout.strip()}")
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if not lines:
            return {}
        return json.loads(lines[-1])

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
        backup_metadata = {
            "package_id": package.get("package_id"),
            "backup_manifest_sha256": manifest_hash,
            "canonical_package_sha256": package.get("package_sha256"),
            "payload_sha256": package.get("payload_sha256"),
            "backup_dir": backup_dir,
        }
        plan_json = {"full_decision": "prepared", "package": metadata, "plan": package.get("plan", {})}
        if self._uses_local_peer_root_psql():
            q = self._sql_literal
            sql = f"""
            begin;
            with snapshot_before as (
              insert into firewall_snapshots (backend, iptables_save_text, checksum, created_by, reason)
              values ('iptables', {q(pre_iptables_save)}, {q(_sha(pre_iptables_save))}, {q(operator)}, {q(reason)}) returning id
            ), backup_row as (
              insert into backups (backup_type, path, checksum, status, created_by, verified_at, error_message, metadata_json)
              values ('firewall', {q(backup_dir)}, {q(manifest_hash)}, 'prepared', {q(operator)}, now(), NULL, {q(_json(backup_metadata))}::jsonb) returning id
            ), restore_row as (
              insert into restore_points (restore_type, subject_type, subject_id, snapshot_id, backup_id, metadata_json, created_by, reason, checksum)
              select 'firewall', 'phase11_controlled_artifact_reapply', NULL, snapshot_before.id, backup_row.id, {q(_json(metadata))}::jsonb, {q(operator)}, {q(reason)}, {q(str(package.get('package_sha256')))} from snapshot_before, backup_row returning id, snapshot_id, backup_id
            ), apply_row as (
              insert into firewall_applies (action, status, apply_mode, backend, restore_point_id, snapshot_before_id, snapshot_after_id, plan_json, summary, started_at, created_by, error_message, correlation_id)
              select 'phase11_reapply', 'prepared', 'controlled', 'iptables', restore_row.id, restore_row.snapshot_id, NULL, {q(_json(plan_json))}::jsonb, 'Phase 11 controlled artifact reapply prepared', now(), {q(operator)}, NULL, {q(correlation_id)} from restore_row returning id, restore_point_id, snapshot_before_id
            ), event_row as (
              insert into events (event_type, severity, subject_type, subject_id, message, data_json, created_by, correlation_id)
              select 'firewall_apply_prepared', 'info', 'firewall_apply', apply_row.id, 'Phase 11 controlled artifact reapply prepared', jsonb_set(jsonb_set(jsonb_set({q(_json(metadata))}::jsonb, '{{firewall_apply_id}}', to_jsonb(apply_row.id)), '{{restore_point_id}}', to_jsonb(apply_row.restore_point_id)), '{{backup_id}}', to_jsonb((select backup_id from restore_row))), {q(operator)}, {q(correlation_id)} from apply_row
            ), audit_row as (
              insert into audit_log (actor_type, actor_id, action, resource_type, resource_id, before_json, after_json, reason, correlation_id)
              select 'operator', {q(operator)}, 'phase11_controlled_artifact_reapply_prepared', 'firewall_apply', apply_row.id, NULL, jsonb_set(jsonb_set(jsonb_set({q(_json(metadata))}::jsonb, '{{firewall_apply_id}}', to_jsonb(apply_row.id)), '{{restore_point_id}}', to_jsonb(apply_row.restore_point_id)), '{{backup_id}}', to_jsonb((select backup_id from restore_row))), {q(reason)}, {q(correlation_id)} from apply_row
            )
            select json_build_object('snapshot_before_id', snapshot_before_id, 'backup_id', (select backup_id from restore_row), 'restore_point_id', restore_point_id, 'firewall_apply_id', id, 'correlation_id', {q(correlation_id)}, 'backup_dir', {q(backup_dir)}, 'backup_manifest_sha256', {q(manifest_hash)}) from apply_row;
            commit;
            """
            return self._psql_json(sql)

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
        if self._uses_local_peer_root_psql():
            q = self._sql_literal
            sql = f"""
            begin;
            with snapshot_after as (
              insert into firewall_snapshots (backend, iptables_save_text, checksum, created_by, reason)
              values ('iptables', {q(post_iptables_save)}, {q(_sha(post_iptables_save))}, 'mpf', {q(summary)}) returning id
            ), apply_update as (
              update firewall_applies set status={q(short_status)}, snapshot_after_id=(select id from snapshot_after), plan_json={q(_json(data))}::jsonb, summary={q(summary)}, finished_at=now(), error_message={q(_json(error_details or {}) if error_details else None)} where correlation_id={q(correlation_id)} returning id
            ), event_row as (
              insert into events (event_type, severity, subject_type, subject_id, message, data_json, created_by, correlation_id)
              select 'firewall_apply_result', {q('error' if rollback_required else 'info')}, 'firewall_apply', apply_update.id, {q(summary)}, {q(_json(data))}::jsonb, 'mpf', {q(correlation_id)} from apply_update
            ), audit_row as (
              insert into audit_log (actor_type, actor_id, action, resource_type, resource_id, before_json, after_json, reason, correlation_id)
              select 'system', 'mpf', 'phase11_controlled_artifact_reapply_result', 'firewall_apply', apply_update.id, NULL, {q(_json(data))}::jsonb, {q(summary)}, {q(correlation_id)} from apply_update
            )
            select json_build_object('snapshot_after_id', (select id from snapshot_after), 'firewall_apply_id', (select id from apply_update), 'correlation_id', {q(correlation_id)}, 'short_status', {q(short_status)});
            commit;
            """
            return self._psql_json(sql)

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
