import json,hashlib
from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_post_evidence_service import build_phase11e_limited_activation_post_evidence_report
cfg=lambda: MPFConfig.model_construct(database=MPFConfig.model_fields['database'].annotation.model_construct())
def test_read_only(tmp_path):
 p=tmp_path/'e.json'; p.write_text(json.dumps({'candidate_customer_key':'limited-btc-001'})); s=hashlib.sha256(p.read_bytes()).hexdigest();
 r=build_phase11e_limited_activation_post_evidence_report(cfg(),expected_version='0.1.228',activation_execution_json=p,activation_execution_json_sha256=s,operator='o',reason='r',operator_confirmed=True,i_understand_post_evidence_only=True,i_understand_no_db_mutation=True,i_understand_no_firewall_apply=True,i_understand_no_production_traffic_expansion=True,i_understand_no_miner_traffic_expansion=True)
 assert r['final_decision'].endswith('READY') and r['mutation_performed'] is False
