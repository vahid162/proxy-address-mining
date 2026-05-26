from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig

EXP={"customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def _load(p:Path,b:list[str],m:str,i:str):
    if not p.exists() or not p.is_file(): b.append(m); return None
    try:o=json.loads(p.read_text(encoding='utf-8'))
    except Exception: b.append(i); return None
    return o if isinstance(o,dict) else (b.append(i) or None)

def build_phase11e_limited_activation_decision_report(config: MPFConfig, **k: object)->dict[str,object]:
    del config; b=[]; w=[]
    for c in ["operator_confirmed","i_understand_decision_only","i_understand_no_activation_performed","i_understand_no_db_mutation","i_understand_no_firewall_apply","i_understand_no_production_traffic","i_understand_no_miner_traffic","i_understand_no_abuse_automation","i_understand_phase11_not_accepted"]:
        if k.get(c) is not True: b.append(f"missing_confirmation:{c}")
    def L(name,sha_name):
        p=Path(str(k.get(name,''))); o=_load(p,b,f"{name}_missing",f"{name}_invalid")
        exp=str(k.get(sha_name,''))
        if o is not None and exp and _sha(p)!=exp: b.append(f"{name}_hash_mismatch")
        return o
    vis=L('visibility_bundle_json','visibility_bundle_json_sha256'); src=L('source_evidence_json','source_evidence_json_sha256')
    abuse=L('abuse_readiness_json','abuse_readiness_json_sha256') if k.get('abuse_readiness_json_sha256') else L('abuse_readiness_json','abuse_readiness_json_sha256')
    rst=L('restart_readiness_json','restart_readiness_json_sha256') if k.get('restart_readiness_json_sha256') else L('restart_readiness_json','restart_readiness_json_sha256')
    pre=L('limited_acceptance_precheck_json','limited_acceptance_precheck_json_sha256') if k.get('limited_acceptance_precheck_json_sha256') else L('limited_acceptance_precheck_json','limited_acceptance_precheck_json_sha256')
    art=L('artifact_gate_json','artifact_gate_json_sha256')
    for o,n,f in [(vis,'PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY','visibility_bundle_not_ready'),(src,'PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY','source_evidence_not_ready'),(abuse,'PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY','abuse_readiness_not_ready'),(rst,'PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY','restart_readiness_not_ready'),(pre,'PHASE11_SINGLE_CUSTOMER_LIMITED_ACCEPTANCE_PRECHECK_READY','limited_acceptance_precheck_not_ready')]:
        if o is not None and o.get('final_decision')!=n: b.append(f)
    for o in [vis,src]:
        if isinstance(o,dict):
            if o.get('candidate_customer_key',o.get('customer_key'))!=EXP['customer_key'] or o.get('candidate_lane',o.get('lane'))!=EXP['lane'] or int(o.get('candidate_public_port',o.get('public_port',20101)))!=EXP['public_port'] or o.get('candidate_backend_target',o.get('backend_target'))!=EXP['backend_target']: b.append('scope_mismatch')
            for f in ["production_traffic_enabled","miner_traffic_allowed","abuse_automation_enabled","phase11_accepted","db_activation_allowed","mutation_performed"]:
                if f in o and o.get(f) is not False: b.append('safety_flag_open')
    if art is not None:
        if art.get('final_decision') not in {"PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS","PASS_NO_CUSTOMER_ARTIFACTS"}: b.append('artifact_gate_not_passed')
        if art.get('unknown_mpf_artifacts')!=[]: b.append('unknown_mpf_artifacts')
        if art.get('production_gates_remain_closed') is not True: b.append('production_gates_not_closed')
    ready=not b
    return {"component":"phase11e_limited_activation_decision","expected_version":str(k.get('expected_version',__version__)),"repository_version":__version__,"candidate_customer_key":EXP['customer_key'],"lane":EXP['lane'],"public_port":EXP['public_port'],"backend_target":EXP['backend_target'],"visibility_bundle_sha256":k.get('visibility_bundle_json_sha256'),"source_evidence_sha256":k.get('source_evidence_json_sha256'),"artifact_gate_sha256":k.get('artifact_gate_json_sha256'),"abuse_readiness_final_decision":None if abuse is None else abuse.get('final_decision'),"restart_readiness_final_decision":None if rst is None else rst.get('final_decision'),"limited_acceptance_precheck_final_decision":None if pre is None else pre.get('final_decision'),"all_readiness_inputs_ready":ready,"controlled_activation_decision_ready":ready,"activation_performed":False,"db_mutation_performed":False,"firewall_apply_performed":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"blockers":sorted(set(b)),"warnings":w,"next_required_step":"phase11e_limited_activation_execution_package_review" if ready else "fix_blockers_and_regenerate","final_decision":"PHASE11E_LIMITED_ACTIVATION_DECISION_READY" if ready else "BLOCKED"}
