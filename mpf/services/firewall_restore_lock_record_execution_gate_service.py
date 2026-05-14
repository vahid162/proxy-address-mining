from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import uuid

from mpf.config import MPFConfig

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

def run_restore_lock_record_controlled_execution(cfg: MPFConfig, repo_root: Path | None = None, *, execute_controlled_boundary: bool = False, operator: str | None = None, reason: str | None = None, yes: bool = False, record_writer=None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"
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
    report={"component":"firewall_restore_lock_record_execution_gate","phase":"Phase 6 — Firewall Planner","final_decision":"BLOCKED","gate_status":"CONTROLLED_BOUNDARY_READY" if evidence["controlled_execution_boundary_accepted_present"] else "EXECUTION_GATE_SCAFFOLD_READY","authorization_status":"CONTROLLED_BOUNDARY_EXECUTED" if execution_allowed else "CONTROLLED_BOUNDARY_ACCEPTED_DRY_RUN","inspection_only":not execution_allowed,"report_only":not execution_allowed,"preflight_only":not execution_allowed,"dry_run":dry_run,"execute_controlled_boundary":execute_controlled_boundary,"execution_allowed":execution_allowed,"controlled_boundary_accepted":evidence["controlled_execution_boundary_accepted_present"],"operator":operator or "-","reason":reason or "-","correlation_id":correlation_id,"current_state_preserved":current_state_preserved,"restore_lock_record_execution_allowed":current_state.get("restore_lock_record_execution_allowed",""),"apply_mode_plan_only":apply_mode_plan_only,"runtime_activation_allowed":runtime_activation_allowed,"production_traffic":"none","firewall_apply_allowed":"no","abuse_automation_allowed":"no","live_snapshot_read_allowed":"iptables_save_read_only",**evidence,"farm5_time_sync_resolved":farm5_time_sync_resolved,"restore_point_write_allowed":execute_controlled_boundary,"restore_point_written":False,"restore_point_id":None,"restore_point_artifact_written":False,"restore_point_artifact_path":"-","restore_point_checksum":checksum,"lock_acquisition_allowed":execute_controlled_boundary,"lock_acquired":False,"lock_name":"phase6_restore_lock_record_execution","lock_owner":operator or "-","lock_expires_at":"-","db_apply_record_write_allowed":execute_controlled_boundary,"db_apply_record_written":False,"firewall_apply_id":None,"db_mutation":False,"firewall_snapshot_write_allowed":False,"firewall_snapshot_written":False,"live_firewall_read_allowed":False,"live_firewall_read_executed":False,"iptables_save_allowed":False,"iptables_save_executed":False,"live_firewall_write_allowed":False,"live_firewall_apply_allowed":False,"live_firewall_rollback_allowed":False,"live_firewall_verify_allowed":False,"iptables_restore_allowed":False,"iptables_restore_executed":False,"customer_nat_allowed":False,"customer_nat_changed":False,"customer_firewall_rules_allowed":False,"customer_firewall_rules_changed":False,"production_traffic_changed":False,"usage_automation_allowed":False,"abuse_automation_allowed_runtime":False,"ui_allowed_runtime":False,"telegram_allowed_runtime":False,"apply_decision":"BLOCKED","next_required_gate":"Future Dedicated Phase 6 Apply Gate Proposal/Review","blockers":blockers,"warnings":warnings,"errors":errors}
    if execution_allowed:
        if record_writer is None:
            report["blockers"].append("record_writer is required for controlled execution")
            report["execution_allowed"] = False
            return report
        try:
            now=datetime.now(timezone.utc)
            result=record_writer({"metadata":metadata,"checksum":checksum,"operator":operator,"reason":reason,"lock_name":"phase6_restore_lock_record_execution","lock_expires_at":(now+timedelta(minutes=10)).isoformat(),"backend":cfg.firewall.backend,"apply_mode":cfg.firewall.apply_mode})
            report.update({"restore_point_written":True,"lock_acquired":True,"db_apply_record_written":True,"db_mutation":True,"restore_point_id":result.get("restore_point_id"),"firewall_apply_id":result.get("firewall_apply_id"),"lock_expires_at":result.get("lock_expires_at",report["lock_expires_at"])})
        except Exception as exc:
            report["errors"].append(str(exc))
            report["execution_allowed"]=False
    return report

def build_restore_lock_record_execution_gate_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    return run_restore_lock_record_controlled_execution(cfg, repo_root=repo_root)
