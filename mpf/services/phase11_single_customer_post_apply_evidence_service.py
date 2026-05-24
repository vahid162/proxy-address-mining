from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_firewall_apply_gate_service import _read_live_snapshot

REQ_EXEC_SHA="bd8f3900db3d3fb2647ead8cec47c870f4cd00ebaf52b68bc329a065a65b880b"
REQ_PRE_SHA="3a493643f796f10f37443152e99adda928f30c82067fc98a4a748f52d2767494"
REQ_POST_SHA="c6330a80954f7268ccec311750751b45464c84c2efd627509d1ecee274eec27b"
REQ_APPLY_SHA="500978bf2b156a5da6a1b299e41d346cadf2b20b15280212c607c51c9a307b1a"
REQ_PLAN_SHA="0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438"

def _sha(p: Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()

def _parse(s:str)->dict[str,object]:
    ls=s.splitlines()
    d201=[l for l in ls if 'MPF_NAT_PRE' in l and '--dport 20101' in l and '-j DNAT' in l]
    return {
      'has_canary_20001': ':MPFC_20001' in s and any('--dport 20001' in l and 'canary-btc-001' in l for l in ls),
      'has_20101_chain': ':MPFC_20101' in s,
      'has_20101_ref': 'limited-btc-001' in s,
      'dnat_20101_exact': len([l for l in d201 if '--to-destination 172.18.0.3:60010' in l and 'limited-btc-001' in l]),
      'dnat_20101_loop': len([l for l in d201 if '--to-destination 127.0.0.1:' in l]),
      'unrelated_nat': len([l for l in ls if '-A MPF_NAT_PRE' in l and 'mpf:' in l and 'limited-btc-001' not in l and 'canary-btc-001' not in l]),
    }

def build_phase11_single_customer_post_apply_evidence_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    b=[]
    ev=str(kwargs.get('expected_version','0.1.205'))
    out={"component":"phase11_single_customer_post_apply_evidence","expected_version":ev,"repository_version":__version__,"candidate_customer_key":str(kwargs.get('candidate_customer_key','limited-btc-001')),"candidate_lane":str(kwargs.get('candidate_lane','btc')),"candidate_public_port":int(kwargs.get('candidate_public_port',20101)),"candidate_backend_target":str(kwargs.get('candidate_backend_target','172.18.0.3:60010')),"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"additional_firewall_apply_allowed":False,"db_activation_allowed":False,"mutation_performed":False}
    for f,blk in {"operator_confirmed":"operator_not_confirmed","i_understand_post_apply_evidence_only":"post_apply_evidence_only_not_confirmed","i_understand_no_additional_firewall_apply":"no_additional_firewall_apply_not_confirmed","i_understand_no_production_traffic_acceptance":"no_production_traffic_not_confirmed","i_understand_no_miner_traffic_acceptance":"no_miner_traffic_not_confirmed","i_confirm_runtime_path_evidence_required_next":"runtime_path_required_not_confirmed","i_confirm_stratum_transcript_required_next":"stratum_transcript_required_not_confirmed","i_confirm_visibility_bundle_required_next":"visibility_bundle_required_not_confirmed","i_confirm_abuse_1h_required_before_customer_traffic":"abuse_1h_required_not_confirmed","i_confirm_restart_container_order_required_before_limited_acceptance":"restart_container_order_required_not_confirmed"}.items():
        if kwargs.get(f) is not True: b.append(blk)
    ej=Path(str(kwargs.get('execution_json','')))
    if not ej.exists(): b.append('execution_json_missing'); data={}
    else:
        try:data=json.loads(ej.read_text())
        except Exception:data={}; b.append('execution_json_invalid')
        if _sha(ej)!=str(kwargs.get('execution_json_sha256',REQ_EXEC_SHA)): b.append('execution_json_hash_mismatch')
    for f,v in {"final_decision":"PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTED_PENDING_REVIEW","execute_requested":True,"apply_execution_ready":True,"firewall_apply_execution_allowed":True,"iptables_restore_authorized":True,"mutation_performed":True,"firewall_mutation_performed":True,"nat_mutation_performed":True,"next_required_step":"phase11e_post_apply_runtime_evidence_pr","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False}.items():
        if data and data.get(f)!=v: b.append('execution_json_not_success')
    if data and (data.get('candidate_customer_key')!='limited-btc-001' or data.get('candidate_lane')!='btc' or data.get('candidate_public_port')!=20101 or data.get('candidate_backend_target')!='172.18.0.3:60010'): b.append('execution_json_scope_mismatch')
    if data and (data.get('blockers')!=[] or data.get('warnings')!=[]): b.append('execution_json_safety_boundary_open')
    pav=data.get('post_apply_verification') if isinstance(data,dict) else None
    if not isinstance(pav,dict): b.append('execution_json_post_apply_verification_missing')
    else:
        exp={"mpf_nat_pre_exists":True,"mpfc_20001_exists":True,"mpfc_20101_exists":True,"canary_20001_exact_artifact_preserved":True,"dnat_20101_exact_target_count":1,"dnat_20101_loopback_count":0,"unrelated_customer_nat_rule_count":0,"limited_20101_connlimit_reject_rule_count":1,"limited_20101_hashlimit_reject_rule_count":1,"limited_20101_filter_primitives_verified":True}
        if any(pav.get(k)!=v for k,v in exp.items()): b.append('execution_json_post_apply_verification_failed')
    pre=Path(str(kwargs.get('pre_apply_snapshot_file',''))); post=Path(str(kwargs.get('post_apply_snapshot_file','')))
    if not pre.exists(): b.append('pre_apply_snapshot_missing')
    elif _sha(pre)!=str(kwargs.get('pre_apply_snapshot_sha256',REQ_PRE_SHA)): b.append('pre_apply_snapshot_hash_mismatch')
    if not post.exists(): b.append('post_apply_snapshot_missing')
    elif _sha(post)!=str(kwargs.get('post_apply_snapshot_sha256',REQ_POST_SHA)): b.append('post_apply_snapshot_hash_mismatch')
    ag=Path(str(kwargs.get('apply_gate_json',''))); pg=Path(str(kwargs.get('plan_gate_json','')))
    if (not ag.exists()) or _sha(ag)!=str(kwargs.get('apply_gate_json_sha256',REQ_APPLY_SHA)): b.append('execution_json_safety_boundary_open')
    if (not pg.exists()) or _sha(pg)!=str(kwargs.get('plan_gate_json_sha256',REQ_PLAN_SHA)): b.append('execution_json_safety_boundary_open')
    if pre.exists() and post.exists():
        p1,p2=_parse(pre.read_text()),_parse(post.read_text())
        if p1['has_20101_ref'] or p1['dnat_20101_exact']>0: b.append('pre_apply_snapshot_unexpected_20101_present')
        if not p2['has_20101_chain'] or p2['dnat_20101_exact']<1: b.append('post_apply_snapshot_missing_20101')
        if not p2['has_canary_20001']: b.append('post_apply_snapshot_missing_canary_20001')
        if p2['dnat_20101_exact']>1: b.append('post_apply_snapshot_duplicate_20101')
        if p2['dnat_20101_loop']>0: b.append('post_apply_snapshot_loopback_20101')
        if p2['unrelated_nat']>0: b.append('post_apply_snapshot_unrelated_customer_nat')
    try: rows=customer_read_service.list_customer_status(config,include_deleted=False,limit=5000)
    except Exception: rows=customer_read_service.CustomerList(ok=False,message='x',customers=[])
    if not rows.ok: b.append('db_read_failed')
    else:
        st=[r for r in rows.customers if r.customer_key=='limited-btc-001']
        if len(st)==0:b.append('staged_customer_missing')
        elif len(st)>1:b.append('staged_customer_duplicate')
        else:
            s=st[0]
            if s.lane!='btc' or s.port!=20101:b.append('staged_customer_scope_mismatch')
            if str(s.status).lower()!='paused': b.append('staged_customer_not_paused')
        if [r for r in rows.customers if r.customer_key!='limited-btc-001' and r.port==20101]: b.append('candidate_port_collision')
    livef=kwargs.get('live_snapshot_file'); collect=bool(kwargs.get('collect_live',False))
    if livef or collect:
        try:
            live=_read_live_snapshot(Path(str(livef)) if livef else None,collect,kwargs.get('live_snapshot_reader'))
            if _parse(live)!=_parse(post.read_text() if post.exists() else ''): b.append('post_apply_snapshot_missing_20101')
        except Exception: b.append('live_firewall_read_failed')
    if b:
        return {**out,"post_apply_evidence_ready":False,"controlled_apply_recorded":False,"runtime_path_evidence_ready":False,"stratum_transcript_ready":False,"visibility_bundle_ready":False,"abuse_1h_coverage_ready":False,"restart_container_order_ready":False,"blockers":sorted(set(b)),"warnings":[],"next_required_step":"none","final_decision":"BLOCKED"}
    return {**out,"post_apply_evidence_ready":True,"controlled_apply_recorded":True,"runtime_path_evidence_ready":False,"stratum_transcript_ready":False,"visibility_bundle_ready":False,"abuse_1h_coverage_ready":False,"restart_container_order_ready":False,"blockers":[],"warnings":[],"next_required_step":"phase11e_single_customer_runtime_path_evidence_pr","final_decision":"PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY"}
