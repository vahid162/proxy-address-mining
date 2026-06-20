from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from mpf.services.historical_phase_status import historical_phase_status_path, read_historical_phase_status
import uuid

from mpf.config import MPFConfig
from mpf.db import _local_peer_dbname, write_controlled_execution_records_local_peer_as_mpf

_EXPECTED_CURRENT_STATE = {
    "current_accepted_phase": "Phase 5 — Customer CRUD in DB Only accepted on farm5",
    "current_working_phase": "Phase 6 — Firewall Planner",
    "server_state": "farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active",
    "production_traffic": "none",
    "firewall_apply_allowed": "no",
    "abuse_automation_allowed": "no",
    "customer_onboarding_allowed": "db_only",
    "proxy_data_plane_allowed": "limited_runtime_local_only",
    "ui_allowed": "no",
    "telegram_allowed": "no",
    "live_snapshot_read_allowed": "iptables_save_read_only",
    "restore_lock_record_execution_allowed": "controlled_boundary_only",
}

def _parse_current_state_block(text: str) -> dict[str, str] | None:
    marker = "## Current State"
    start = text.find(marker)
    if start < 0:
        return None
    code_start = text.find("```text", start)
    if code_start < 0:
        return None
    code_end = text.find("```", code_start + 7)
    if code_end < 0:
        return None
    parsed: dict[str, str] = {}
    for line in text[code_start + 7 : code_end].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed if parsed else None



def _write_controlled_records(connection_factory, *, metadata: dict[str, object], checksum: str, operator: str, reason: str, lock_name: str, lock_expires_at: str, backend: str, apply_mode: str) -> dict[str, object]:
    with connection_factory() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("select 1 from scheduler_locks where lock_name=%s and expires_at > now()", (lock_name,))
                if cur.fetchone() is not None:
                    raise RuntimeError("scoped controlled execution lock already exists")
                cur.execute(
                    """
                    insert into restore_points (restore_type, subject_type, subject_id, snapshot_id, backup_id, metadata_json, created_by, reason, checksum)
                    values (%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s) returning id
                    """,
                    ("firewall", "phase6_controlled_execution", None, None, None, json.dumps(metadata, sort_keys=True), operator, reason, checksum),
                )
                restore_point_id = int(cur.fetchone()[0])
                cur.execute(
                    """
                    insert into scheduler_locks (lock_name, owner, acquired_at, expires_at, metadata_json)
                    values (%s,%s,now(),%s,%s::jsonb) returning expires_at
                    """,
                    (lock_name, operator, lock_expires_at, json.dumps({"controlled_boundary": True, "correlation_id": metadata["correlation_id"], "reason": reason, "apply_decision": "BLOCKED"}, sort_keys=True)),
                )
                lock_exp = cur.fetchone()[0]
                cur.execute(
                    """
                    insert into firewall_applies (action, status, apply_mode, backend, restore_point_id, snapshot_before_id, snapshot_after_id, plan_json, summary, created_by, correlation_id)
                    values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s) returning id
                    """,
                    (
                        "prepare", "blocked", apply_mode, backend, restore_point_id, None, None,
                        json.dumps({"controlled_boundary": True, "apply_decision": "BLOCKED", "no_firewall_apply": True, "no_iptables_restore": True, "no_customer_nat": True, "no_customer_firewall_rules": True, "correlation_id": metadata["correlation_id"]}, sort_keys=True),
                        "controlled restore/lock/db apply record boundary prepared; apply remains blocked", operator, metadata["correlation_id"],
                    ),
                )
                firewall_apply_id = int(cur.fetchone()[0])
    return {"restore_point_id": restore_point_id, "firewall_apply_id": firewall_apply_id, "lock_expires_at": str(lock_exp)}

def _default_connection_factory(cfg: MPFConfig):
    import psycopg

    return lambda: psycopg.connect(cfg.database.url, connect_timeout=5)


