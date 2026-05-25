import json, hashlib
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_restart_container_order_readiness_service as s
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
w=lambda p,o: (p.write_text(json.dumps(o)),p)[1]
V={"final_decision":"PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY","visibility_bundle_ready":True,"candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}

def test_block_missing_restart(tmp_path):
 p=w(tmp_path/'v.json',V); h=hashlib.sha256(p.read_bytes()).hexdigest(); r=s.build_phase11_single_customer_restart_container_order_readiness_report(cfg(),visibility_bundle_json=p,visibility_bundle_json_sha256=h,operator='o',reason='r',operator_confirmed=True,i_understand_restart_readiness_only=True,i_understand_no_restart_performed_by_classifier=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True); assert r['final_decision']=='BLOCKED'
