import json, hashlib
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_limited_acceptance_precheck_service as s
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
w=lambda p,o: (p.write_text(json.dumps(o)),p)[1]
def test_blocks_missing(tmp_path):
 v=w(tmp_path/'v.json',{'final_decision':'BLOCKED','visibility_bundle_ready':False}); a=w(tmp_path/'a.json',{'abuse_1h_coverage_ready':False}); r=w(tmp_path/'r.json',{'restart_container_order_ready':False})
 out=s.build_phase11_single_customer_limited_acceptance_precheck_report(cfg(),visibility_bundle_json=v,abuse_1h_readiness_json=a,restart_container_order_readiness_json=r,operator='o',reason='r',operator_confirmed=True,i_understand_precheck_only=True,i_understand_no_customer_activation=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert out['final_decision']=='BLOCKED' and out['mutation_performed'] is False