def _default_record_writer(cfg: MPFConfig, payload: dict[str, object]) -> dict[str, object]:
    local_peer_dbname = _local_peer_dbname(cfg.database.url)
    if local_peer_dbname and __import__("os").geteuid() == 0:
        result = write_controlled_execution_records_local_peer_as_mpf(
            dbname=local_peer_dbname,
            payload_json=json.dumps(
                {
                    "metadata": payload["metadata"],
                    "checksum": payload["checksum"],
                    "operator": payload["operator"],
                    "reason": payload["reason"],
                    "lock_name": payload["lock_name"],
                    "lock_expires_at": payload["lock_expires_at"],
                    "backend": payload["backend"],
                    "apply_mode": payload["apply_mode"],
                    "lock_metadata": {
                        "controlled_boundary": True,
                        "correlation_id": payload["metadata"]["correlation_id"],
                        "reason": payload["reason"],
                        "apply_decision": "BLOCKED",
                    },
                    "plan_json": {
                        "controlled_boundary": True,
                        "apply_decision": "BLOCKED",
                        "no_firewall_apply": True,
                        "no_iptables_restore": True,
                        "no_customer_nat": True,
                        "no_customer_firewall_rules": True,
                        "correlation_id": payload["metadata"]["correlation_id"],
                    },
                },
                separators=(",", ":"),
            ),
        )
        return {
            "restore_point_id": result.restore_point_id,
            "firewall_apply_id": result.firewall_apply_id,
            "lock_expires_at": result.lock_expires_at,
        }

    connection_factory = _default_connection_factory(cfg)
    return _write_controlled_records(connection_factory, **payload)


