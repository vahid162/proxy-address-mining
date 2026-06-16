"""Controlled DB-only Phase 11 customer lifecycle execution evidence."""
from __future__ import annotations

import hashlib
import json
import os
import pwd
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config

TARGET_CUSTOMER_KEY = "limited-btc-001"
TARGET_LANE = "btc"
TARGET_PORT = 20101
BACKUP_ROOT = Path("/var/backups/mpf/phase11-lifecycle-execution")
RECOMMENDED_EXECUTION_USER = "mpf"
READY = "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"
RECORDED = "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_RECORDED"

REQ_TABLES = (
    "customers",
    "customer_policies",
    "customer_ip_pins",
    "events",
    "audit_log",
    "backups",
    "restore_points",
)
REQ_COLUMNS = {
    "customers": ("id", "customer_key", "lane_id", "port", "status", "service_days", "lifecycle_note", "updated_at", "updated_by"),
    "backups": ("id", "backup_type", "path", "checksum", "status", "created_by", "verified_at", "metadata_json"),
    "restore_points": ("id", "restore_type", "subject_type", "subject_id", "backup_id", "metadata_json", "created_by", "reason", "checksum"),
    "events": ("id", "event_type", "severity", "subject_type", "subject_id", "message", "data_json", "created_by", "correlation_id"),
    "audit_log": ("id", "actor_type", "actor_id", "action", "resource_type", "resource_id", "before_json", "after_json", "reason", "correlation_id"),
}


def _canon(o: Any) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), default=str)


def _sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _base_flags() -> dict[str, Any]:
    return {
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
    }


def _blocked(component: str, blockers: list[str], **extra: Any) -> dict[str, Any]:
    return {
        "component": component,
        "repository_version": __version__,
        "blockers": sorted(set(blockers)),
        "final_decision": "BLOCKED",
        **_base_flags(),
        **extra,
    }


def _load_json_checked(path: Path, *, component: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, ["evidence_file_missing" if "verify" in component else "package_file_missing"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"json_invalid:{exc.msg}"]
    except Exception as exc:
        return None, [f"json_read_failed:{exc}"]
    if not isinstance(data, dict):
        return None, ["json_root_not_object"]
    return data, []


def _load_json(p: Path) -> dict[str, Any]:
    data, blockers = _load_json_checked(p, component="generic_json")
    if blockers:
        raise ValueError(",".join(blockers))
    assert data is not None
    return data


def _hash_pkg(pkg: dict[str, Any]) -> str:
    body = dict(pkg)
    body.pop("package_sha256", None)
    return _sha_text(_canon(body))


def _gate_contract() -> dict[str, Any]:
    return {
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
    }


def _connect(config_path: Path):
    import psycopg

    return psycopg.connect(load_config(config_path).database.url, connect_timeout=5)


def _dict(cur, sql: str, params: tuple = ()) -> dict[str, Any] | None:
    cur.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d.name if hasattr(d, "name") else d[0] for d in cur.description]
    return dict(zip(cols, row, strict=False))


