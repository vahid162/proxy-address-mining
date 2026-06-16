"""Controlled DB-only Phase 11 customer lifecycle execution evidence."""
from __future__ import annotations

import hashlib, json, uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config

TARGET_CUSTOMER_KEY="limited-btc-001"; TARGET_LANE="btc"; TARGET_PORT=20101
BACKUP_ROOT=Path("/var/backups/mpf/phase11-lifecycle-execution")
READY="PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"

REQ_TABLES=("customers","customer_policies","customer_ip_pins","events","audit_log","backups","restore_points")


def _canon(o: Any)->str: return json.dumps(o, sort_keys=True, separators=(",",":"), default=str)
def _sha_text(s: str)->str: return hashlib.sha256(s.encode()).hexdigest()
def _load_json(p: Path)->dict[str, Any]: return json.loads(p.read_text())
def _hash_pkg(pkg: dict[str, Any])->str:
    body=dict(pkg); body.pop("package_sha256", None); return _sha_text(_canon(body))
def _gate_contract()->dict[str, Any]:
    return {"production_traffic":"controlled_cli_limited","customer_onboarding_allowed":"controlled_cli_limited","phase12_start_allowed":False,"worker_enforcement_allowed":"no","ui_allowed":"no","telegram_allowed":"no"}

def _connect(config_path: Path):
    import psycopg
    return psycopg.connect(load_config(config_path).database.url, connect_timeout=5)

def _dict(cur, sql: str, params: tuple=())->dict[str, Any]|None:
    cur.execute(sql, params); row=cur.fetchone()
    if row is None: return None
    cols=[d.name if hasattr(d,"name") else d[0] for d in cur.description]
    return dict(zip(cols,row, strict=False))

def _list(cur, sql: str, params: tuple=())->list[dict[str, Any]]:
    cur.execute(sql, params); rows=cur.fetchall(); cols=[d.name if hasattr(d,"name") else d[0] for d in cur.description]
    return [dict(zip(cols,r, strict=False)) for r in rows]

def _customer_state(cur)->dict[str, Any]|None:
    return _dict(cur,"""select c.id,c.customer_key,lower(l.name) as lane,c.port,c.status,c.service_days,c.lifecycle_note,c.starts_at,c.expires_at,c.activated_at,c.updated_at from customers c join lanes l on l.id=c.lane_id where c.customer_key=%s""",(TARGET_CUSTOMER_KEY,))

def _validate_target(st: dict[str, Any]|None)->list[str]:
    b=[]
    if not st: return ["target_customer_missing"]
    if st.get("customer_key")!=TARGET_CUSTOMER_KEY: b.append("customer_key_mismatch")
    if str(st.get("lane")).lower()!=TARGET_LANE: b.append("lane_mismatch")
    if int(st.get("port") or 0)!=TARGET_PORT: b.append("port_mismatch")
    if st.get("status")!="active": b.append("target_customer_not_active")
    return b

