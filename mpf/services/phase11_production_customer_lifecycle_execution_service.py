"""Controlled DB-only Phase 11 customer lifecycle execution evidence."""
from __future__ import annotations

import getpass, hashlib, json, os, tempfile, uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.db import query_database_params

TARGET_CUSTOMER_KEY = "limited-btc-001"; TARGET_LANE = "btc"; TARGET_PORT = 20101
RECOMMENDED_EXECUTION_USER = "mpf"
BACKUP_ROOT = Path("/var/backups/mpf/phase11-lifecycle-execution")
READY = "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"
REQ_TABLES = ("customers","customer_policies","customer_ip_pins","events","audit_log","backups","restore_points")
REQ_COLUMNS = {
    "customers": ("id","customer_key","lane_id","port","status","service_days","lifecycle_note","updated_at","updated_by"),
    "lanes": ("id","name"),
    "backups": ("id","backup_type","path","checksum","status","created_by","metadata_json"),
    "restore_points": ("id","restore_type","subject_type","subject_id","backup_id","metadata_json","created_by","reason","checksum"),
    "events": ("id","event_type","subject_id","data_json","correlation_id"),
    "audit_log": ("id","action","resource_id","after_json","correlation_id"),
}


def _canon(o: Any) -> str: return json.dumps(o, sort_keys=True, separators=(",", ":"), default=str)
def _sha_text(s: str) -> str: return hashlib.sha256(s.encode()).hexdigest()
def _hash_pkg(pkg: dict[str, Any]) -> str:
    body = dict(pkg); body.pop("package_sha256", None); return _sha_text(_canon(body))