def run_restore_lock_record_controlled_execution(cfg: MPFConfig, repo_root: Path | None = None, *, execute_controlled_boundary: bool = False, operator: str | None = None, reason: str | None = None, yes: bool = False, record_writer=None, connection_factory=None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = historical_phase_status_path(root)
    blockers: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    text = phase_status.read_text(encoding="utf-8") if phase_status.exists() else ""
    current_state = _parse_current_state_block(text) or {}
    current_state_preserved = all(current_state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
    required_tokens = {
        "read_only_snapshot_evidence_present": "Phase 6 Read-Only iptables-save Snapshot — Server Evidence",
        "farm5_time_sync_evidence_present": "Phase 6 farm5 Time Synchronization — Server Evidence",
        "restore_lock_record_readiness_evidence_present": "Phase 6 Restore/Lock/DB Apply Record Readiness — Server Sync",
        "restore_lock_record_gate_report_evidence_present": "Phase 6 Restore/Lock/DB Apply Record Gate Report — Server Sync",
        "restore_lock_record_acceptance_gate_evidence_present": "Phase 6 Restore/Lock/DB Apply Record Acceptance Gate — Server Sync",
        "restore_lock_record_execution_scaffold_evidence_present": "Phase 6 Restore/Lock/DB Apply Record Execution Gate Scaffold — Server Sync",
        "controlled_execution_proposal_review_present": "Phase 6 Controlled Restore/Lock/DB Apply Record Execution Gate — Proposal Review",
        "controlled_execution_boundary_accepted_present": "Phase 6 Controlled Restore/Lock/DB Apply Record Execution Boundary — Accepted",
    }
    evidence={k:(v in text) for k,v in required_tokens.items()}
    farm5_time_sync_resolved = all(tok in text for tok in ("System clock synchronized: yes","NTPSynchronized=yes","194.225.150.25"))
    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    runtime_activation_allowed = bool(cfg.proxy.runtime_activation_allowed)
    if not current_state_preserved: blockers.append("Current State does not match required gate")
    if not apply_mode_plan_only: blockers.append("firewall.apply_mode is not plan_only")
    if runtime_activation_allowed: blockers.append("proxy.runtime_activation_allowed is true")
    missing_map={
        "farm5_time_sync_evidence_present":"Phase 6 farm5 Time Synchronization — Server Evidence is missing",
        "restore_lock_record_acceptance_gate_evidence_present":"Phase 6 Restore/Lock/DB Apply Record Acceptance Gate — Server Sync is missing",
    }
    for k,v in evidence.items():
        if not v:
            blockers.append(missing_map.get(k, f"{k} is false"))
    if not farm5_time_sync_resolved: blockers.append("farm5 time sync evidence is incomplete")
    if execute_controlled_boundary and not operator: blockers.append("operator is required for controlled execution")
    if execute_controlled_boundary and not reason: blockers.append("reason is required for controlled execution")
    if execute_controlled_boundary and not yes: blockers.append("--yes is required for controlled execution")
    dry_run=not execute_controlled_boundary
    execution_allowed=execute_controlled_boundary and not blockers
    correlation_id=str(uuid.uuid4())
    metadata={"controlled_boundary":True,"source":"restore_lock_record_execution_gate","apply_decision":"BLOCKED","firewall_apply_allowed":"no","production_traffic":"none","operator":operator or "-","reason":reason or "-","correlation_id":correlation_id}
    checksum=hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    report={"component":"firewall_restore_lock_record_execution_gate","phase":"Phase 6 — Firewall Planner","final_decision":"BLOCKED","gate_status":"CONTROLLED_BOUNDARY_READY" if evidence["controlled_execution_boundary_accepted_present"] else "EXECUTION_GATE_SCAFFOLD_READY","authorization_status":"CONTROLLED_BOUNDARY_EXECUTED" if execution_allowed else "CONTROLLED_BOUNDARY_ACCEPTED_DRY_RUN","inspection_only":not execution_allowed,"report_only":not execution_allowed,"preflight_only":not execution_allowed,"dry_run":dry_run,"execute_controlled_boundary":execute_controlled_boundary,"execution_allowed":execution_allowed,"controlled_boundary_accepted":evidence["controlled_execution_boundary_accepted_present"],"operator":operator or "-","reason":reason or "-","correlation_id":correlation_id,"current_state_preserved":current_state_preserved,"restore_lock_record_execution_allowed":current_state.get("restore_lock_record_execution_allowed",""),"apply_mode_plan_only":apply_mode_plan_only,"runtime_activation_allowed":runtime_activation_allowed,"production_traffic":"none","firewall_apply_allowed":"no","abuse_automation_allowed":"no","live_snapshot_read_allowed":"iptables_save_read_only",**evidence,"farm5_time_sync_resolved":farm5_time_sync_resolved,"restore_point_write_allowed":execution_allowed,"restore_point_written":False,"restore_point_id":None,"restore_point_artifact_written":False,"restore_point_artifact_path":"-","restore_point_checksum":checksum,"lock_acquisition_allowed":execution_allowed,"lock_acquired":False,"lock_name":"phase6_restore_lock_record_execution","lock_owner":operator or "-","lock_expires_at":"-","db_apply_record_write_allowed":execution_allowed,"db_apply_record_written":False,"firewall_apply_id":None,"db_mutation":False,"firewall_snapshot_write_allowed":False,"firewall_snapshot_written":False,"live_firewall_read_allowed":False,"live_firewall_read_executed":False,"iptables_save_allowed":False,"iptables_save_executed":False,"live_firewall_write_allowed":False,"live_firewall_apply_allowed":False,"live_firewall_rollback_allowed":False,"live_firewall_verify_allowed":False,"iptables_restore_allowed":False,"iptables_restore_executed":False,"customer_nat_allowed":False,"customer_nat_changed":False,"customer_firewall_rules_allowed":False,"customer_firewall_rules_changed":False,"production_traffic_changed":False,"usage_automation_allowed":False,"abuse_automation_allowed_runtime":False,"ui_allowed_runtime":False,"telegram_allowed_runtime":False,"apply_decision":"BLOCKED","next_required_gate":"Future Dedicated Phase 6 Apply Gate Proposal/Review","blockers":blockers,"warnings":warnings,"errors":errors}
    if execution_allowed:
        if record_writer is None:
            if connection_factory is None:
                record_writer = lambda payload: _default_record_writer(cfg, payload)
            else:
                record_writer = lambda payload: _write_controlled_records(connection_factory, **payload)
        try:
            now=datetime.now(timezone.utc)
            result=record_writer({"metadata":metadata,"checksum":checksum,"operator":operator,"reason":reason,"lock_name":"phase6_restore_lock_record_execution","lock_expires_at":(now+timedelta(minutes=10)).isoformat(),"backend":cfg.firewall.backend,"apply_mode":cfg.firewall.apply_mode})
            report.update({"restore_point_written":True,"lock_acquired":True,"db_apply_record_written":True,"db_mutation":True,"restore_point_id":result.get("restore_point_id"),"firewall_apply_id":result.get("firewall_apply_id"),"lock_expires_at":result.get("lock_expires_at",report["lock_expires_at"])})
        except Exception as exc:
            report.update({
                "authorization_status": "CONTROLLED_BOUNDARY_EXECUTION_FAILED",
                "inspection_only": True,
                "report_only": True,
                "preflight_only": True,
                "execution_allowed": False,
                "restore_point_write_allowed": False,
                "lock_acquisition_allowed": False,
                "db_apply_record_write_allowed": False,
            })
            report["errors"].append(str(exc))
    return report

def build_restore_lock_record_execution_gate_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    return run_restore_lock_record_controlled_execution(cfg, repo_root=repo_root)
