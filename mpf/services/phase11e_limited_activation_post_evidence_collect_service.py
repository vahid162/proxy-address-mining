from __future__ import annotations
from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11e_limited_activation_common import CANARY_KEY,SCOPE,base_report,load_hashed_json,validate_artifact_gate,validate_confirmations,validate_current_phase_gate,validate_expected_version,validate_operator,validate_scope
CONFIRMATIONS=("operator_confirmed","i_understand_post_evidence_only","i_understand_no_db_mutation","i_understand_no_firewall_apply","i_understand_no_production_traffic_expansion","i_understand_no_miner_traffic_expansion","i_understand_no_abuse_automation")
def build_phase11e_limited_activation_post_evidence_collect_report(config:MPFConfig,**kwargs:object)->dict[str,object]:
 b:list[str]=[]; w:list[str]=[]; expected=validate_expected_version(kwargs,b);validate_operator(kwargs,b);validate_confirmations(kwargs,CONFIRMATIONS,b)
 ex=load_hashed_json(kwargs,"activation_execution_json","activation_execution_json_sha256",b); art=load_hashed_json(kwargs,"artifact_gate_json","artifact_gate_json_sha256",b)
 validate_scope(ex,b,"activation_execution");validate_artifact_gate(art,b);before=len(b);validate_current_phase_gate(b);gate_ok=len(b)==before
 if ex is not None and ex.get("final_decision")!="PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE":b.append("activation_execution_not_ready")
 src=None
 if kwargs.get("source_evidence_json") or kwargs.get("source_evidence_json_sha256"):
  src=load_hashed_json(kwargs,"source_evidence_json","source_evidence_json_sha256",b)
  if src is not None and src.get("changed_customers") not in (None,[SCOPE["candidate_customer_key"]]):b.append("unexpected_changed_customer")
 rows=customer_read_service.list_customer_status(config,include_deleted=False,limit=5000);limited=None;canary=False
 if not rows.ok:b.append("customer_state_read_failed")
 else:
  lm=[r for r in rows.customers if r.customer_key==SCOPE["candidate_customer_key"]];ca=[r for r in rows.customers if r.customer_key==CANARY_KEY]
  if len(lm)!=1:b.append("limited_customer_missing_or_ambiguous")
  else:
   limited=lm[0]
   if limited.status!="active":b.append("limited_customer_not_active")
   if limited.lane!=SCOPE["lane"] or limited.port!=SCOPE["public_port"]:b.append("limited_customer_scope_mismatch")
  canary=len(ca)==1 and ca[0].status=="active"
  if not canary:b.append("canary_missing_or_not_active")
 db_ok=None if src is None else src.get("db_ok");proxy_ok=None if src is None else src.get("proxy_ok")
 if src is None:w.append("source_evidence_not_provided_db_proxy_checks_unavailable")
 elif db_ok is not True or proxy_ok is not True:b.append("source_evidence_db_or_proxy_not_ok")
 r=base_report("phase11e_limited_activation_post_evidence_collect",expected);r.update({"limited_customer_status":None if limited is None else limited.status,"canary_preserved":canary,"artifact_gate_final_decision":None if art is None else art.get("final_decision"),"unknown_mpf_artifacts":None if art is None else art.get("unknown_mpf_artifacts"),"forbidden_public_runtime_exposure":None if art is None else art.get("forbidden_public_runtime_exposure"),"production_gates_remain_closed":None if art is None else art.get("production_gates_remain_closed"),"current_phase_gate_ok":gate_ok,"db_ok":db_ok,"proxy_ok":proxy_ok,"blockers":sorted(set(b)),"warnings":w,"next_required_step":"operator_review_phase11e_limited_activation_evidence" if not b else "fix_blockers_and_recollect","final_decision":"PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY" if not b else "BLOCKED"});return r
