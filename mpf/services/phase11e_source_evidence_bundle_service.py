from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import phase11_current_controlled_artifact_gate_service as ags
EXPECTED={"customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def _load(p:Path,b:list[str],m:str,i:str):
    if not p.exists() or not p.is_file(): b.append(m); return None
    try:o=json.loads(p.read_text(encoding='utf-8'))
    except Exception: b.append(i); return None
    if not isinstance(o,dict): b.append(i); return None
    return o

def build_phase11e_source_evidence_bundle_report(config: MPFConfig, **kwargs: object)->dict[str,object]:
    del config
    b=[]; w=[]; ev=str(kwargs.get('expected_version',__version__))
    for c in ['operator_confirmed','i_understand_read_only','i_understand_no_activation','i_understand_no_firewall_apply','i_understand_no_db_mutation','i_understand_no_restart','i_understand_no_abuse_automation']:
        if kwargs.get(c) is not True: b.append(f'missing_confirmation:{c}')
    vp=Path(str(kwargs.get('visibility_bundle_json',''))); v=_load(vp,b,'visibility_bundle_missing','visibility_bundle_invalid')
    vsha=str(kwargs.get('visibility_bundle_json_sha256',''))
    if v is not None and _sha(vp)!=vsha: b.append('visibility_bundle_hash_mismatch')
    phase=kwargs.get('phase_status') if isinstance(kwargs.get('phase_status'),dict) else {}
    mpf_doctor=kwargs.get('mpf_doctor') if isinstance(kwargs.get('mpf_doctor'),dict) else {}
    db_status=kwargs.get('db_status') if isinstance(kwargs.get('db_status'),dict) else {}
    proxy_doctor=kwargs.get('proxy_doctor') if isinstance(kwargs.get('proxy_doctor'),dict) else {}
    lanes=kwargs.get('lanes') if isinstance(kwargs.get('lanes'),list) else []
    customers=kwargs.get('customers') if isinstance(kwargs.get('customers'),list) else []
    artifact=kwargs.get('current_controlled_artifact_gate') if isinstance(kwargs.get('current_controlled_artifact_gate'),dict) else {}
    if v is not None:
        if v.get('expected_version')!='0.1.218': b.append('unsupported_source_visibility_bundle_version')
        if v.get('candidate_customer_key')!=EXPECTED['customer_key'] or v.get('candidate_lane')!=EXPECTED['lane'] or v.get('candidate_public_port')!=EXPECTED['public_port'] or v.get('candidate_backend_target')!=EXPECTED['backend_target']: b.append('visibility_bundle_scope_mismatch')
        for f in ('production_traffic_enabled','miner_traffic_allowed','phase11_accepted','db_activation_allowed','mutation_performed'):
            if v.get(f) is not False: b.append('visibility_bundle_safety_boundary_open'); break
    if phase.get('production_traffic') not in ('none',None): b.append('production_gate_open')
    if artifact.get('unknown_mpf_artifacts',[])!=[]: b.append('unknown_mpf_artifacts')
    if artifact and artifact.get('production_gates_remain_closed') is not True: b.append('artifact_gate_production_gates_open')
    active=[c.get('customer_key') for c in customers if isinstance(c,dict) and c.get('status')=='active' and c.get('lane') in [l.get('name') for l in lanes if isinstance(l,dict) and l.get('enabled')]]
    paused=[c.get('customer_key') for c in customers if isinstance(c,dict) and c.get('status')=='paused']
    disabled=[l.get('name') for l in lanes if isinstance(l,dict) and not l.get('enabled')]
    ready=len(b)==0
    return {'component':'phase11e_source_evidence_bundle','expected_version':ev,'repository_version':__version__,'source_visibility_bundle_version':None if v is None else v.get('expected_version'),'source_visibility_bundle_repository_version':None if v is None else v.get('repository_version'),'candidate_customer_key':EXPECTED['customer_key'],'candidate_lane':EXPECTED['lane'],'candidate_public_port':EXPECTED['public_port'],'candidate_backend_target':EXPECTED['backend_target'],'visibility_bundle_sha256':vsha,'phase_status':phase,'mpf_doctor':mpf_doctor,'db_status':db_status,'proxy_doctor':proxy_doctor,'lanes':lanes,'customers':customers,'active_enabled_lane_customers':active,'paused_candidate_customers':paused,'disabled_lanes':disabled,'current_controlled_artifact_gate':artifact,'current_controlled_artifact_gate_sha256':kwargs.get('current_controlled_artifact_gate_sha256'),'runtime_order_observations':kwargs.get('runtime_order_observations',{}),'exposure_observations':kwargs.get('exposure_observations',{}),'abuse_contract_observations':kwargs.get('abuse_contract_observations',{}),'source_files':kwargs.get('source_files',[]),'source_hashes':kwargs.get('source_hashes',{}),'production_traffic_enabled':False,'miner_traffic_allowed':False,'abuse_automation_enabled':False,'phase11_accepted':False,'db_activation_allowed':False,'mutation_performed':False,'blockers':sorted(set(b)),'warnings':sorted(set(w)),'final_decision':'PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY' if ready else 'BLOCKED'}
