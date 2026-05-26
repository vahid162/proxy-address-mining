import hashlib, json
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11e_source_evidence_bundle_service as s
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
V={"expected_version":"0.1.218","repository_version":"0.1.218","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}

def test_blocks_without_confirmations(tmp_path):
 p=tmp_path/'v.json'; p.write_text(json.dumps(V)); h=hashlib.sha256(p.read_bytes()).hexdigest()
 r=s.build_phase11e_source_evidence_bundle_report(cfg(),expected_version='0.1.221',visibility_bundle_json=p,visibility_bundle_json_sha256=h)
 assert r['final_decision']=='BLOCKED'

def test_accepts_218_source_bundle(tmp_path):
 p=tmp_path/'v.json'; p.write_text(json.dumps(V)); h=hashlib.sha256(p.read_bytes()).hexdigest()
 r=s.build_phase11e_source_evidence_bundle_report(cfg(),expected_version='0.1.221',visibility_bundle_json=p,visibility_bundle_json_sha256=h,operator_confirmed=True,i_understand_read_only=True,i_understand_no_activation=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_restart=True,i_understand_no_abuse_automation=True,phase_status={'production_traffic':'none'},lanes=[{'name':'btc','enabled':True}],customers=[{'customer_key':'limited-btc-001','status':'paused','lane':'btc'}],current_controlled_artifact_gate={'unknown_mpf_artifacts':[],'production_gates_remain_closed':True})
 assert r['source_visibility_bundle_version']=='0.1.218'
 assert r['mutation_performed'] is False