def build_package(config_path: Path=DEFAULT_CONFIG_PATH, *, out_json: Path|None=None)->dict[str, Any]:
    blockers=[]; st=None
    try:
        with _connect(config_path) as conn, conn.cursor() as cur: st=_customer_state(cur); blockers+=_validate_target(st)
    except Exception as exc: blockers.append(f"db_read_failed:{exc}")
    pkg={"component":"phase11_production_customer_lifecycle_execution_package","repository_version":__version__,"package_id":f"phase11-lifecycle-{uuid.uuid4()}","target":{"customer_key":TARGET_CUSTOMER_KEY,"lane":TARGET_LANE,"port":TARGET_PORT},"expected_before_state":st,"intended_lifecycle_operation":{"operation":"controlled_renew_evidence_metadata_update","service_days_from_before_state":(st or {}).get("service_days"),"lifecycle_note":"Phase 11 controlled lifecycle execution evidence 0.1.278; DB-only reversible metadata update"},"required_confirmation_flags":["operator_confirmed","i_understand_db_only","i_understand_no_firewall_apply","i_understand_no_runtime_change","i_understand_phase11_not_completed"],"safety_contract":_gate_contract()|{"firewall_apply_performed":False,"conntrack_flush_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False},"blockers":blockers,"mutation_performed":False,"db_mutation_performed":False,"final_decision":"PACKAGE_READY" if not blockers else "BLOCKED"}
    pkg["package_sha256"]=_hash_pkg(pkg)
    if out_json: out_json.write_text(json.dumps(pkg,indent=2,default=str)+"\n")
    return pkg

def preflight(package_file: Path, config_path: Path=DEFAULT_CONFIG_PATH)->dict[str, Any]:
    pkg=_load_json(package_file); blockers=[]
    if pkg.get("package_sha256")!=_hash_pkg(pkg): blockers.append("package_hash_mismatch")
    if pkg.get("target")!={"customer_key":TARGET_CUSTOMER_KEY,"lane":TARGET_LANE,"port":TARGET_PORT}: blockers.append("package_scope_mismatch")
    try:
        with _connect(config_path) as conn, conn.cursor() as cur:
            for t in REQ_TABLES:
                cur.execute("select to_regclass(%s)",(t,));
                if cur.fetchone()[0] is None: blockers.append(f"missing_table:{t}")
            st=_customer_state(cur); blockers+=_validate_target(st)
            exp=pkg.get("expected_before_state") or {}
            for k in ("customer_key","lane","port","status","service_days","lifecycle_note"):
                if str((st or {}).get(k))!=str(exp.get(k)): blockers.append(f"target_state_drift:{k}")
    except Exception as exc: blockers.append(f"db_read_failed:{exc}")
    return {"component":"phase11_production_customer_lifecycle_execution_preflight","repository_version":__version__,"package_id":pkg.get("package_id"),"package_sha256":pkg.get("package_sha256"),"blockers":sorted(set(blockers)),"mutation_performed":False,"db_mutation_performed":False,"firewall_apply_performed":False,"final_decision":"PREFLIGHT_READY" if not blockers else "BLOCKED"}

def execute(package_file: Path, config_path: Path=DEFAULT_CONFIG_PATH, *, operator: str, reason: str, backup_root: Path=BACKUP_ROOT, operator_confirmed: bool=False, i_understand_db_only: bool=False, i_understand_no_firewall_apply: bool=False, i_understand_no_runtime_change: bool=False, i_understand_phase11_not_completed: bool=False, out_json: Path|None=None)->dict[str, Any]:
    if not all([operator_confirmed,i_understand_db_only,i_understand_no_firewall_apply,i_understand_no_runtime_change,i_understand_phase11_not_completed]):
        return {"final_decision":"BLOCKED_CONFIRMATION_REQUIRED","db_mutation_performed":False,"firewall_apply_performed":False,"phase12_start_allowed":False}
    pf=preflight(package_file,config_path)
    if pf["blockers"]: return pf|{"final_decision":"BLOCKED_PREFLIGHT"}
    pkg=_load_json(package_file); corr=str(uuid.uuid4()); backup_root.mkdir(parents=True, exist_ok=True)
    with _connect(config_path) as conn:
      with conn.transaction(), conn.cursor() as cur:
        st=_customer_state(cur); pol=_list(cur,"select * from customer_policies where customer_id=%s and is_current=true",(st["id"],)); pins=_list(cur,"select * from customer_ip_pins where customer_id=%s",(st["id"],))
        artifact={"artifact_type":"phase11_lifecycle_execution_restore","customer_before_state":st,"current_customer_policy_before_state":pol,"ip_pins_before_state":pins,"operation_metadata":{"operator":operator,"reason":reason,"created_at":datetime.now(UTC).isoformat(),"package_id":pkg["package_id"],"package_sha256":pkg["package_sha256"],"correlation_id":corr}}
        ap=backup_root/f"{corr}.json"; ap.write_text(json.dumps(artifact,indent=2,default=str)+"\n"); bsha=hashlib.sha256(ap.read_bytes()).hexdigest()
        cur.execute("insert into backups (backup_type,path,checksum,status,created_by,verified_at,metadata_json) values (%s,%s,%s,%s,%s,now(),%s::jsonb) returning id",("phase11_lifecycle_execution",str(ap),bsha,"prepared",operator,_canon({"package_id":pkg["package_id"],"correlation_id":corr}))); bid=cur.fetchone()[0]
        cur.execute("insert into restore_points (restore_type,subject_type,subject_id,backup_id,metadata_json,created_by,reason,checksum) values (%s,%s,%s,%s,%s::jsonb,%s,%s,%s) returning id",("customer_lifecycle","customer",st["id"],bid,_canon({"package_id":pkg["package_id"],"correlation_id":corr}),operator,reason,bsha)); rpid=cur.fetchone()[0]
        new_note=f"Phase 11 controlled lifecycle execution evidence 0.1.278; previous_note={st.get('lifecycle_note') or ''}"[:1000]
        cur.execute("update customers set lifecycle_note=%s, service_days=service_days, updated_at=now(), updated_by=%s where id=%s",(new_note,operator,st["id"]))
        cur.execute("insert into events (event_type,severity,subject_type,subject_id,message,data_json,created_by,correlation_id) values (%s,'info','customer',%s,%s,%s::jsonb,%s,%s) returning id",("phase11.production_customer_lifecycle_execution",st["id"],"Phase 11 controlled DB-only lifecycle execution evidence",_canon({"backup_id":bid,"restore_point_id":rpid,"package_id":pkg["package_id"]}),operator,corr)); eid=cur.fetchone()[0]
        cur.execute("insert into audit_log (actor_type,actor_id,action,resource_type,resource_id,before_json,after_json,reason,correlation_id) values ('operator',%s,%s,'customer',%s,%s::jsonb,%s::jsonb,%s,%s) returning id",(operator,"phase11.production_customer_lifecycle_execution",st["id"],_canon(st),_canon({"lifecycle_note":new_note}),reason,corr)); aid=cur.fetchone()[0]
    out={"final_decision":"PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_RECORDED","package_id":pkg["package_id"],"package_sha256":pkg["package_sha256"],"correlation_id":corr,"customer_id":st["id"],"backup_id":bid,"backup_path":str(ap),"backup_sha256":bsha,"restore_point_id":rpid,"event_id":eid,"audit_id":aid,"db_mutation_performed":True,"firewall_apply_performed":False,"conntrack_flush_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False,"phase12_start_allowed":False}
    if out_json: out_json.write_text(json.dumps(out,indent=2,default=str)+"\n")
    return out

def verify(evidence_file: Path, config_path: Path=DEFAULT_CONFIG_PATH)->dict[str, Any]:
    ev=_load_json(evidence_file); blockers=[]
    p=Path(ev.get("backup_path",""))
    if not p.exists(): blockers.append("backup_artifact_missing")
    elif hashlib.sha256(p.read_bytes()).hexdigest()!=ev.get("backup_sha256"): blockers.append("backup_checksum_mismatch")
    for flag in ("firewall_apply_performed","conntrack_flush_performed","docker_restart_performed","systemd_restart_performed","phase12_start_allowed"):
        if ev.get(flag) is not False: blockers.append(f"forbidden_flag:{flag}")
    try:
        with _connect(config_path) as conn, conn.cursor() as cur:
            checks=[("backups",ev.get("backup_id")),("restore_points",ev.get("restore_point_id")),("events",ev.get("event_id")),("audit_log",ev.get("audit_id"))]
            for t,i in checks:
                cur.execute(f"select 1 from {t} where id=%s",(i,));
                if cur.fetchone() is None: blockers.append(f"missing_{t}_row")
            st=_customer_state(cur); blockers+=_validate_target(st)
            cur.execute("select backup_id,subject_id from restore_points where id=%s",(ev.get("restore_point_id"),)); rp=cur.fetchone()
            if not rp or int(rp[0])!=int(ev.get("backup_id")) or int(rp[1])!=int(ev.get("customer_id")): blockers.append("restore_point_link_mismatch")
    except Exception as exc: blockers.append(f"db_read_failed:{exc}")
    return {"component":"phase11_production_customer_lifecycle_execution_verify","repository_version":__version__,"package_id":ev.get("package_id"),"package_sha256":ev.get("package_sha256"),"correlation_id":ev.get("correlation_id"),"blockers":sorted(set(blockers)),"mutation_performed":False,"db_mutation_performed":False,"firewall_apply_performed":False,"conntrack_flush_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False,"phase12_start_allowed":False,"worker_enforcement_allowed":"no","ui_allowed":"no","telegram_allowed":"no","production_traffic":"controlled_cli_limited","customer_onboarding_allowed":"controlled_cli_limited","final_decision":READY if not blockers else "BLOCKED"}
