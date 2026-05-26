import hashlib, json
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_restart_container_order_evidence_builder_service as s
from mpf.services import phase11_single_customer_restart_container_order_readiness_service as r
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
V={"final_decision":"PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY","visibility_bundle_ready":True,"expected_version":"0.1.218","repository_version":"0.1.218","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}
AG={"final_decision":"PASS_NO_CUSTOMER_ARTIFACTS","unknown_mpf_artifacts":[],"production_gates_remain_closed":True}

def w(p,o): p.write_text(json.dumps(o)); return p

def test_default_blocked_and_missing_artifact(tmp_path):
 v=w(tmp_path/'v.json',V); h=hashlib.sha256(v.read_bytes()).hexdigest()
 rep=s.build_phase11_single_customer_restart_container_order_evidence_report(cfg(),expected_version='0.1.220',visibility_bundle_json=v,visibility_bundle_json_sha256=h,operator='o',reason='r',operator_confirmed=True,i_understand_evidence_only=True,i_understand_no_restart=True,i_understand_no_docker_restart=True,i_understand_no_systemctl_restart=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True)
 assert rep['final_decision']=='BLOCKED' and 'missing_artifact_gate_evidence' in rep['blockers']

def test_ready_only_with_explicit_sources(tmp_path):
 v=w(tmp_path/'v.json',V); h=hashlib.sha256(v.read_bytes()).hexdigest(); ag=w(tmp_path/'ag.json',AG); agh=hashlib.sha256(ag.read_bytes()).hexdigest()
 kwargs={k:True for k in ['post_restart_or_controlled_order_test_performed','required_containers_running','v2raya_running_before_forwarder_check','socks_bridge_ready_before_forwarder_check','forwarder_ready','bridge_ready','proxy_doctor_ok','mpf_doctor_ok','db_status_ok','phase_gate_ok','backend_60010_local_or_internal_reachable']}
 kwargs.update({'post_restart_or_controlled_order_source':'operator evidence','required_containers_running_source':'docker ps','v2raya_order_source':'docker compose ps','socks_bridge_order_source':'docker compose ps','forwarder_ready_source':'mpf proxy doctor','bridge_ready_source':'mpf proxy doctor','proxy_doctor_source':'mpf proxy doctor','mpf_doctor_source':'mpf doctor','db_status_source':'mpf db status','phase_gate_source':'mpf phase-status','backend_internal_reachability_source':'ss output','exposure_check_source':'doctor output','public_v2raya_ui_exposed':False,'backend_60010_publicly_exposed':False})
 rep=s.build_phase11_single_customer_restart_container_order_evidence_report(cfg(),expected_version='0.1.220',visibility_bundle_json=v,visibility_bundle_json_sha256=h,artifact_gate_json=ag,artifact_gate_json_sha256=agh,operator='o',reason='r',operator_confirmed=True,i_understand_evidence_only=True,i_understand_no_restart=True,i_understand_no_docker_restart=True,i_understand_no_systemctl_restart=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True,**kwargs)
 assert rep['final_decision'].endswith('READY') and rep['mutation_performed'] is False
 p=tmp_path/'r.json'; p.write_text(json.dumps(rep))
 rr=r.build_phase11_single_customer_restart_container_order_readiness_report(cfg(),expected_version='0.1.220',visibility_bundle_json=v,visibility_bundle_json_sha256=h,restart_evidence_json=p,artifact_gate_json=ag,artifact_gate_json_sha256=agh,operator='o',reason='r',operator_confirmed=True,i_understand_restart_readiness_only=True,i_understand_no_restart_performed_by_classifier=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert rr['final_decision'].endswith('READY')


def test_source_bundle_controlled_order_maps_to_post_restart_or_controlled(tmp_path):
 v=w(tmp_path/'v.json',V); h=hashlib.sha256(v.read_bytes()).hexdigest(); ag=w(tmp_path/'ag.json',AG); agh=hashlib.sha256(ag.read_bytes()).hexdigest()
 se=w(tmp_path/'se.json',{"runtime_order_observations":{"controlled_order_test_performed":True,"post_host_restart_test_performed":False,"required_containers_running":True,"v2raya_running_before_forwarder_check":True,"socks_bridge_ready_before_forwarder_check":True,"forwarder_ready":True,"bridge_ready":True,"post_restart_or_controlled_order_source":"source-bundle","required_containers_running_source":"source-bundle","v2raya_order_source":"source-bundle","socks_bridge_order_source":"source-bundle","forwarder_ready_source":"source-bundle","bridge_ready_source":"source-bundle","backend_60010_local_or_internal_reachable":True,"backend_internal_reachability_source":"source-bundle","proxy_doctor_ok":True,"mpf_doctor_ok":True,"db_status_ok":True},"exposure_observations":{"source":"source-bundle","public_v2raya_ui_exposed":False,"backend_60010_publicly_exposed":False},"phase_status":{"production_traffic":"none","firewall_apply_allowed":"no","abuse_automation_allowed":"no"}})
 seh=hashlib.sha256(se.read_bytes()).hexdigest()
 rep=s.build_phase11_single_customer_restart_container_order_evidence_report(cfg(),expected_version='0.1.223',visibility_bundle_json=v,visibility_bundle_json_sha256=h,source_evidence_json=se,source_evidence_json_sha256=seh,artifact_gate_json=ag,artifact_gate_json_sha256=agh,operator='o',reason='r',operator_confirmed=True,i_understand_evidence_only=True,i_understand_no_restart=True,i_understand_no_docker_restart=True,i_understand_no_systemctl_restart=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True)
 assert rep['post_restart_or_controlled_order_test_performed'] is True
 assert rep['final_decision'].endswith('READY')


def test_source_bundle_false_controlled_and_false_post_restart_remains_blocked(tmp_path):
 v=w(tmp_path/'v.json',V); h=hashlib.sha256(v.read_bytes()).hexdigest(); ag=w(tmp_path/'ag.json',AG); agh=hashlib.sha256(ag.read_bytes()).hexdigest()
 se=w(tmp_path/'se.json',{"runtime_order_observations":{"controlled_order_test_performed":False,"post_host_restart_test_performed":False,"required_containers_running":True,"v2raya_running_before_forwarder_check":True,"socks_bridge_ready_before_forwarder_check":True,"forwarder_ready":True,"bridge_ready":True,"backend_60010_local_or_internal_reachable":True},"exposure_observations":{"source":"source-bundle","public_v2raya_ui_exposed":False,"backend_60010_publicly_exposed":False},"proxy_doctor":{"ok":True},"mpf_doctor":{"ok":True},"db_status":{"ok":True},"phase_status":{"production_traffic":"none","firewall_apply_allowed":"no","abuse_automation_allowed":"no"}})
 seh=hashlib.sha256(se.read_bytes()).hexdigest()
 rep=s.build_phase11_single_customer_restart_container_order_evidence_report(cfg(),expected_version='0.1.223',visibility_bundle_json=v,visibility_bundle_json_sha256=h,source_evidence_json=se,source_evidence_json_sha256=seh,artifact_gate_json=ag,artifact_gate_json_sha256=agh,operator='o',reason='r',operator_confirmed=True,i_understand_evidence_only=True,i_understand_no_restart=True,i_understand_no_docker_restart=True,i_understand_no_systemctl_restart=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True)
 assert rep['post_restart_or_controlled_order_test_performed'] is False
 assert 'missing_or_false:post_restart_or_controlled_order_test_performed' in rep['blockers']
 assert rep['final_decision'] == 'BLOCKED'
