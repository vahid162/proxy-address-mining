import json
import hashlib
from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_decision_service import build_phase11e_limited_activation_decision_report

cfg=lambda: MPFConfig.model_construct(database=MPFConfig.model_fields['database'].annotation.model_construct())

def w(p,d): p.write_text(json.dumps(d)); return p
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def base(tmp_path):
    vis=w(tmp_path/'v.json',{'final_decision':'PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY','candidate_customer_key':'limited-btc-001','candidate_lane':'btc','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010','production_traffic_enabled':False,'miner_traffic_allowed':False,'abuse_automation_enabled':False,'phase11_accepted':False,'db_activation_allowed':False,'mutation_performed':False})
    src=w(tmp_path/'s.json',{'final_decision':'PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY','candidate_customer_key':'limited-btc-001','candidate_lane':'btc','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010','production_traffic_enabled':False,'miner_traffic_allowed':False,'abuse_automation_enabled':False,'phase11_accepted':False,'db_activation_allowed':False,'mutation_performed':False})
    ab=w(tmp_path/'a.json',{'final_decision':'PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY','candidate_customer_key':'limited-btc-001'})
    rs=w(tmp_path/'r.json',{'final_decision':'PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY','candidate_lane':'btc'})
    pr=w(tmp_path/'p.json',{'final_decision':'PHASE11_SINGLE_CUSTOMER_LIMITED_ACCEPTANCE_PRECHECK_READY','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010'})
    ag=w(tmp_path/'g.json',{'final_decision':'PASS_NO_CUSTOMER_ARTIFACTS','unknown_mpf_artifacts':[],'production_gates_remain_closed':True})
    return dict(expected_version='0.1.225',visibility_bundle_json=vis,visibility_bundle_json_sha256=sha(vis),source_evidence_json=src,source_evidence_json_sha256=sha(src),abuse_readiness_json=ab,abuse_readiness_json_sha256=sha(ab),restart_readiness_json=rs,restart_readiness_json_sha256=sha(rs),limited_acceptance_precheck_json=pr,limited_acceptance_precheck_json_sha256=sha(pr),artifact_gate_json=ag,artifact_gate_json_sha256=sha(ag),operator='o',reason='r',operator_confirmed=True,i_understand_decision_only=True,i_understand_no_activation_performed=True,i_understand_no_db_mutation=True,i_understand_no_firewall_apply=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True,i_understand_no_abuse_automation=True,i_understand_phase11_not_accepted=True)

def call(tmp_path, **over):
    k=base(tmp_path);k.update(over);return build_phase11e_limited_activation_decision_report(cfg(),**k)

def test_ready_complete_fixture(tmp_path): assert call(tmp_path)['final_decision']=='PHASE11E_LIMITED_ACTIVATION_DECISION_READY'
def test_missing_abuse_hash_blocked(tmp_path): assert 'missing_abuse_readiness_hash' in call(tmp_path,abuse_readiness_json_sha256='')['blockers']
def test_missing_restart_hash_blocked(tmp_path): assert 'missing_restart_readiness_hash' in call(tmp_path,restart_readiness_json_sha256='')['blockers']
def test_missing_precheck_hash_blocked(tmp_path): assert 'missing_limited_acceptance_precheck_hash' in call(tmp_path,limited_acceptance_precheck_json_sha256='')['blockers']
def test_abuse_hash_mismatch_blocked(tmp_path): assert 'abuse_readiness_hash_mismatch' in call(tmp_path,abuse_readiness_json_sha256='bad')['blockers']
def test_restart_hash_mismatch_blocked(tmp_path): assert 'restart_readiness_hash_mismatch' in call(tmp_path,restart_readiness_json_sha256='bad')['blockers']
def test_precheck_hash_mismatch_blocked(tmp_path): assert 'limited_acceptance_precheck_hash_mismatch' in call(tmp_path,limited_acceptance_precheck_json_sha256='bad')['blockers']
def test_precheck_not_ready(tmp_path):
    p=tmp_path/'p2.json';w(p,{'final_decision':'BLOCKED'}); assert 'limited_acceptance_precheck_not_ready' in call(tmp_path,limited_acceptance_precheck_json=p,limited_acceptance_precheck_json_sha256=sha(p))['blockers']
def test_restart_not_ready(tmp_path): p=tmp_path/'r2.json';w(p,{'final_decision':'BLOCKED'}); assert 'restart_readiness_not_ready' in call(tmp_path,restart_readiness_json=p,restart_readiness_json_sha256=sha(p))['blockers']
def test_abuse_not_ready(tmp_path): p=tmp_path/'a2.json';w(p,{'final_decision':'BLOCKED'}); assert 'abuse_readiness_not_ready' in call(tmp_path,abuse_readiness_json=p,abuse_readiness_json_sha256=sha(p))['blockers']
def test_safety_flag_open_blocked(tmp_path): p=tmp_path/'a3.json';w(p,{'final_decision':'PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY','production_traffic_enabled':True}); assert any(x.startswith('safety_flag_open') for x in call(tmp_path,abuse_readiness_json=p,abuse_readiness_json_sha256=sha(p))['blockers'])
def test_scope_mismatch_blocked(tmp_path): p=tmp_path/'r3.json';w(p,{'final_decision':'PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY','candidate_lane':'ltc'}); assert any(x.startswith('scope_mismatch') for x in call(tmp_path,restart_readiness_json=p,restart_readiness_json_sha256=sha(p))['blockers'])
