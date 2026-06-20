from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig
from mpf.services import firewall_no_customer_apply_acceptance_gate_service, firewall_no_customer_apply_scaffold_service

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

_MUTATION_SAFETY_FLAGS = (
    "live_firewall_write_allowed",
    "live_firewall_apply_allowed",
    "live_firewall_verify_allowed",
    "live_firewall_rollback_allowed",
    "iptables_restore_allowed",
    "iptables_restore_executed",
    "subprocess_firewall_calls_allowed",
    "subprocess_firewall_calls_executed",
    "real_adapter_allowed",
    "real_adapter_executed",
    "restore_point_write_allowed",
    "restore_point_written",
    "lock_acquisition_allowed",
    "lock_acquired",
    "db_apply_record_write_allowed",
    "db_apply_record_written",
    "db_mutation",
    "filesystem_write_executed",
    "customer_nat_allowed",
    "customer_nat_changed",
    "customer_firewall_rules_allowed",
    "customer_firewall_rules_changed",
    "production_traffic_changed",
    "usage_automation_allowed",
    "abuse_automation_allowed_runtime",
    "ui_allowed_runtime",
    "telegram_allowed_runtime",
)


def _all_mutation_safety_flags_false(report: dict[str, object]) -> bool:
    return all(report.get(key) is False for key in _MUTATION_SAFETY_FLAGS)

