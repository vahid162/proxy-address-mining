import json, hashlib
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_restart_container_order_readiness_service as s
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
def w(p,o): p.write_text(json.dumps(o)); return p
V={"final_decision":"PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY","visibility_bundle_ready":True,"expected_version":"0.1.218","repository_version":"0.1.218","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}
R={"candidate_customer_key":"limited-btc-001","lane":"btc","public_port":20101,"post_restart_or_controlled_order_test_performed":True,"required_containers_running":True,"v2raya_running_before_forwarder_check":True,"socks_bridge_ready_before_forwarder_check":True,"forwarder_ready":True,"bridge_ready":True,"proxy_doctor_ok":True,"mpf_doctor_ok":True,"db_status_ok":True,"phase_gate_ok":True,"current_controlled_artifact_gate_passed":True,"unknown_mpf_artifacts":[],"public_v2raya_ui_exposed":False,"backend_60010_publicly_exposed":False,"backend_60010_local_or_internal_reachable":True,"limited_btc_001_status_changed_by_this_check":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"mutation_performed":False}
AG={"final_decision":"PASS_NO_CUSTOMER_ARTIFACTS","unknown_mpf_artifacts":[],"production_gates_remain_closed":True}

def test_artifact_gate_validation(tmp_path):
 v=w(tmp_path/'v.json',V); vh=hashlib.sha256(v.read_bytes()).hexdigest(); ag=w(tmp_path/'ag.json',AG); agh=hashlib.sha256(ag.read_bytes()).hexdigest(); re=w(tmp_path/'r.json',R|{'visibility_bundle_sha256':vh})
 ok=s.build_phase11_single_customer_restart_container_order_readiness_report(cfg(),expected_version='0.1.219',visibility_bundle_json=v,visibility_bundle_json_sha256=vh,restart_evidence_json=re,artifact_gate_json=ag,artifact_gate_json_sha256=agh,operator='o',reason='r',operator_confirmed=True,i_understand_restart_readiness_only=True,i_understand_no_restart_performed_by_classifier=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert ok['final_decision'].endswith('READY')
 bad=s.build_phase11_single_customer_restart_container_order_readiness_report(cfg(),expected_version='0.1.219',visibility_bundle_json=v,visibility_bundle_json_sha256=vh,restart_evidence_json=re,artifact_gate_json=ag,artifact_gate_json_sha256='x',operator='o',reason='r',operator_confirmed=True,i_understand_restart_readiness_only=True,i_understand_no_restart_performed_by_classifier=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert bad['final_decision']=='BLOCKED'
