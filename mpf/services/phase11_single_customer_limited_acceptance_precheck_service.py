from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig
KEYS=['expected_version','repository_version','candidate_customer_key','candidate_lane','candidate_public_port','candidate_backend_target','visibility_bundle_sha256']
SAFE_FLAGS=['production_traffic_enabled','miner_traffic_allowed','abuse_automation_enabled','phase11_accepted','db_activation_allowed','mutation_performed']

def _sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def _load(p:Path,b:list[str],m:str,i:str):
    if not p.exists() or not p.is_file(): b.append(m); return None
    try:o=json.loads(p.read_text())
    except Exception: b.append(i); return None
    if not isinstance(o,dict): b.append(i); return None
    return o

def build_phase11_single_customer_limited_acceptance_precheck_report(config: MPFConfig, **kwargs: object)->dict[str,object]:
    del config; b=[]
    ev=str(kwargs.get('expected_version',__version__))
    for c in ['operator_confirmed','i_understand_precheck_only','i_understand_no_customer_activation','i_understand_no_production_traffic_acceptance','i_understand_no_miner_traffic_acceptance','i_understand_no_db_activation']:
        if kwargs.get(c) is not True: b.append(f'missing_confirmation:{c}')
    vp=Path(str(kwargs.get('visibility_bundle_json',''))); ap=Path(str(kwargs.get('abuse_1h_readiness_json',''))); rp=Path(str(kwargs.get('restart_container_order_readiness_json','')))
    v=_load(vp,b,'visibility_bundle_missing','visibility_bundle_invalid'); a=_load(ap,b,'abuse_readiness_missing','abuse_readiness_invalid'); r=_load(rp,b,'restart_readiness_missing','restart_readiness_invalid')
    for obj,p,n,tag in [(v,vp,kwargs.get('visibility_bundle_json_sha256'),'visibility'),(a,ap,kwargs.get('abuse_1h_readiness_json_sha256'),'abuse'),(r,rp,kwargs.get('restart_container_order_readiness_json_sha256'),'restart')]:
        if obj is not None and n is not None and _sha(p)!=str(n): b.append(f'{tag}_sha256_mismatch')
    if any(x is None for x in (v,a,r)): b.append('required_input_missing_or_invalid')
    if v is not None and (v.get('final_decision')!='PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY' or v.get('visibility_bundle_ready') is not True): b.append('visibility_bundle_not_ready')
    if a is not None:
        if a.get('abuse_1h_coverage_ready') is not True: b.append('abuse_1h_not_ready')
        for f in SAFE_FLAGS:
            if a.get(f) is not False: b.append('abuse_readiness_safety_boundary_open'); break
    if r is not None:
        if r.get('restart_container_order_ready') is not True: b.append('restart_container_order_not_ready')
        for f in SAFE_FLAGS:
            if r.get(f) is not False: b.append('restart_readiness_safety_boundary_open'); break
    if all(isinstance(x,dict) for x in (v,a,r)):
        for k in KEYS:
            vals={v.get(k),a.get(k),r.get(k)}
            if len(vals)!=1: b.append(f'mismatch:{k}')
    ready=len(b)==0
    return {"component":"phase11_single_customer_limited_acceptance_precheck","expected_version":ev,"repository_version":__version__,"candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","visibility_bundle_ready":bool(v and v.get('visibility_bundle_ready') is True),"abuse_1h_coverage_ready":bool(a and a.get('abuse_1h_coverage_ready') is True),"restart_container_order_ready":bool(r and r.get('restart_container_order_ready') is True),"limited_acceptance_precheck_ready":ready,"production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,"blockers":sorted(set(b)),"warnings":[],"next_required_step":('explicit_limited_customer_activation_decision_pr' if ready else 'resolve_missing_phase11e_readiness_gates'),"final_decision":('PHASE11_SINGLE_CUSTOMER_LIMITED_ACCEPTANCE_PRECHECK_READY' if ready else 'BLOCKED')}
