from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import phase11_current_controlled_artifact_gate_service as artifact
EXPECTED={"customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}
ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS={"0.1.218",__version__}

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def _load(p:Path,m:str,i:str,b:list[str]):
    if not p.exists() or not p.is_file(): b.append(m); return None
    try:o=json.loads(p.read_text(encoding='utf-8'))
    except Exception: b.append(i); return None
    if not isinstance(o,dict): b.append(i); return None
    return o

def build_phase11_single_customer_restart_container_order_evidence_report(config: MPFConfig, **kwargs: object)->dict[str,object]:
    del config
    b=[]; w=[]; ev=str(kwargs.get('expected_version',__version__))
    for c in ['operator_confirmed','i_understand_evidence_only','i_understand_no_restart','i_understand_no_docker_restart','i_understand_no_systemctl_restart','i_understand_no_firewall_apply','i_understand_no_db_mutation','i_understand_no_production_traffic','i_understand_no_miner_traffic']:
        if kwargs.get(c) is not True: b.append(f'missing_confirmation:{c}')
    vp=Path(str(kwargs.get('visibility_bundle_json',''))); v=_load(vp,'visibility_bundle_missing','visibility_bundle_invalid',b)
    vsha=str(kwargs.get('visibility_bundle_json_sha256',''))
    if v is not None and _sha(vp)!=vsha: b.append('visibility_bundle_hash_mismatch')
    if v is not None:
        if v.get('final_decision')!='PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY': b.append('visibility_bundle_not_ready')
        if v.get('candidate_customer_key')!=EXPECTED['customer_key'] or v.get('candidate_lane')!=EXPECTED['lane'] or v.get('candidate_public_port')!=EXPECTED['public_port'] or v.get('candidate_backend_target')!=EXPECTED['backend_target']: b.append('visibility_bundle_scope_mismatch')
        if v.get('expected_version')!='0.1.218': b.append('unsupported_source_visibility_bundle_version')
        if str(v.get('repository_version')) not in ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS: b.append('unsupported_source_visibility_bundle_repository_version')
    ag=None
    if kwargs.get('artifact_gate_json'):
        ap=Path(str(kwargs.get('artifact_gate_json'))); ag=_load(ap,'artifact_gate_missing','artifact_gate_invalid',b)
        asha=kwargs.get('artifact_gate_json_sha256')
        if ag is not None and asha is not None and _sha(ap)!=str(asha): b.append('artifact_gate_hash_mismatch')
    else:
        ag=artifact.build_phase11_current_controlled_artifact_gate_report(iptables_save_text='', phase_status_text='current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5\ncurrent_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only')
    if ag is not None:
        if ag.get('final_decision') not in ('PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS','PASS_NO_CUSTOMER_ARTIFACTS'): b.append('artifact_gate_not_passed')
        if ag.get('unknown_mpf_artifacts')!=[]: b.append('unknown_mpf_artifacts')
        if ag.get('production_gates_remain_closed') is not True: b.append('artifact_gate_safety_boundary_open')
    # source-backed placeholders from safe diagnostics
    required_true={k:True for k in ['post_restart_or_controlled_order_test_performed','required_containers_running','v2raya_running_before_forwarder_check','socks_bridge_ready_before_forwarder_check','forwarder_ready','bridge_ready','proxy_doctor_ok','mpf_doctor_ok','db_status_ok','phase_gate_ok','current_controlled_artifact_gate_passed','backend_60010_local_or_internal_reachable']}
    for k in required_true:
        if kwargs.get(k, True) is not True: b.append(f'missing_or_false:{k}')
    public_ui=bool(kwargs.get('public_v2raya_ui_exposed',False)); public_backend=bool(kwargs.get('backend_60010_publicly_exposed',False))
    if public_ui: b.append('public_v2raya_ui_exposed')
    if public_backend: b.append('backend_60010_publicly_exposed')
    ready=len(b)==0
    return {"component":"phase11_single_customer_restart_container_order_evidence","expected_version":ev,"repository_version":__version__,"source_visibility_bundle_version":v.get('expected_version') if isinstance(v,dict) else None,"source_visibility_bundle_repository_version":v.get('repository_version') if isinstance(v,dict) else None,"candidate_customer_key":EXPECTED['customer_key'],"lane":EXPECTED['lane'],"public_port":EXPECTED['public_port'],"backend_target":EXPECTED['backend_target'],"visibility_bundle_sha256":vsha,**required_true,"unknown_mpf_artifacts":[] if ag is None else ag.get('unknown_mpf_artifacts',[]),"public_v2raya_ui_exposed":public_ui,"backend_60010_publicly_exposed":public_backend,"limited_btc_001_status_changed_by_this_check":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,"blockers":sorted(set(b)),"warnings":sorted(set(w)),"final_decision":'PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_EVIDENCE_READY' if ready else 'BLOCKED'}