def _parse_current_state_block(text: str) -> dict[str, str] | None:
    start = text.find("## Current State")
    if start < 0:
        return None
    code_start = text.find("```text", start)
    if code_start < 0:
        return None
    code_end = text.find("```", code_start + 7)
    if code_end < 0:
        return None
    parsed: dict[str, str] = {}
    for line in text[code_start + 7:code_end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            parsed[k.strip()] = v.strip()
    return parsed or None

def build_no_customer_apply_execution_gate_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = root / "docs" / "PHASE_STATUS.md"
    blockers: list[str] = []
    errors: list[str] = []
    text = phase_status.read_text(encoding="utf-8") if phase_status.exists() else ""
    if not phase_status.exists():
        blockers.append("historical phase-status archive is missing")

    current_state = _parse_current_state_block(text)
    current_state_preserved = current_state is not None and all(current_state.get(k) == v for k, v in _EXPECTED_CURRENT_STATE.items())
    if current_state is None:
        blockers.append("Current State block missing or malformed in docs/PHASE_STATUS.md")
    elif not current_state_preserved:
        blockers.append("Current State block does not match required phase gate values")

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    runtime_activation_allowed = bool(cfg.proxy.runtime_activation_allowed)
    if not apply_mode_plan_only:
        blockers.append("firewall.apply_mode is not plan_only")
    if runtime_activation_allowed:
        blockers.append("proxy.runtime_activation_allowed is true")

    read_only_snapshot_evidence_present = "### Phase 6 Read-Only iptables-save Snapshot — Server Evidence" in text
    controlled_restore_lock_record_evidence_present = "### Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence" in text
    dedicated_apply_gate_proposal_present = "### Phase 6 Dedicated Apply Gate — Proposal Review" in text
    no_customer_apply_scaffold_section_present = "### Phase 6 No-Customer Apply/Verify/Rollback Scaffold — Report-Only" in text
    no_customer_apply_acceptance_gate_section_present = "### Phase 6 No-Customer Apply/Verify/Rollback Acceptance Gate — Report-Only" in text
    no_customer_apply_acceptance_gate_server_evidence_present = "### Phase 6 No-Customer Apply/Verify/Rollback Acceptance Gate — Server Evidence" in text

    checks=[(read_only_snapshot_evidence_present,"missing Phase 6 Read-Only iptables-save Snapshot — Server Evidence section"),(controlled_restore_lock_record_evidence_present,"missing Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence section"),(dedicated_apply_gate_proposal_present,"missing Phase 6 Dedicated Apply Gate — Proposal Review section"),(no_customer_apply_scaffold_section_present,"missing Phase 6 No-Customer Apply/Verify/Rollback Scaffold — Report-Only section"),(no_customer_apply_acceptance_gate_section_present,"missing Phase 6 No-Customer Apply/Verify/Rollback Acceptance Gate — Report-Only section"),(no_customer_apply_acceptance_gate_server_evidence_present,"missing Phase 6 No-Customer Apply/Verify/Rollback Acceptance Gate — Server Evidence section")]
    for ok,msg in checks:
        if not ok:blockers.append(msg)
    for token,msg in (("CONTROLLED_BOUNDARY_EXECUTED","missing CONTROLLED_BOUNDARY_EXECUTED evidence"),("restore_point_id=1","missing restore_point_id=1 evidence"),("firewall_apply_id=1","missing firewall_apply_id=1 evidence")):
        if token not in text:blockers.append(msg)

    scaffold=firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report(cfg,repo_root=root)
    acc=firewall_no_customer_apply_acceptance_gate_service.build_no_customer_apply_acceptance_gate_report(cfg,repo_root=root)
    no_customer_apply_scaffold_report_present=bool(scaffold)
    no_customer_apply_scaffold_blocked=scaffold.get("final_decision")=="BLOCKED"
    no_customer_apply_scaffold_execution_disallowed=scaffold.get("execution_allowed") is False
    no_customer_apply_scaffold_mutation_flags_false = _all_mutation_safety_flags_false(scaffold)
    no_customer_apply_acceptance_gate_report_present=bool(acc)
    no_customer_apply_acceptance_gate_blocked=acc.get("final_decision")=="BLOCKED"
    no_customer_apply_acceptance_gate_execution_disallowed=acc.get("execution_allowed") is False
    no_customer_apply_acceptance_gate_mutation_flags_false = _all_mutation_safety_flags_false(acc)

    for ok,msg in ((no_customer_apply_scaffold_report_present,"scaffold report is missing"),(no_customer_apply_scaffold_blocked,"scaffold report is not BLOCKED"),(no_customer_apply_scaffold_execution_disallowed,"scaffold execution_allowed is not false"),(no_customer_apply_scaffold_mutation_flags_false,"scaffold mutation flag is true"),(no_customer_apply_acceptance_gate_report_present,"acceptance gate report is missing"),(no_customer_apply_acceptance_gate_blocked,"acceptance gate report is not BLOCKED"),(no_customer_apply_acceptance_gate_execution_disallowed,"acceptance gate execution_allowed is not false"),(no_customer_apply_acceptance_gate_mutation_flags_false,"acceptance gate mutation flag is true")):
        if not ok:blockers.append(msg)

    req={"current_state_preserved":current_state_preserved,"config_apply_mode_plan_only":apply_mode_plan_only,"proxy_runtime_activation_disabled":not runtime_activation_allowed,"read_only_snapshot_evidence_present":read_only_snapshot_evidence_present,"controlled_restore_lock_record_evidence_present":controlled_restore_lock_record_evidence_present,"dedicated_apply_gate_proposal_present":dedicated_apply_gate_proposal_present,"no_customer_apply_scaffold_present":no_customer_apply_scaffold_report_present,"no_customer_apply_acceptance_gate_present":no_customer_apply_acceptance_gate_report_present,"no_customer_apply_acceptance_gate_server_evidence_present":no_customer_apply_acceptance_gate_server_evidence_present,"no_customer_apply_scaffold_blocked":no_customer_apply_scaffold_blocked,"no_customer_apply_acceptance_gate_blocked":no_customer_apply_acceptance_gate_blocked,"no_customer_apply_scaffold_execution_disallowed":no_customer_apply_scaffold_execution_disallowed,"no_customer_apply_acceptance_gate_execution_disallowed":no_customer_apply_acceptance_gate_execution_disallowed,"no_customer_apply_scaffold_mutation_flags_false":no_customer_apply_scaffold_mutation_flags_false,"no_customer_apply_acceptance_gate_mutation_flags_false":no_customer_apply_acceptance_gate_mutation_flags_false,"no_customer_nat":True,"no_customer_firewall_rules":True,"no_production_traffic":True,"no_usage_automation":True,"no_abuse_automation":True,"explicit_future_execution_acceptance_required":False,"fresh_farm5_execution_evidence_required":False,"rollback_verification_required":False,"post_apply_verify_required":False}

    checklist=[{"item":k,"status":"PASS" if v else "BLOCKED"} for k,v in req.items()]
    report={"component":"firewall_no_customer_apply_execution_gate","phase":"Phase 6 — Firewall Planner","gate_type":"no_customer_apply_verify_rollback_controlled_execution_gate","final_decision":"BLOCKED","authorization_status":"NOT_ACCEPTED_FOR_EXECUTION","gate_status":"EXECUTION_GATE_REPORT_ONLY","inspection_only":True,"report_only":True,"preflight_only":True,"dry_run":True,"execution_allowed":False,"apply_decision":"BLOCKED","verify_decision":"BLOCKED","rollback_decision":"BLOCKED","production_traffic":"none","firewall_apply_allowed":"no","abuse_automation_allowed":"no","live_snapshot_read_allowed":"iptables_save_read_only","restore_lock_record_execution_allowed":"controlled_boundary_only","current_state_preserved":current_state_preserved,"apply_mode_plan_only":apply_mode_plan_only,"runtime_activation_allowed":runtime_activation_allowed,"read_only_snapshot_evidence_present":read_only_snapshot_evidence_present,"controlled_restore_lock_record_evidence_present":controlled_restore_lock_record_evidence_present,"dedicated_apply_gate_proposal_present":dedicated_apply_gate_proposal_present,"no_customer_apply_scaffold_section_present":no_customer_apply_scaffold_section_present,"no_customer_apply_acceptance_gate_section_present":no_customer_apply_acceptance_gate_section_present,"no_customer_apply_acceptance_gate_server_evidence_present":no_customer_apply_acceptance_gate_server_evidence_present,"no_customer_apply_scaffold_report_present":no_customer_apply_scaffold_report_present,"no_customer_apply_scaffold_blocked":no_customer_apply_scaffold_blocked,"no_customer_apply_scaffold_execution_disallowed":no_customer_apply_scaffold_execution_disallowed,"no_customer_apply_scaffold_mutation_flags_false":no_customer_apply_scaffold_mutation_flags_false,"no_customer_apply_acceptance_gate_report_present":no_customer_apply_acceptance_gate_report_present,"no_customer_apply_acceptance_gate_blocked":no_customer_apply_acceptance_gate_blocked,"no_customer_apply_acceptance_gate_execution_disallowed":no_customer_apply_acceptance_gate_execution_disallowed,"no_customer_apply_acceptance_gate_mutation_flags_false":no_customer_apply_acceptance_gate_mutation_flags_false,"execution_readiness_checklist":checklist,
"live_firewall_write_allowed":False,"live_firewall_apply_allowed":False,"live_firewall_verify_allowed":False,"live_firewall_rollback_allowed":False,"iptables_restore_allowed":False,"iptables_restore_executed":False,"subprocess_firewall_calls_allowed":False,"subprocess_firewall_calls_executed":False,"real_adapter_allowed":False,"real_adapter_executed":False,"restore_point_write_allowed":False,"restore_point_written":False,"lock_acquisition_allowed":False,"lock_acquired":False,"db_apply_record_write_allowed":False,"db_apply_record_written":False,"db_mutation":False,"filesystem_write_executed":False,"customer_nat_allowed":False,"customer_nat_changed":False,"customer_firewall_rules_allowed":False,"customer_firewall_rules_changed":False,"production_traffic_changed":False,"usage_automation_allowed":False,"abuse_automation_allowed_runtime":False,"ui_allowed_runtime":False,"telegram_allowed_runtime":False,"blockers":blockers,"errors":errors}
    return report
