import json,hashlib
from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_rollback_package_service import build_phase11e_limited_activation_rollback_package_report
cfg=lambda: MPFConfig.model_construct(database=MPFConfig.model_fields['database'].annotation.model_construct())
def test_ready(tmp_path):
 p=tmp_path/'d.json'; p.write_text(json.dumps({'final_decision':'PHASE11E_LIMITED_ACTIVATION_DECISION_READY'})); s=hashlib.sha256(p.read_bytes()).hexdigest();
 r=build_phase11e_limited_activation_rollback_package_report(cfg(),expected_version='0.1.224',limited_activation_decision_json=p,limited_activation_decision_json_sha256=s,operator='o',reason='r',operator_confirmed=True,i_understand_rollback_package_only=True,i_understand_no_rollback_performed=True,i_understand_no_db_mutation=True,i_understand_no_firewall_apply=True)
 assert r['final_decision'].endswith('READY') and r['mutation_performed'] is False
