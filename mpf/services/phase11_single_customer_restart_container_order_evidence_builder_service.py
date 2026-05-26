from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

EXPECTED={"customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}
ALLOWED_SOURCE_VISIBILITY_REPOSITORY_VERSIONS={"0.1.218",__version__}


def _sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load(p:Path,m:str,i:str,b:list[str]):
    if not p.exists() or not p.is_file(): b.append(m); return None
    try:o=json.loads(p.read_text(encoding='utf-8'))
    except Exception: b.append(i); return None
    if not isinstance(o,dict): b.append(i); return None
    return o


def _source_ok(src: object) -> bool:
    if not isinstance(src, str):
        return False
    s = src.strip().lower()
    return bool(s) and s not in {"default", "synthetic", "placeholder", "none"}


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
        for f in ('production_traffic_enabled','miner_traffic_allowed','phase11_accepted','db_activation_allowed','mutation_performed'):
            if v.get(f) is not False: b.append('visibility_bundle_safety_boundary_open'); break

    ag_path = kwargs.get('artifact_gate_json')
    ag = None
    if ag_path is None:
        b.append('missing_artifact_gate_evidence')
    else:
        ap=Path(str(ag_path)); ag=_load(ap,'artifact_gate_missing','artifact_gate_invalid',b)
        asha=kwargs.get('artifact_gate_json_sha256')
        if ag is not None and asha is not None and _sha(ap)!=str(asha): b.append('artifact_gate_hash_mismatch')
        if ag is not None:
            if ag.get('final_decision') not in ('PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS','PASS_NO_CUSTOMER_ARTIFACTS'): b.append('artifact_gate_not_passed')
            if ag.get('unknown_mpf_artifacts')!=[]: b.append('artifact_gate_unknown_mpf_artifacts')
            if ag.get('production_gates_remain_closed') is not True: b.append('artifact_gate_safety_boundary_open')

    required = {
        'post_restart_or_controlled_order_test_performed': ('missing_post_restart_or_controlled_order_source', 'post_restart_or_controlled_order_source'),
        'required_containers_running': ('missing_required_containers_running_source', 'required_containers_running_source'),
        'v2raya_running_before_forwarder_check': ('missing_v2raya_order_source', 'v2raya_order_source'),
        'socks_bridge_ready_before_forwarder_check': ('missing_socks_bridge_order_source', 'socks_bridge_order_source'),
        'forwarder_ready': ('missing_forwarder_ready_source', 'forwarder_ready_source'),
        'bridge_ready': ('missing_bridge_ready_source', 'bridge_ready_source'),
        'proxy_doctor_ok': ('missing_proxy_doctor_source', 'proxy_doctor_source'),
        'mpf_doctor_ok': ('missing_mpf_doctor_source', 'mpf_doctor_source'),
        'db_status_ok': ('missing_db_status_source', 'db_status_source'),
        'phase_gate_ok': ('missing_phase_gate_source', 'phase_gate_source'),
        'backend_60010_local_or_internal_reachable': ('missing_backend_internal_reachability_source', 'backend_internal_reachability_source'),
    }

    values: dict[str, bool] = {}
    sources: dict[str, object] = {}
    for field, (missing_blocker, source_field) in required.items():
        sources[source_field] = kwargs.get(source_field)
        if not _source_ok(sources[source_field]):
            b.append(missing_blocker)
        val = kwargs.get(field)
        values[field] = (val is True)
        if val is not True:
            b.append(f'missing_or_false:{field}')

    exposure_source = kwargs.get('exposure_check_source')
    if not _source_ok(exposure_source): b.append('missing_exposure_check_source')

    public_ui=(kwargs.get('public_v2raya_ui_exposed') is True)
    public_backend=(kwargs.get('backend_60010_publicly_exposed') is True)
    if public_ui: b.append('public_v2raya_ui_exposed')
    if public_backend: b.append('backend_60010_publicly_exposed')

    ready=len(b)==0
    return {
        "component":"phase11_single_customer_restart_container_order_evidence",
        "expected_version":ev,
        "repository_version":__version__,
        "source_visibility_bundle_version":v.get('expected_version') if isinstance(v,dict) else None,
        "source_visibility_bundle_repository_version":v.get('repository_version') if isinstance(v,dict) else None,
        "candidate_customer_key":EXPECTED['customer_key'],"lane":EXPECTED['lane'],"public_port":EXPECTED['public_port'],"backend_target":EXPECTED['backend_target'],"visibility_bundle_sha256":vsha,
        **values,
        **sources,
        "exposure_check_source": exposure_source,
        "current_controlled_artifact_gate_passed": ag is not None and ag.get('final_decision') in ('PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS','PASS_NO_CUSTOMER_ARTIFACTS') and ag.get('unknown_mpf_artifacts')==[] and ag.get('production_gates_remain_closed') is True,
        "unknown_mpf_artifacts": [] if ag is None else ag.get('unknown_mpf_artifacts',[]),
        "public_v2raya_ui_exposed":public_ui,
        "backend_60010_publicly_exposed":public_backend,
        "limited_btc_001_status_changed_by_this_check":False,
        "production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,
        "blockers":sorted(set(b)),"warnings":sorted(set(w)),"final_decision":'PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_EVIDENCE_READY' if ready else 'BLOCKED'
    }
