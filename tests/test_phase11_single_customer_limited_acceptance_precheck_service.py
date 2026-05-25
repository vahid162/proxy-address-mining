import json, hashlib
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_limited_acceptance_precheck_service as s
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
def w(p,o): p.write_text(json.dumps(o)); return p

def test_blocks_on_non_dict_and_safety_flags(tmp_path):
 v=w(tmp_path/'v.json',[]); a=w(tmp_path/'a.json',{"abuse_1h_coverage_ready":True,"production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}); r=w(tmp_path/'r.json',{"restart_container_order_ready":True,"production_traffic_enabled":True,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False})
 out=s.build_phase11_single_customer_limited_acceptance_precheck_report(cfg(),visibility_bundle_json=v,visibility_bundle_json_sha256=hashlib.sha256(v.read_bytes()).hexdigest(),abuse_1h_readiness_json=a,restart_container_order_readiness_json=r,operator='o',reason='r',operator_confirmed=True,i_understand_precheck_only=True,i_understand_no_customer_activation=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert out['final_decision']=='BLOCKED'