def _list(cur, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    rows = cur.fetchall()
    cols = [d.name if hasattr(d, "name") else d[0] for d in cur.description]
    return [dict(zip(cols, r, strict=False)) for r in rows]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _customer_state(cur) -> dict[str, Any] | None:
    return _dict(
        cur,
        """
        select c.id,c.customer_key,lower(l.name) as lane,c.port,c.status,c.service_days,
               c.lifecycle_note,c.starts_at,c.expires_at,c.activated_at,c.updated_at
        from customers c
        join lanes l on l.id=c.lane_id
        where c.customer_key=%s
        """,
        (TARGET_CUSTOMER_KEY,),
    )


def _validate_target(st: dict[str, Any] | None) -> list[str]:
    b = []
    if not st:
        return ["target_customer_missing"]
    if st.get("customer_key") != TARGET_CUSTOMER_KEY:
        b.append("customer_key_mismatch")
    if str(st.get("lane")).lower() != TARGET_LANE:
        b.append("lane_mismatch")
    if int(st.get("port") or 0) != TARGET_PORT:
        b.append("port_mismatch")
    if st.get("status") != "active":
        b.append("target_customer_not_active")
    return b


def _operator_context(backup_root: Path = BACKUP_ROOT) -> dict[str, Any]:
    uid = os.geteuid()
    gid = os.getegid()
    try:
        user = pwd.getpwuid(uid).pw_name
    except KeyError:
        user = str(uid)
    try:
        recommended = pwd.getpwnam(RECOMMENDED_EXECUTION_USER)
        recommended_user_exists = True
        recommended_uid = recommended.pw_uid
        recommended_gid = recommended.pw_gid
    except KeyError:
        recommended_user_exists = False
        recommended_uid = None
        recommended_gid = None
    return {
        "effective_user": user,
        "effective_uid": uid,
        "effective_gid": gid,
        "recommended_execution_user": RECOMMENDED_EXECUTION_USER,
        "recommended_user_exists": recommended_user_exists,
        "recommended_uid": recommended_uid,
        "recommended_gid": recommended_gid,
        "recommended_command_prefix": f"sudo -u {RECOMMENDED_EXECUTION_USER} /usr/local/bin/mpf",
        "running_as_recommended_user": user == RECOMMENDED_EXECUTION_USER,
        "backup_root": str(backup_root),
    }


def _backup_root_status(backup_root: Path = BACKUP_ROOT) -> dict[str, Any]:
    parent = backup_root.parent
    exists = backup_root.exists()
    path_to_check = backup_root if exists else parent
    parent_exists = parent.exists()
    return {
        "backup_root": str(backup_root),
        "parent": str(parent),
        "exists": exists,
        "parent_exists": parent_exists,
        "effective_user_can_create_or_write": parent_exists and os.access(path_to_check, os.W_OK | os.X_OK),
        "mode": oct(backup_root.stat().st_mode & 0o777) if exists else None,
        "parent_mode": oct(parent.stat().st_mode & 0o777) if parent_exists else None,
        "status": "ready" if parent_exists and os.access(path_to_check, os.W_OK | os.X_OK) else "blocked",
    }


def _validate_required_columns(cur) -> list[str]:
    blockers: list[str] = []
    for table, columns in REQ_COLUMNS.items():
        cur.execute(
            """
            select column_name from information_schema.columns
            where table_schema='public' and table_name=%s
            """,
            (table,),
        )
        present = {r[0] for r in cur.fetchall()}
        for column in columns:
            if column not in present:
                blockers.append(f"missing_column:{table}.{column}")
    return blockers


def _write_json_optional(path: Path | None, payload: dict[str, Any]) -> list[str]:
    if path is None:
        return []
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    except Exception as exc:
        return [f"out_json_write_failed:{exc}"]
    return []


def build_package(config_path: Path = DEFAULT_CONFIG_PATH, *, out_json: Path | None = None, backup_root: Path = BACKUP_ROOT) -> dict[str, Any]:
    blockers: list[str] = []
    st = None
    operator_context = _operator_context(backup_root)
    try:
        with _connect(config_path) as conn, conn.cursor() as cur:
            st = _customer_state(cur)
            blockers += _validate_target(st)
    except Exception as exc:
        blockers.append(f"db_read_failed:{exc}")
    pkg = {
        "component": "phase11_production_customer_lifecycle_execution_package",
        "repository_version": __version__,
        "package_id": f"phase11-lifecycle-{uuid.uuid4()}",
        "target": {"customer_key": TARGET_CUSTOMER_KEY, "lane": TARGET_LANE, "port": TARGET_PORT},
        "target_summary": f"{TARGET_CUSTOMER_KEY}/{TARGET_LANE}/{TARGET_PORT}",
        "expected_before_state": st,
        "expected_before_state_present": st is not None,
        "intended_lifecycle_operation": {
            "operation": "controlled_renew_evidence_metadata_update",
            "service_days_from_before_state": (st or {}).get("service_days"),
            "lifecycle_note": f"Phase 11 controlled lifecycle execution evidence {__version__}; DB-only reversible metadata update",
        },
        "required_confirmation_flags": [
            "operator_confirmed",
            "i_understand_db_only",
            "i_understand_no_firewall_apply",
            "i_understand_no_runtime_change",
            "i_understand_phase11_not_completed",
        ],
        "operator_context": operator_context,
        "execution_allowed": False,
        "recommended_next_command": f"{operator_context['recommended_command_prefix']} production production-customer-lifecycle-execution-preflight --package-json <package.json> --output json",
        "safety_contract": _gate_contract() | {
            "firewall_apply_performed": False,
            "conntrack_flush_performed": False,
            "docker_restart_performed": False,
            "systemd_restart_performed": False,
        },
        "blockers": blockers,
        "warnings": [] if operator_context["running_as_recommended_user"] else ["not_running_as_recommended_execution_user"],
        **_base_flags(),
        "final_decision": "PACKAGE_READY" if not blockers else "BLOCKED",
    }
    pkg["package_sha256"] = _hash_pkg(pkg)
    write_warnings = _write_json_optional(out_json, pkg)
    if write_warnings:
        pkg["warnings"].extend(write_warnings)
    return pkg


def preflight(
    package_file: Path,
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    backup_root: Path = BACKUP_ROOT,
    out_json_path: Path | None = None,
) -> dict[str, Any]:
    component = "phase11_production_customer_lifecycle_execution_preflight"
    pkg, blockers = _load_json_checked(package_file, component=component)
    operator_context = _operator_context(backup_root)
    backup_status = _backup_root_status(backup_root)
    warnings: list[str] = []
    st = None
    if pkg is None:
        return _blocked(component, blockers, operator_context=operator_context, backup_root_status=backup_status)
    if pkg.get("final_decision") != "PACKAGE_READY":
        blockers.append("package_not_ready")
    if pkg.get("blockers"):
        blockers.append("package_has_blockers")
    if pkg.get("package_sha256") != _hash_pkg(pkg):
        blockers.append("package_hash_mismatch")
    if pkg.get("target") != {"customer_key": TARGET_CUSTOMER_KEY, "lane": TARGET_LANE, "port": TARGET_PORT}:
        blockers.append("package_scope_mismatch")
    exp = pkg.get("expected_before_state")
    if not isinstance(exp, dict) or not exp:
        blockers.append("expected_before_state_missing")
        exp = {}
    if not operator_context["recommended_user_exists"]:
        blockers.append("recommended_execution_user_missing")
    if not operator_context["running_as_recommended_user"]:
        blockers.append("operator_context_not_recommended_user")
        warnings.append(f"run_as_{RECOMMENDED_EXECUTION_USER}_required_for_execute")
    if backup_status["status"] != "ready":
        blockers.append("backup_root_not_writable_for_effective_user")
    if out_json_path is not None and not out_json_path.parent.exists():
        blockers.append("out_json_parent_missing")
    elif out_json_path is not None and not os.access(out_json_path.parent, os.W_OK | os.X_OK):
        blockers.append("out_json_parent_not_writable")
    try:
        with _connect(config_path) as conn, conn.cursor() as cur:
            for table in REQ_TABLES:
                cur.execute("select to_regclass(%s)", (table,))
                if cur.fetchone()[0] is None:
                    blockers.append(f"missing_table:{table}")
            blockers += _validate_required_columns(cur)
            st = _customer_state(cur)
            blockers += _validate_target(st)
            for key in ("customer_key", "lane", "port", "status", "service_days", "lifecycle_note"):
                if str((st or {}).get(key)) != str(exp.get(key)):
                    blockers.append(f"target_state_drift:{key}")
    except Exception as exc:
        blockers.append(f"db_read_failed:{exc}")
    return {
        "component": component,
        "repository_version": __version__,
        "package_id": pkg.get("package_id"),
        "package_sha256": pkg.get("package_sha256"),
        "target": pkg.get("target"),
        "expected_before_state_present": bool(exp),
        "current_target_state_present": st is not None,
        "operator_context": operator_context,
        "backup_root_status": backup_status,
        "recommended_command_prefix": operator_context["recommended_command_prefix"],
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        **_base_flags(),
        "final_decision": "PREFLIGHT_READY" if not blockers else "BLOCKED",
    }


def doctor(config_path: Path = DEFAULT_CONFIG_PATH, *, backup_root: Path = BACKUP_ROOT, package_file: Path | None = None) -> dict[str, Any]:
    component = "phase11_production_customer_lifecycle_execution_doctor"
    blockers: list[str] = []
    operator_context = _operator_context(backup_root)
    backup_status = _backup_root_status(backup_root)
    db_ok = False
    target_state = None
    try:
        with _connect(config_path) as conn, conn.cursor() as cur:
            db_ok = True
            target_state = _customer_state(cur)
            blockers += _validate_target(target_state)
            for table in REQ_TABLES:
                cur.execute("select to_regclass(%s)", (table,))
                if cur.fetchone()[0] is None:
                    blockers.append(f"missing_table:{table}")
            blockers += _validate_required_columns(cur)
    except Exception as exc:
        blockers.append(f"db_read_failed:{exc}")
    preflight_report = preflight(package_file, config_path, backup_root=backup_root) if package_file else None
    return {
        "component": component,
        "repository_version": __version__,
        "db_connectivity": "ok" if db_ok else "blocked",
        "target": {"customer_key": TARGET_CUSTOMER_KEY, "lane": TARGET_LANE, "port": TARGET_PORT},
        "target_state_present": target_state is not None,
        "operator_context": operator_context,
        "backup_root_status": backup_status,
        "package_preflight": preflight_report,
        "blockers": sorted(set(blockers)),
        **_base_flags(),
        "final_decision": "DOCTOR_READY" if not blockers and backup_status["status"] == "ready" else "BLOCKED",
    }


def execute(
    package_file: Path,
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    operator: str,
    reason: str,
    backup_root: Path = BACKUP_ROOT,
    operator_confirmed: bool = False,
    i_understand_db_only: bool = False,
    i_understand_no_firewall_apply: bool = False,
    i_understand_no_runtime_change: bool = False,
    i_understand_phase11_not_completed: bool = False,
    out_json: Path | None = None,
) -> dict[str, Any]:
    component = "phase11_production_customer_lifecycle_execution_execute"
    operator_context = _operator_context(backup_root)
    if not all([operator_confirmed, i_understand_db_only, i_understand_no_firewall_apply, i_understand_no_runtime_change, i_understand_phase11_not_completed]):
        return {
            "component": component,
            "repository_version": __version__,
            "final_decision": "BLOCKED_CONFIRMATION_REQUIRED",
            "blockers": ["confirmation_flags_required"],
            "operator_context": operator_context,
            **_base_flags(),
        }
    pf = preflight(package_file, config_path, backup_root=backup_root, out_json_path=out_json)
    if pf["blockers"]:
        return pf | {"component": component, "final_decision": "BLOCKED_PREFLIGHT"}
    pkg, load_blockers = _load_json_checked(package_file, component=component)
    if pkg is None:
        return _blocked(component, load_blockers, operator_context=operator_context)
    corr = str(uuid.uuid4())
    artifact_created = False
    artifact_path: Path | None = None
    artifact_sha: str | None = None
    try:
        backup_root.mkdir(parents=True, exist_ok=True)
        with _connect(config_path) as conn:
            with conn.transaction(), conn.cursor() as cur:
                st = _customer_state(cur)
                target_blockers = _validate_target(st)
                if target_blockers:
                    return _blocked(component, target_blockers, operator_context=operator_context)
                assert st is not None
                pol = _list(cur, "select * from customer_policies where customer_id=%s and is_current=true", (st["id"],))
                pins = _list(cur, "select * from customer_ip_pins where customer_id=%s", (st["id"],))
                artifact = {
                    "artifact_type": "phase11_lifecycle_execution_restore",
                    "customer_before_state": st,
                    "current_customer_policy_before_state": pol,
                    "ip_pins_before_state": pins,
                    "operation_metadata": {
                        "operator": operator,
                        "reason": reason,
                        "created_at": datetime.now(UTC).isoformat(),
                        "package_id": pkg["package_id"],
                        "package_sha256": pkg["package_sha256"],
                        "correlation_id": corr,
                    },
                }
                artifact_path = backup_root / f"{corr}.json"
                artifact_path.write_text(json.dumps(artifact, indent=2, default=str) + "\n", encoding="utf-8")
                artifact_created = True
                artifact_sha = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                metadata = _canon({"package_id": pkg["package_id"], "correlation_id": corr})
                cur.execute(
                    "insert into backups (backup_type,path,checksum,status,created_by,verified_at,metadata_json) values (%s,%s,%s,%s,%s,now(),%s::jsonb) returning id",
                    ("phase11_lifecycle_execution", str(artifact_path), artifact_sha, "prepared", operator, metadata),
                )
                bid = cur.fetchone()[0]
                cur.execute(
                    "insert into restore_points (restore_type,subject_type,subject_id,backup_id,metadata_json,created_by,reason,checksum) values (%s,%s,%s,%s,%s::jsonb,%s,%s,%s) returning id",
                    ("customer_lifecycle", "customer", st["id"], bid, metadata, operator, reason, artifact_sha),
                )
                rpid = cur.fetchone()[0]
                new_note = f"Phase 11 controlled lifecycle execution evidence {__version__}; previous_note={st.get('lifecycle_note') or ''}"[:1000]
                cur.execute("update customers set lifecycle_note=%s, service_days=service_days, updated_at=now(), updated_by=%s where id=%s", (new_note, operator, st["id"]))
                cur.execute(
                    "insert into events (event_type,severity,subject_type,subject_id,message,data_json,created_by,correlation_id) values (%s,'info','customer',%s,%s,%s::jsonb,%s,%s) returning id",
                    ("phase11.production_customer_lifecycle_execution", st["id"], "Phase 11 controlled DB-only lifecycle execution evidence", _canon({"backup_id": bid, "restore_point_id": rpid, "package_id": pkg["package_id"], "correlation_id": corr}), operator, corr),
                )
                eid = cur.fetchone()[0]
                cur.execute(
                    "insert into audit_log (actor_type,actor_id,action,resource_type,resource_id,before_json,after_json,reason,correlation_id) values ('operator',%s,%s,'customer',%s,%s::jsonb,%s::jsonb,%s,%s) returning id",
                    (operator, "phase11.production_customer_lifecycle_execution", st["id"], _canon(st), _canon({"lifecycle_note": new_note, "package_id": pkg["package_id"], "correlation_id": corr}), reason, corr),
                )
                aid = cur.fetchone()[0]
        out = {
            "component": component,
            "repository_version": __version__,
            "final_decision": RECORDED,
            "package_id": pkg["package_id"],
            "package_sha256": pkg["package_sha256"],
            "correlation_id": corr,
            "customer_id": st["id"],
            "backup_id": bid,
            "backup_path": str(artifact_path),
            "backup_sha256": artifact_sha,
            "restore_point_id": rpid,
            "event_id": eid,
            "audit_id": aid,
            "operator_context": operator_context,
            **_base_flags(),
            "mutation_performed": True,
            "db_mutation_performed": True,
        }
    except Exception as exc:
        out = {
            "component": component,
            "repository_version": __version__,
            "final_decision": "BLOCKED_EXECUTE_EXCEPTION",
            "blockers": [f"execute_failed:{exc}"],
            "operator_context": operator_context,
            "orphan_backup_artifact_created": artifact_created,
            "orphan_backup_artifact_path": str(artifact_path) if artifact_path else None,
            "orphan_backup_artifact_sha256": artifact_sha,
            **_base_flags(),
        }
    write_warnings = _write_json_optional(out_json, out)
    if write_warnings:
        out["warnings"] = sorted(set([*(out.get("warnings") or []), *write_warnings]))
    return out


def verify(evidence_file: Path, config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    component = "phase11_production_customer_lifecycle_execution_verify"
    ev, blockers = _load_json_checked(evidence_file, component=component)
    if ev is None:
        return _blocked(component, blockers)
    p = Path(ev.get("backup_path", ""))
    if not p.exists():
        blockers.append("backup_artifact_missing")
    elif hashlib.sha256(p.read_bytes()).hexdigest() != ev.get("backup_sha256"):
        blockers.append("backup_checksum_mismatch")
    for flag in ("firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed", "phase12_start_allowed"):
        if ev.get(flag) is not False:
            blockers.append(f"forbidden_flag:{flag}")
    try:
        with _connect(config_path) as conn, conn.cursor() as cur:
            backup = _dict(cur, "select id,metadata_json from backups where id=%s", (ev.get("backup_id"),))
            restore = _dict(cur, "select id,backup_id,subject_id,metadata_json from restore_points where id=%s", (ev.get("restore_point_id"),))
            event = _dict(cur, "select id,event_type,subject_id,data_json,correlation_id from events where id=%s", (ev.get("event_id"),))
            audit = _dict(cur, "select id,action,resource_id,after_json,correlation_id from audit_log where id=%s", (ev.get("audit_id"),))
            rows = {"backups": backup, "restore_points": restore, "events": event, "audit_log": audit}
            for table, row in rows.items():
                if row is None:
                    blockers.append(f"missing_{table}_row")
            st = _customer_state(cur)
            blockers += _validate_target(st)
            package_id = ev.get("package_id")
            correlation_id = ev.get("correlation_id")
            if backup:
                meta = _as_dict(backup.get("metadata_json"))
                if meta.get("package_id") != package_id or meta.get("correlation_id") != correlation_id:
                    blockers.append("backup_metadata_correlation_mismatch")
            if restore:
                meta = _as_dict(restore.get("metadata_json"))
                if meta.get("package_id") != package_id or meta.get("correlation_id") != correlation_id:
                    blockers.append("restore_point_metadata_correlation_mismatch")
                if int(restore.get("backup_id") or -1) != int(ev.get("backup_id") or -2):
                    blockers.append("restore_point_backup_link_mismatch")
                if int(restore.get("subject_id") or -1) != int(ev.get("customer_id") or -2):
                    blockers.append("restore_point_subject_mismatch")
            if event:
                if event.get("event_type") != "phase11.production_customer_lifecycle_execution":
                    blockers.append("event_type_mismatch")
                if event.get("correlation_id") != correlation_id:
                    blockers.append("event_correlation_mismatch")
                data = _as_dict(event.get("data_json"))
                if data.get("package_id") != package_id or data.get("correlation_id") != correlation_id:
                    blockers.append("event_data_correlation_mismatch")
            if audit:
                if audit.get("action") != "phase11.production_customer_lifecycle_execution":
                    blockers.append("audit_action_mismatch")
                if audit.get("correlation_id") != correlation_id:
                    blockers.append("audit_correlation_mismatch")
                after = _as_dict(audit.get("after_json"))
                if after.get("package_id") != package_id or after.get("correlation_id") != correlation_id:
                    blockers.append("audit_after_correlation_mismatch")
    except Exception as exc:
        blockers.append(f"db_read_failed:{exc}")
    return {
        "component": component,
        "repository_version": __version__,
        "package_id": ev.get("package_id"),
        "package_sha256": ev.get("package_sha256"),
        "correlation_id": ev.get("correlation_id"),
        "blockers": sorted(set(blockers)),
        **_base_flags(),
        "final_decision": READY if not blockers else "BLOCKED",
    }
