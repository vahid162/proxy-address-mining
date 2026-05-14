from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services.firewall_no_customer_apply_execution_gate_service import build_no_customer_apply_execution_gate_report

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
_MUTATION_FLAGS=("live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","restore_point_write_allowed","restore_point_written","lock_acquisition_allowed","lock_acquired","db_apply_record_write_allowed","db_apply_record_written","db_mutation","filesystem_write_executed","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","usage_automation_allowed","abuse_automation_allowed_runtime","ui_allowed_runtime","telegram_allowed_runtime")

def _parse_current_state_block(text:str)->dict[str,str]|None:
    s=text.find("## Current State")
    if s<0:return None
    a=text.find("```text",s); b=text.find("```",a+7) if a>=0 else -1
    if a<0 or b<0:return None
    out={}
    for line in text[a+7:b].strip().splitlines():
        if ":" in line:
            k,v=line.split(":",1); out[k.strip()]=v.strip()
    return out or None

def _all_false(report:dict[str,object])->bool:
    return all(report.get(k) is False for k in _MUTATION_FLAGS)

def build_no_customer_apply_package_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root=repo_root or Path(__file__).resolve().parents[2]
    ps=root/"docs"/"PHASE_STATUS.md"
    blockers=[]; errors=[]
    text=ps.read_text(encoding='utf-8') if ps.exists() else ""
    if not ps.exists(): blockers.append("docs/PHASE_STATUS.md is missing")
    current=_parse_current_state_block(text)
    current_state_preserved=current is not None and all(current.get(k)==v for k,v in _EXPECTED_CURRENT_STATE.items())
    if current is None:blockers.append("Current State block missing or malformed in docs/PHASE_STATUS.md")
    elif not current_state_preserved:blockers.append("Current State block does not match required phase gate values")
    apply_mode_plan_only=cfg.firewall.apply_mode=="plan_only"
    runtime_activation_allowed=bool(cfg.proxy.runtime_activation_allowed)
    if not apply_mode_plan_only:blockers.append("firewall.apply_mode is not plan_only")
    if runtime_activation_allowed:blockers.append("proxy.runtime_activation_allowed is true")

    needed=[
        ("### Phase 6 Read-Only iptables-save Snapshot — Server Evidence","read-only snapshot evidence is missing"),
        ("### Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence","controlled restore/lock/db apply record evidence is missing"),
        ("### Phase 6 No-Customer Apply/Verify/Rollback Acceptance Gate — Server Evidence","no-customer acceptance-gate server evidence is missing"),
        ("### Phase 6 No-Customer Apply/Verify/Rollback Execution Gate — Server Evidence","no-customer execution-gate server evidence is missing"),
    ]
    for token,msg in needed:
        if token not in text:blockers.append(msg)

    eg=build_no_customer_apply_execution_gate_report(cfg,repo_root=root)
    if not eg:blockers.append("execution-gate report is missing")
    if eg.get("final_decision")!="BLOCKED": blockers.append("execution-gate report is not BLOCKED")
    if eg.get("execution_allowed") is not False: blockers.append("execution-gate execution_allowed is not false")
    if not _all_false(eg): blockers.append("execution-gate mutation flags are not all false")

    seq=[
        "load current state","verify read-only snapshot evidence","verify restore/lock/db apply record evidence",
        "verify no-customer acceptance-gate server evidence","verify no-customer execution-gate server evidence",
        "build no-customer-safe payload","apply no-customer-safe payload","verify no-customer result","rollback no-customer result","record execution evidence"
    ]
    modeled_sequence=[{"step":s,"executable":False,"executed":False,"future_command":"-"} for s in seq]
    report={"component":"firewall_no_customer_apply_package","phase":"Phase 6 — Firewall Planner","package_type":"no_customer_apply_verify_rollback_package","final_decision":"BLOCKED","authorization_status":"PACKAGE_DEFINED_NOT_EXECUTABLE","package_status":"ARTIFACT_ONLY","inspection_only":True,"report_only":True,"preflight_only":True,"dry_run":True,"execution_allowed":False,"apply_decision":"BLOCKED","verify_decision":"BLOCKED","rollback_decision":"BLOCKED","current_state_preserved":current_state_preserved,"apply_mode_plan_only":apply_mode_plan_only,"runtime_activation_allowed":runtime_activation_allowed,
    "payload_kind":"no_customer_safe_payload","payload_contains_customer_nat":False,"payload_contains_customer_firewall_rules":False,"payload_contains_production_traffic":False,"payload_contains_ipv4_customer_refs":False,"payload_contains_ipv6_customer_refs":False,"payload_contains_iptables_restore":False,"payload_contains_subprocess_call":False,"payload_contains_db_write":False,"payload_contains_file_write":False,"payload_contains_lock_acquisition":False,"payload_contains_restore_point_write":False,
    "modeled_sequence":modeled_sequence,
    **{k:False for k in _MUTATION_FLAGS},"blockers":blockers,"errors":errors}
    return report
