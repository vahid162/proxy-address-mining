import hashlib, json
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_restart_container_order_evidence_builder_service as s
from mpf.services import phase11_single_customer_restart_container_order_readiness_service as r
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
V={"final_decision":"PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY","visibility_bundle_ready":True,"expected_version":"0.1.218","repository_version":"0.1.218","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}
AG={"final_decision":"PASS_NO_CUSTOMER_ARTIFACTS","unknown_mpf_artifacts":[],"production_gates_remain_closed":True}

def w(p,o): p.write_text(json.dumps(o)); return p

def test_core(tmp_path):
 v=w(tmp_path/'v.json',V); h=hashlib.sha256(v.read_bytes()).hexdigest(); ag=w(tmp_path/'ag.json',AG); agh=hashlib.sha256(ag.read_bytes()).hexdigest()
 rep=s.build_phase11_single_customer_restart_container_order_evidence_report(cfg(),expected_version='0.1.220',visibility_bundle_json=v,visibility_bundle_json_sha256=h,artifact_gate_json=ag,artifact_gate_json_sha256=agh,operator='o',reason='r',operator_confirmed=True,i_understand_evidence_only=True,i_understand_no_restart=True,i_understand_no_docker_restart=True,i_understand_no_systemctl_restart=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True)
 assert rep['final_decision'].endswith('READY')
 p=tmp_path/'r.json'; p.write_text(json.dumps(rep))
 rr=r.build_phase11_single_customer_restart_container_order_readiness_report(cfg(),expected_version='0.1.220',visibility_bundle_json=v,visibility_bundle_json_sha256=h,restart_evidence_json=p,artifact_gate_json=ag,artifact_gate_json_sha256=agh,operator='o',reason='r',operator_confirmed=True,i_understand_restart_readiness_only=True,i_understand_no_restart_performed_by_classifier=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert rr['final_decision'].endswith('READY')
