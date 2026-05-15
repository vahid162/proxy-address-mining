from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services.phase7_final_acceptance_readiness_service import build_phase7_final_acceptance_readiness_report


def build_phase7_operator_acceptance_decision_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    readiness = build_phase7_final_acceptance_readiness_report(cfg, repo_root=repo_root)
    runtime_flag_keys = [
        k for k in readiness.keys()
        if (
            k.endswith("_allowed")
            or k.endswith("_executed")
            or (k.endswith("_started") and not k.endswith("_not_started"))
            or k.endswith("_changed")
            or k in {"db_mutation", "filesystem_write_executed", "scheduler_job_created", "timer_enabled"}
        )
    ]
    runtime_flags_all_false = not any(bool(readiness.get(k)) for k in runtime_flag_keys)
    blockers = []
    if readiness.get("blockers"): blockers.append("phase7_final_acceptance_readiness_report_has_blockers")
    if readiness.get("final_decision") != "BLOCKED": blockers.append("phase7_final_acceptance_readiness_report_final_decision_not_blocked")
    if not readiness.get("phase7_doctor_ok"): blockers.append("phase7_doctor_not_ok")
    if not readiness.get("farm5_0_1_107_sync_evidence_present"): blockers.append("farm5_0_1_107_sync_evidence_missing")
    if not readiness.get("abuse_invariant_preserved"): blockers.append("abuse_invariant_missing_or_weakened")
    if not readiness.get("phase8_not_started"): blockers.append("phase8_appears_started")
    if not runtime_flags_all_false: blockers.append("runtime_mutation_safety_flag_true")
    return {
        "component":"phase7_operator_acceptance_decision","phase":"Phase 7 — Usage + Policy/Reject Accounting","gate_type":"phase7_operator_acceptance_decision",
        "operator_decision":"READY_FOR_OPERATOR_ACCEPTANCE","final_decision":"BLOCKED","acceptance_scope":"report_only_service_contract_readiness",
        "recommended_next_phase_after_operator_acceptance":"Phase 8 — Abuse 1h Core planning/readiness",
        "authorization_status":"PHASE7_ACCEPTANCE_DECISION_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED","inspection_only":True,"report_only":True,
        "preflight_only":True,"dry_run":True,"execution_allowed":False,"phase7_acceptance_allowed":False,"phase8_start_allowed":False,
        "operator_review_required":True,"operator_must_explicitly_accept_phase7":True,"separate_phase_gate_update_pr_required":True,
        "phase7_final_acceptance_readiness_clean":not readiness.get("blockers"),"farm5_0_1_107_sync_evidence_present":bool(readiness.get("farm5_0_1_107_sync_evidence_present")),
        "phase7_doctor_ok":bool(readiness.get("phase7_doctor_ok")),"all_phase7_child_reports_clean":bool(readiness.get("phase7_child_reports_clean")),
        "runtime_gates_closed":runtime_flags_all_false,"abuse_invariant_preserved":bool(readiness.get("abuse_invariant_preserved")),"phase8_not_started":bool(readiness.get("phase8_not_started")),
        "decision_summary":["Phase 7 can be considered ready for operator acceptance only as report-only/service-contract/readiness.","Phase 7 acceptance must not be interpreted as production activation.","Phase 7 acceptance must not authorize firewall apply.","Phase 7 acceptance must not authorize customer NAT/customer firewall rules.","Phase 7 acceptance must not authorize usage collectors.","Phase 7 acceptance must not authorize policy/reject collectors.","Phase 7 acceptance must not authorize abuse automation.","Phase 8 Abuse 1h Core remains mandatory before production completeness.","A separate phase gate update PR is required if the operator accepts Phase 7."],
        "blockers":blockers,"errors":[], **{k: readiness.get(k, False) for k in runtime_flag_keys if k in readiness}
    }
