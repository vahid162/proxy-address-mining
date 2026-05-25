import json, hashlib
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_abuse_1h_readiness_service as s

def cfg(): return load_config(Path('configs/mpf.example.yaml'))
def w(p,o): p.write_text(json.dumps(o)); return p
V={"final_decision":"PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY","visibility_bundle_ready":True,"expected_version":"0.1.219","repository_version":"0.1.219","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}
A={"expected_version":"0.1.219","repository_version":"0.1.219","candidate_customer_key":"limited-btc-001","lane":"btc","public_port":20101,"all_active_enabled_lane_customers_scanned":True,"skipped_active_customers":[],"missing_active_customers":[],"silent_skip_detected":False,"exemption_policy_validated":True,"state_machine_contract":["normal","over_tracking","over_grace","hard"],"transition_coverage":["normal->over_tracking","over_tracking->over_grace","over_grace->normal","over_grace->over_tracking","over_tracking->hard_after_threshold"],"hard_threshold_sec":3600,"hard_before_threshold_detected":False,"farms_over_alone_hardens":False,"worker_over_alone_hardens":False,"missing_or_stale_evidence_hardens":False,"db_failure_hardens":False,"firewall_failure_hardens":False,"manual_unhard_audited":True,"restore_point_required_for_hard":True,"policy_backup_required_for_hard":True,"classifier_enabled_automation":False,"mutation_performed":False,"exemptions":[]}

def test_block_missing_abuse(tmp_path):
 p=w(tmp_path/'v.json',V); h=hashlib.sha256(p.read_bytes()).hexdigest(); r=s.build_phase11_single_customer_abuse_1h_readiness_report(cfg(),visibility_bundle_json=p,visibility_bundle_json_sha256=h,operator='o',reason='r',operator_confirmed=True,i_understand_abuse_readiness_only=True,i_understand_no_abuse_automation_enable=True,i_understand_no_hard_block_automation=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True); assert r['final_decision']=='BLOCKED'

def test_ready_and_contract_failures(tmp_path):
 p=w(tmp_path/'v.json',V); h=hashlib.sha256(p.read_bytes()).hexdigest(); a=A|{"visibility_bundle_sha256":h}; ap=w(tmp_path/'a.json',a)
 ok=s.build_phase11_single_customer_abuse_1h_readiness_report(cfg(),expected_version='0.1.219',visibility_bundle_json=p,visibility_bundle_json_sha256=h,abuse_evidence_json=ap,operator='o',reason='r',operator_confirmed=True,i_understand_abuse_readiness_only=True,i_understand_no_abuse_automation_enable=True,i_understand_no_hard_block_automation=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert ok['abuse_1h_coverage_ready'] is True and ok['mutation_performed'] is False
 bad=w(tmp_path/'bad.json',a|{'farms_over_alone_hardens':True})
 r=s.build_phase11_single_customer_abuse_1h_readiness_report(cfg(),visibility_bundle_json=p,visibility_bundle_json_sha256=h,abuse_evidence_json=bad,operator='o',reason='r',operator_confirmed=True,i_understand_abuse_readiness_only=True,i_understand_no_abuse_automation_enable=True,i_understand_no_hard_block_automation=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert r['final_decision']=='BLOCKED'
