from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig
EXPECTED={"customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}
ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS={"0.1.218",__version__}

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def _load(p:Path,m:str,i:str,b:list[str]):
    if not p.exists() or not p.is_file(): b.append(m); return None
    try:o=json.loads(p.read_text(encoding='utf-8'))
    except Exception: b.append(i); return None
    if not isinstance(o,dict): b.append(i); return None
    return o

def build_phase11_single_customer_restart_container_order_readiness_report(config: MPFConfig, **kwargs: object)->dict[str,object]:
    del config; b=[]
    ev=str(kwargs.get('expected_version',__version__))
    for c in ['operator_confirmed','i_understand_restart_readiness_only','i_understand_no_restart_performed_by_classifier','i_understand_no_production_traffic_acceptance','i_understand_no_miner_traffic_acceptance','i_understand_no_db_activation']:
        if kwargs.get(c) is not True: b.append(f'missing_confirmation:{c}')
    vp=Path(str(kwargs.get('visibility_bundle_json',''))); v=_load(vp,'visibility_bundle_missing','visibility_bundle_invalid',b)
    vsha=kwargs.get('visibility_bundle_json_sha256')
    if v is not None and vsha is not None and _sha(vp)!=str(vsha): b.append('visibility_bundle_hash_mismatch')
    src_ver=v.get('expected_version') if isinstance(v,dict) else None
    src_repo=v.get('repository_version') if isinstance(v,dict) else None
    if v is not None:
        if v.get('final_decision')!='PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY' or v.get('visibility_bundle_ready') is not True: b.append('visibility_bundle_not_ready')
        for k,val in [('candidate_customer_key',EXPECTED['customer_key']),('candidate_lane',EXPECTED['lane']),('candidate_public_port',EXPECTED['public_port']),('candidate_backend_target',EXPECTED['backend_target'])]:
            if v.get(k)!=val: b.append('visibility_bundle_scope_mismatch')
        for f in ('production_traffic_enabled','miner_traffic_allowed','phase11_accepted','db_activation_allowed','mutation_performed'):
            if v.get(f) is not False: b.append('visibility_bundle_safety_boundary_open'); break
        if v.get('expected_version')!='0.1.218': b.append('unsupported_source_visibility_bundle_version')
        if str(v.get('repository_version')) not in ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS: b.append('unsupported_source_visibility_bundle_repository_version')

    ag_path=kwargs.get('artifact_gate_json'); ag=None
    if ag_path is not None:
        agp=Path(str(ag_path)); ag=_load(agp,'artifact_gate_missing','artifact_gate_invalid',b)
        agsha=kwargs.get('artifact_gate_json_sha256')
        if ag is not None and agsha is not None and _sha(agp)!=str(agsha): b.append('artifact_gate_hash_mismatch')
        if ag is not None:
            if ag.get('final_decision') not in ('PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS','PASS_NO_CUSTOMER_ARTIFACTS'): b.append('artifact_gate_not_passed')
            if ag.get('unknown_mpf_artifacts')!=[]: b.append('artifact_gate_unknown_mpf_artifacts')
            if ag.get('production_gates_remain_closed') is not True: b.append('artifact_gate_safety_boundary_open')

    rp=kwargs.get('restart_evidence_json'); r=None
    if rp is None: b.append('missing_restart_container_order_evidence')
    else:
        rp=Path(str(rp)); r=_load(rp,'restart_evidence_missing','restart_evidence_invalid',b)
        rsha=kwargs.get('restart_evidence_json_sha256')
        if r is not None and rsha is not None and _sha(rp)!=str(rsha): b.append('restart_evidence_hash_mismatch')
    if r is not None:
        for k,val in [('candidate_customer_key',EXPECTED['customer_key']),('lane',EXPECTED['lane']),('public_port',EXPECTED['public_port']),('visibility_bundle_sha256',str(vsha))]:
            if r.get(k)!=val: b.append('restart_evidence_scope_mismatch')
        trues=['post_restart_or_controlled_order_test_performed','required_containers_running','v2raya_running_before_forwarder_check','socks_bridge_ready_before_forwarder_check','forwarder_ready','bridge_ready','proxy_doctor_ok','mpf_doctor_ok','db_status_ok','phase_gate_ok','current_controlled_artifact_gate_passed','backend_60010_local_or_internal_reachable']
        for k in trues:
            if r.get(k) is not True: b.append(f'restart_contract_failed:{k}')
        if r.get('unknown_mpf_artifacts')!=[]: b.append('restart_contract_failed:unknown_mpf_artifacts')
        for k in ['public_v2raya_ui_exposed','backend_60010_publicly_exposed','limited_btc_001_status_changed_by_this_check','production_traffic_enabled','miner_traffic_allowed','abuse_automation_enabled','mutation_performed']:
            if r.get(k) is not False: b.append(f'restart_contract_failed:{k}')
    ready=len(b)==0
    return {"component":"phase11_single_customer_restart_container_order_readiness","expected_version":ev,"source_visibility_bundle_version":src_ver,"source_visibility_bundle_repository_version":src_repo,"repository_version":__version__,"candidate_customer_key":EXPECTED['customer_key'],"candidate_lane":EXPECTED['lane'],"candidate_public_port":EXPECTED['public_port'],"candidate_backend_target":EXPECTED['backend_target'],"visibility_bundle_link":v.get('final_decision') if isinstance(v,dict) else None,"visibility_bundle_sha256":vsha,"restart_evidence_link":r.get('final_decision') if isinstance(r,dict) else None,"restart_container_order_ready":ready,"container_order_contract_ready":ready,"post_restart_proxy_doctor_ready":ready,"post_restart_artifact_gate_ready":ready,"local_only_runtime_ready":ready,"backend_public_exposure_blocked":ready,"backend_internal_reachability_ready":ready,"production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,"blockers":sorted(set(b)),"warnings":[],"next_required_step":('phase11e_limited_acceptance_precheck' if ready else 'collect_phase11e_restart_container_order_evidence'),"final_decision":('PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY' if ready else 'BLOCKED')}
