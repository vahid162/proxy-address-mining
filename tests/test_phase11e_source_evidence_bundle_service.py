import hashlib, json
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11e_source_evidence_bundle_service as s
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
V={"expected_version":"0.1.218","repository_version":"0.1.218","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}

def call(tmp_path, **kw):
 p=tmp_path/'v.json'; p.write_text(json.dumps(V)); h=hashlib.sha256(p.read_bytes()).hexdigest()
 base=dict(expected_version='0.1.259',current_controlled_artifact_gate_sha256='abc',visibility_bundle_json=p,visibility_bundle_json_sha256=h,operator_confirmed=True,i_understand_read_only=True,i_understand_no_activation=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_restart=True,i_understand_no_abuse_automation=True)
 base.update(kw)
 return s.build_phase11e_source_evidence_bundle_report(cfg(), **base)

def full_sources():
 return dict(
  phase_status={'production_traffic':'none','firewall_apply_allowed':'no','abuse_automation_allowed':'no','customer_onboarding_allowed':'db_only','ui_allowed':'no','telegram_allowed':'no'},
  mpf_doctor={'status':'OK','ok':True},db_status={'status':'OK','ok':True},proxy_doctor={'status':'OK','ok':True},
  lanes=[{'name':'btc','enabled':True}],customers=[{'customer_key':'limited-btc-001','status':'paused','lane':'btc'}],
  current_controlled_artifact_gate={'repository_version':'0.1.259','current_phase_gate_ok':True,'unknown_mpf_artifacts':[],'forbidden_public_runtime_exposure':False,'production_gates_remain_closed':True,'final_decision':'PASS_NO_CUSTOMER_ARTIFACTS'},
  runtime_order_observations={'source_files':['a'],'source_hashes':{'a':'h'}},exposure_observations={'source_files':['b'],'source_hashes':{'b':'h'}},abuse_contract_observations={'source_files':['c'],'source_hashes':{'c':'h'}}
 )

def test_missing_mpf_doctor_blocks(tmp_path): assert 'missing_mpf_doctor_source' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='mpf_doctor'})['blockers']
def test_missing_db_status_blocks(tmp_path): assert 'missing_db_status_source' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='db_status'})['blockers']
def test_missing_proxy_doctor_blocks(tmp_path): assert 'missing_proxy_doctor_source' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='proxy_doctor'})['blockers']
def test_missing_lanes_blocks(tmp_path): assert 'missing_lane_source' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='lanes'})['blockers']
def test_missing_customers_blocks(tmp_path): assert 'missing_customer_source' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='customers'})['blockers']
def test_missing_artifact_gate_blocks(tmp_path): assert 'missing_current_controlled_artifact_gate_source' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='current_controlled_artifact_gate'})['blockers']
def test_missing_runtime_obs_blocks(tmp_path): assert 'missing_runtime_order_observations' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='runtime_order_observations'})['blockers']
def test_missing_exposure_obs_blocks(tmp_path): assert 'missing_exposure_observations' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='exposure_observations'})['blockers']
def test_missing_abuse_obs_blocks(tmp_path): assert 'missing_abuse_contract_observations' in call(tmp_path, **{k:v for k,v in full_sources().items() if k!='abuse_contract_observations'})['blockers']
def test_complete_source_bundle_ready(tmp_path): assert call(tmp_path, **full_sources())['final_decision']=='PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY'
