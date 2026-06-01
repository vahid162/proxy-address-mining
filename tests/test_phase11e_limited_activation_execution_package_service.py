import json,hashlib
from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_execution_package_service import build_phase11e_limited_activation_execution_package_report
cfg=lambda: MPFConfig.model_construct(database=MPFConfig.model_fields['database'].annotation.model_construct())

def test_block_and_ready(tmp_path):
 p=tmp_path/'d.json'; p.write_text(json.dumps({'final_decision':'PHASE11E_LIMITED_ACTIVATION_DECISION_READY'})); s=hashlib.sha256(p.read_bytes()).hexdigest()
 k=dict(expected_version='0.1.228',limited_activation_decision_json=p,limited_activation_decision_json_sha256=s,operator='o',reason='r',operator_confirmed=True,i_understand_package_only=True,i_understand_no_activation_performed=True,i_understand_no_db_mutation=True,i_understand_no_firewall_apply=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True,i_understand_no_abuse_automation=True,i_understand_phase11_not_accepted=True)
 r=build_phase11e_limited_activation_execution_package_report(cfg(),**k)
 assert r['final_decision'].endswith('READY') and r['mutation_performed'] is False
 assert not any('mpf customer activate' in c for c in r['operator_commands'])