def _load_json(p: Path) -> dict[str, Any]: return json.loads(p.read_text(encoding="utf-8"))
def _controlled_base(**extra: Any) -> dict[str, Any]:
    return {"repository_version": __version__, "mutation_performed": False, "db_mutation_performed": False, "firewall_apply_performed": False, "conntrack_flush_performed": False, "docker_restart_performed": False, "systemd_restart_performed": False, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no", "production_traffic": "controlled_cli_limited", "customer_onboarding_allowed": "controlled_cli_limited", **extra}
def _gate_contract() -> dict[str, Any]:
    return {"production_traffic":"controlled_cli_limited","customer_onboarding_allowed":"controlled_cli_limited","phase12_start_allowed":False,"worker_enforcement_allowed":"no","ui_allowed":"no","telegram_allowed":"no"}
def _operator_context(backup_root: Path = BACKUP_ROOT) -> dict[str, Any]:
    return {"recommended_execution_user": RECOMMENDED_EXECUTION_USER, "effective_user": getpass.getuser(), "effective_uid": os.geteuid(), "command_prefix": "sudo -u mpf /usr/local/bin/mpf", "backup_root": str(backup_root)}
def _connect(config_path: Path):
    import psycopg
    return psycopg.connect(load_config(config_path).database.url, connect_timeout=5)
def _dict(cur, sql: str, params: tuple = ()) -> dict[str, Any] | None:
    cur.execute(sql, params); row = cur.fetchone()
    if row is None: return None
    cols = [d.name if hasattr(d,"name") else d[0] for d in cur.description]
    return dict(zip(cols, row, strict=False))
def _list(cur, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params); rows = cur.fetchall(); cols = [d.name if hasattr(d,"name") else d[0] for d in cur.description]
    return [dict(zip(cols, r, strict=False)) for r in rows]
def _customer_state(cur) -> dict[str, Any] | None:
    return _dict(cur, """select c.id,c.customer_key,lower(l.name) as lane,c.port,c.status,c.service_days,c.lifecycle_note,c.starts_at,c.expires_at,c.activated_at,c.updated_at from customers c join lanes l on l.id=c.lane_id where c.customer_key=%s""", (TARGET_CUSTOMER_KEY,))
def _validate_target(st: dict[str, Any] | None) -> list[str]:
    if not st: return ["target_customer_missing"]
    b=[]
    if st.get("customer_key") != TARGET_CUSTOMER_KEY: b.append("customer_key_mismatch")
    if str(st.get("lane")).lower() != TARGET_LANE: b.append("lane_mismatch")
    if int(st.get("port") or 0) != TARGET_PORT: b.append("port_mismatch")
    if st.get("status") != "active": b.append("target_customer_not_active")
    return b
def _is_writable(path: Path) -> bool:
    """Probe writability without creating the persistent backup root during preflight."""
    try:
        if path.exists():
            with tempfile.NamedTemporaryFile(dir=path, prefix=".mpf-preflight-", delete=True): pass
            return True
        parent = path.parent
        if not parent.exists():
            return False
        with tempfile.TemporaryDirectory(dir=parent, prefix=".mpf-preflight-parent-"):
            pass
        return True
    except Exception:
        return False

def build_package(config_path: Path = DEFAULT_CONFIG_PATH, *, out_json: Path | None = None, backup_root: Path = BACKUP_ROOT) -> dict[str, Any]:
    blockers=[]; st=None
    try:
        with _connect(config_path) as conn, conn.cursor() as cur: st=_customer_state(cur); blockers += _validate_target(st)
    except Exception as exc: blockers.append(f"db_read_failed:{exc}")
    pkg={"component":"phase11_production_customer_lifecycle_execution_package","repository_version":__version__,"package_id":f"phase11-lifecycle-{uuid.uuid4()}","operator_context":_operator_context(backup_root),"target":{"customer_key":TARGET_CUSTOMER_KEY,"lane":TARGET_LANE,"port":TARGET_PORT},"expected_before_state":st,"intended_lifecycle_operation":{"operation":"controlled_renew_evidence_metadata_update","service_days_from_before_state":(st or {}).get("service_days"),"lifecycle_note":f"Phase 11 controlled lifecycle execution evidence {__version__}; DB-only reversible metadata update"},"required_confirmation_flags":["operator_confirmed","i_understand_db_only","i_understand_no_firewall_apply","i_understand_no_runtime_change","i_understand_phase11_not_completed"],"safety_contract":_gate_contract()|{"firewall_apply_performed":False,"conntrack_flush_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False},"blockers":blockers,"mutation_performed":False,"db_mutation_performed":False,"final_decision":"PACKAGE_READY" if not blockers else "BLOCKED"}
    pkg["package_sha256"]=_hash_pkg(pkg)
    if out_json: out_json.write_text(json.dumps(pkg, indent=2, default=str)+"\n", encoding="utf-8")
    return pkg

def preflight(package_file: Path, config_path: Path = DEFAULT_CONFIG_PATH, *, backup_root: Path = BACKUP_ROOT) -> dict[str, Any]:
    blockers=[]; pkg={}
    try: pkg=_load_json(package_file)
    except Exception as exc: return _controlled_base(component="phase11_production_customer_lifecycle_execution_preflight", blockers=[f"package_json_invalid:{exc}"], final_decision="BLOCKED")
    if pkg.get("final_decision") != "PACKAGE_READY": blockers.append("package_not_ready")
    if pkg.get("blockers") != []: blockers.append("package_blockers_present")
    if not pkg.get("expected_before_state"): blockers.append("expected_before_state_missing")
    if pkg.get("package_sha256") != _hash_pkg(pkg): blockers.append("package_hash_mismatch")
    if pkg.get("target") != {"customer_key":TARGET_CUSTOMER_KEY,"lane":TARGET_LANE,"port":TARGET_PORT}: blockers.append("package_scope_mismatch")
    ctx=_operator_context(backup_root)
    if ctx["effective_user"] != RECOMMENDED_EXECUTION_USER: blockers.append("operator_context_not_recommended_user")
    if not _is_writable(backup_root): blockers.append("backup_root_not_writable_for_effective_user")
    try:
        with _connect(config_path) as conn, conn.cursor() as cur:
            for t in REQ_TABLES:
                cur.execute("select to_regclass(%s)",(t,));
                if cur.fetchone()[0] is None: blockers.append(f"missing_table:{t}")
            for t, cols in REQ_COLUMNS.items():
                for c in cols:
                    cur.execute("select 1 from information_schema.columns where table_name=%s and column_name=%s", (t,c))
                    if cur.fetchone() is None: blockers.append(f"missing_column:{t}.{c}")
            st=_customer_state(cur); blockers += _validate_target(st); exp=pkg.get("expected_before_state") or {}
            for k in ("customer_key","lane","port","status","service_days","lifecycle_note"):
                if str((st or {}).get(k)) != str(exp.get(k)): blockers.append(f"target_state_drift:{k}")
    except Exception as exc: blockers.append(f"db_read_failed:{exc}")
    return _controlled_base(component="phase11_production_customer_lifecycle_execution_preflight", package_id=pkg.get("package_id"), package_sha256=pkg.get("package_sha256"), operator_context=ctx, blockers=sorted(set(blockers)), final_decision="PREFLIGHT_READY" if not blockers else "BLOCKED")

def execute(package_file: Path, config_path: Path = DEFAULT_CONFIG_PATH, *, operator: str, reason: str, backup_root: Path = BACKUP_ROOT, operator_confirmed: bool=False, i_understand_db_only: bool=False, i_understand_no_firewall_apply: bool=False, i_understand_no_runtime_change: bool=False, i_understand_phase11_not_completed: bool=False, out_json: Path|None=None) -> dict[str, Any]:
    if not all([operator_confirmed,i_understand_db_only,i_understand_no_firewall_apply,i_understand_no_runtime_change,i_understand_phase11_not_completed]):
        return _controlled_base(component="phase11_production_customer_lifecycle_execution_execute", final_decision="BLOCKED_CONFIRMATION_REQUIRED", blockers=["confirmation_flags_required"])
    pf=preflight(package_file, config_path, backup_root=backup_root)
    if pf["blockers"]: return pf | {"component":"phase11_production_customer_lifecycle_execution_execute", "final_decision":"BLOCKED_PREFLIGHT"}
    pkg=_load_json(package_file); corr=str(uuid.uuid4()); orphan=None
    try:
        backup_root.mkdir(parents=True, exist_ok=True)
        with _connect(config_path) as conn:
          with conn.transaction(), conn.cursor() as cur:
            st=_customer_state(cur); pol=_list(cur,"select * from customer_policies where customer_id=%s and is_current=true",(st["id"],)); pins=_list(cur,"select * from customer_ip_pins where customer_id=%s",(st["id"],))
            artifact={"artifact_type":"phase11_lifecycle_execution_restore","customer_before_state":st,"current_customer_policy_before_state":pol,"ip_pins_before_state":pins,"operation_metadata":{"operator":operator,"reason":reason,"created_at":datetime.now(UTC).isoformat(),"package_id":pkg["package_id"],"package_sha256":pkg["package_sha256"],"correlation_id":corr}}
            ap=backup_root/f"{corr}.json"; ap.write_text(json.dumps(artifact,indent=2,default=str)+"\n", encoding="utf-8"); orphan=str(ap); bsha=hashlib.sha256(ap.read_bytes()).hexdigest()
            meta=_canon({"package_id":pkg["package_id"],"correlation_id":corr})
            cur.execute("insert into backups (backup_type,path,checksum,status,created_by,verified_at,metadata_json) values (%s,%s,%s,%s,%s,now(),%s::jsonb) returning id",("phase11_lifecycle_execution",str(ap),bsha,"prepared",operator,meta)); bid=cur.fetchone()[0]
            cur.execute("insert into restore_points (restore_type,subject_type,subject_id,backup_id,metadata_json,created_by,reason,checksum) values (%s,%s,%s,%s,%s::jsonb,%s,%s,%s) returning id",("customer_lifecycle","customer",st["id"],bid,meta,operator,reason,bsha)); rpid=cur.fetchone()[0]
            new_note=f"Phase 11 controlled lifecycle execution evidence {__version__}; previous_note={st.get('lifecycle_note') or ''}"[:1000]
            cur.execute("update customers set lifecycle_note=%s, service_days=service_days, updated_at=now(), updated_by=%s where id=%s",(new_note,operator,st["id"]))
            cur.execute("insert into events (event_type,severity,subject_type,subject_id,message,data_json,created_by,correlation_id) values (%s,'info','customer',%s,%s,%s::jsonb,%s,%s) returning id",("phase11.production_customer_lifecycle_execution",st["id"],"Phase 11 controlled DB-only lifecycle execution evidence",_canon({"backup_id":bid,"restore_point_id":rpid,"package_id":pkg["package_id"],"correlation_id":corr}),operator,corr)); eid=cur.fetchone()[0]
            cur.execute("insert into audit_log (actor_type,actor_id,action,resource_type,resource_id,before_json,after_json,reason,correlation_id) values ('operator',%s,%s,'customer',%s,%s::jsonb,%s::jsonb,%s,%s) returning id",(operator,"phase11.production_customer_lifecycle_execution",st["id"],_canon(st),_canon({"lifecycle_note":new_note,"package_id":pkg["package_id"],"correlation_id":corr}),reason,corr)); aid=cur.fetchone()[0]
        out=_controlled_base(final_decision="PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_RECORDED", package_id=pkg["package_id"], package_sha256=pkg["package_sha256"], correlation_id=corr, customer_id=st["id"], backup_id=bid, backup_path=str(ap), backup_sha256=bsha, restore_point_id=rpid, event_id=eid, audit_id=aid, mutation_performed=True, db_mutation_performed=True)
    except Exception as exc:
        out=_controlled_base(component="phase11_production_customer_lifecycle_execution_execute", final_decision="BLOCKED_EXECUTION_ERROR", blockers=[f"execution_error:{exc}"], orphan_backup_artifact=orphan, package_id=pkg.get("package_id"), correlation_id=corr)
    if out_json: out_json.write_text(json.dumps(out, indent=2, default=str)+"\n", encoding="utf-8")
    return out

def _first_row(config, sql: str, params: tuple[object, ...]) -> tuple[dict[str, Any] | None, str | None]:
    result = query_database_params(config, sql, params)
    if not result.ok:
        return None, result.message
    return (result.rows[0] if result.rows else None), None


def verify(evidence_file: Path, config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    blockers=[]; ev={}
    try: ev=_load_json(evidence_file)
    except FileNotFoundError: return _controlled_base(component="phase11_production_customer_lifecycle_execution_verify", blockers=["evidence_file_missing"], final_decision="BLOCKED")
    except json.JSONDecodeError as exc: return _controlled_base(component="phase11_production_customer_lifecycle_execution_verify", blockers=[f"evidence_json_invalid:{exc}"], final_decision="BLOCKED")
    except Exception as exc: return _controlled_base(component="phase11_production_customer_lifecycle_execution_verify", blockers=[f"evidence_read_failed:{exc}"], final_decision="BLOCKED")
    p=Path(ev.get("backup_path") or "")
    if not p.exists(): blockers.append("backup_artifact_missing")
    elif hashlib.sha256(p.read_bytes()).hexdigest() != ev.get("backup_sha256"): blockers.append("backup_checksum_mismatch")
    for flag in ("firewall_apply_performed","conntrack_flush_performed","docker_restart_performed","systemd_restart_performed","phase12_start_allowed"):
        if ev.get(flag) is not False: blockers.append(f"forbidden_flag:{flag}")
    try:
        cfg = load_config(config_path)
        st, err = _first_row(cfg, """select c.id,c.customer_key,lower(l.name) as lane,c.port,c.status,c.service_days,c.lifecycle_note,c.starts_at,c.expires_at,c.activated_at,c.updated_at from customers c join lanes l on l.id=c.lane_id where c.customer_key=%s""", (TARGET_CUSTOMER_KEY,))
        if err: raise RuntimeError(err)
        blockers += _validate_target(st)
        backup, err = _first_row(cfg, "select id,metadata_json from backups where id=%s", (ev.get("backup_id"),))
        if err: raise RuntimeError(err)
        rp, err = _first_row(cfg, "select backup_id,subject_id,metadata_json from restore_points where id=%s", (ev.get("restore_point_id"),))
        if err: raise RuntimeError(err)
        event, err = _first_row(cfg, "select event_type,data_json,correlation_id from events where id=%s", (ev.get("event_id"),))
        if err: raise RuntimeError(err)
        audit, err = _first_row(cfg, "select action,after_json,correlation_id from audit_log where id=%s", (ev.get("audit_id"),))
        if err: raise RuntimeError(err)
        if backup is None: blockers.append("missing_backups_row")
        if rp is None: blockers.append("missing_restore_points_row")
        if event is None: blockers.append("missing_events_row")
        if audit is None: blockers.append("missing_audit_log_row")
        want_pkg=ev.get("package_id"); want_corr=ev.get("correlation_id")
        def has_meta(obj):
            if isinstance(obj, str):
                try: obj=json.loads(obj)
                except Exception: return False
            return isinstance(obj, dict) and obj.get("package_id")==want_pkg and obj.get("correlation_id")==want_corr
        if backup and not has_meta(backup.get("metadata_json")): blockers.append("backup_correlation_mismatch")
        if rp:
            if int(rp.get("backup_id") or -1) != int(ev.get("backup_id") or -1) or int(rp.get("subject_id") or -1) != int(ev.get("customer_id") or -1): blockers.append("restore_point_link_mismatch")
            if not has_meta(rp.get("metadata_json")): blockers.append("restore_point_correlation_mismatch")
        if event:
            if event.get("event_type") != "phase11.production_customer_lifecycle_execution": blockers.append("event_type_mismatch")
            if event.get("correlation_id") != want_corr or not has_meta(event.get("data_json")): blockers.append("event_correlation_mismatch")
        if audit:
            if audit.get("action") != "phase11.production_customer_lifecycle_execution": blockers.append("audit_action_mismatch")
            if audit.get("correlation_id") != want_corr or not has_meta(audit.get("after_json")): blockers.append("audit_correlation_mismatch")
    except Exception as exc: blockers.append(f"db_read_failed:{exc}")
    return _controlled_base(component="phase11_production_customer_lifecycle_execution_verify", package_id=ev.get("package_id"), package_sha256=ev.get("package_sha256"), correlation_id=ev.get("correlation_id"), blockers=sorted(set(blockers)), final_decision=READY if not blockers else "BLOCKED")
