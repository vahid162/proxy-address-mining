import json,hashlib
from pathlib import Path
from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_decision_service import build_phase11e_limited_activation_decision_report

def w(p,d): p.write_text(json.dumps(d)); return p
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cfg(): return MPFConfig.model_construct(database=MPFConfig.model_fields['database'].annotation.model_construct())
def base(tmp):
 vis=w(tmp/'v.json',{'final_decision':'PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY','candidate_customer_key':'limited-btc-001','candidate_lane':'btc','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010','production_traffic_enabled':False,'miner_traffic_allowed':False,'abuse_automation_enabled':False,'phase11_accepted':False,'db_activation_allowed':False,'mutation_performed':False})
 src=w(tmp/'s.json',{'final_decision':'PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY','candidate_customer_key':'limited-btc-001','candidate_lane':'btc','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010'})
 ab=w(tmp/'a.json',{'final_decision':'PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY'})
 rs=w(tmp/'r.json',{'final_decision':'PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY'})
 pr=w(tmp/'p.json',{'final_decision':'PHASE11_SINGLE_CUSTOMER_LIMITED_ACCEPTANCE_PRECHECK_READY'})
 ag=w(tmp/'g.json',{'final_decision':'PASS_NO_CUSTOMER_ARTIFACTS','unknown_mpf_artifacts':[],'production_gates_remain_closed':True})
 return dict(expected_version='0.1.224',visibility_bundle_json=vis,visibility_bundle_json_sha256=sha(vis),source_evidence_json=src,source_evidence_json_sha256=sha(src),abuse_readiness_json=ab,restart_readiness_json=rs,limited_acceptance_precheck_json=pr,artifact_gate_json=ag,artifact_gate_json_sha256=sha(ag),operator='o',reason='r',operator_confirmed=True,i_understand_decision_only=True,i_understand_no_activation_performed=True,i_understand_no_db_mutation=True,i_understand_no_firewall_apply=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True,i_understand_no_abuse_automation=True,i_understand_phase11_not_accepted=True)

def test_ready(tmp_path): assert build_phase11e_limited_activation_decision_report(cfg(), **base(tmp_path))['final_decision']=='PHASE11E_LIMITED_ACTIVATION_DECISION_READY'
def test_block_missing_confirm(tmp_path): k=base(tmp_path);k['operator_confirmed']=False; assert build_phase11e_limited_activation_decision_report(cfg(), **k)['final_decision']=='BLOCKED'
