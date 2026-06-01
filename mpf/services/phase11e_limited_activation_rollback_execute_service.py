from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services import customer_mutation_service, customer_read_service
from mpf.services.phase11e_limited_activation_common import CANARY_KEY, SCOPE, base_report, load_hashed_json, validate_artifact_gate, validate_confirmations, validate_current_phase_gate, validate_expected_version, validate_operator, validate_rollback_package_scope, validate_scope

CONFIRMATIONS=("operator_confirmed","i_understand_this_mutates_limited_customer_db_state","i_understand_rollback_limited_btc_001_only","i_understand_canary_must_be_preserved","i_understand_no_firewall_apply","i_understand_no_conntrack_flush","i_understand_phase11_not_accepted")

def build_phase11e_limited_activation_rollback_execute_report(config: MPFConfig, **kwargs: object)->dict[str,object]:
    blockers:list[str]=[]; warnings:list[str]=[]
    expected=validate_expected_version(kwargs, blockers); validate_operator(kwargs, blockers); validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    execution=load_hashed_json(kwargs,"activation_execution_json","activation_execution_json_sha256",blockers)
    rollback=load_hashed_json(kwargs,"limited_activation_rollback_package_json","limited_activation_rollback_package_json_sha256",blockers)
    artifact=load_hashed_json(kwargs,"artifact_gate_json","artifact_gate_json_sha256",blockers)
    validate_scope(execution,blockers,"activation_execution"); validate_rollback_package_scope(rollback,blockers); validate_artifact_gate(artifact,blockers); validate_current_phase_gate(blockers)
    if execution is not None and execution.get("final_decision")!="PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE": blockers.append("activation_execution_not_ready")
    if rollback is not None and rollback.get("final_decision")!="PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY": blockers.append("rollback_package_not_ready")
    rows=customer_read_service.list_customer_status(config,include_deleted=False,limit=5000)
    limited=canary=None
    if not rows.ok: blockers.append("customer_state_read_failed")
    else:
        lm=[r for r in rows.customers if r.customer_key==SCOPE["candidate_customer_key"]]; ca=[r for r in rows.customers if r.customer_key==CANARY_KEY]
        if len(lm)!=1: blockers.append("limited_customer_missing_or_ambiguous")
        else:
            limited=lm[0]
            if limited.status!="active": blockers.append("limited_customer_not_active")
            if limited.lane!=SCOPE["lane"] or limited.port!=SCOPE["public_port"]: blockers.append("limited_customer_scope_mismatch")
        if len(ca)!=1 or ca[0].status!="active": blockers.append("canary_missing_or_not_active")
        else: canary=ca[0]
    report=base_report("phase11e_limited_activation_rollback_execute",expected)
    report.update({"before_customer_status":None if limited is None else limited.status,"after_customer_status":None,"rollback_executed":False,"canary_preserved":False,"changed_customers":[],"event_audit_recorded":False})
    if not blockers:
        result=customer_mutation_service.rollback_phase11e_limited_customer(config,customer_key=SCOPE["candidate_customer_key"],lane=SCOPE["lane"],port=SCOPE["public_port"],operator=str(kwargs["operator"]),reason=str(kwargs["reason"]))
        if not result.ok: blockers.append(f"rollback_failed:{result.message}")
        else: report.update({"after_customer_status":"paused","rollback_executed":True,"mutation_performed":True,"db_mutation_performed":True,"canary_preserved":True,"changed_customers":[SCOPE["candidate_customer_key"]],"event_audit_recorded":True})
    report.update({"blockers":sorted(set(blockers)),"warnings":warnings,"final_decision":"PHASE11E_LIMITED_ACTIVATION_ROLLBACK_EXECUTED_PENDING_EVIDENCE" if report["rollback_executed"] else "BLOCKED"})
    return report
