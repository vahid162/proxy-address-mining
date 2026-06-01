import json
from pathlib import Path
from types import SimpleNamespace
from mpf import __version__
from mpf.services import phase11e_limited_activation_acceptance_review_service as service
from tests.test_phase11e_limited_activation_execute_service import _j,_sha
SCOPE={"candidate_customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}
def _k(p:Path):
 p.mkdir(parents=True,exist_ok=True)
 def add(name,payload): q=_j(p/f'{name}.json',payload); return {f'{name}_json':str(q),f'{name}_json_sha256':_sha(q)}
 obs={"final_decision":"PHASE11E_LIMITED_ACTIVATION_OBSERVATION_READY",**SCOPE,**{x:False for x in service.FORBIDDEN_TRUE_FIELDS}}
 rb={"component":"phase11e_limited_activation_rollback_package","final_decision":"PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY","rollback_customer_key":"limited-btc-001","rollback_lane":"btc","rollback_public_port":20101,"rollback_backend_target":"172.18.0.3:60010"}
 k={"expected_version":__version__,"operator":"o","reason":"r",**add('activation_execution',{"final_decision":"PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE",**SCOPE}),**add('post_activation_evidence',{"final_decision":"PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY",**SCOPE}),**add('observation',obs),**add('limited_activation_rollback_package',rb),**add('artifact_gate',{"final_decision":"PASS_NO_CUSTOMER_ARTIFACTS","unknown_mpf_artifacts":[],"forbidden_public_runtime_exposure":False,"production_gates_remain_closed":True})}; k.update({x:True for x in service.CONFIRMATIONS}); return k
def _run(p,edit=None):
 k=_k(p)
 if edit:
  n,c=edit; q=Path(k[f'{n}_json']); d=json.loads(q.read_text()); d.update(c); _j(q,d); k[f'{n}_json_sha256']=_sha(q)
 return service.build_phase11e_limited_activation_acceptance_review_report(SimpleNamespace(),**k)
def test_ready_is_review_only(tmp_path):
 r=_run(tmp_path); assert r['final_decision']=='PHASE11E_LIMITED_ACTIVATION_ACCEPTANCE_REVIEW_READY'; assert r['phase11_final_acceptance_allowed'] is False
 for x in service.FORBIDDEN_TRUE_FIELDS: assert r[x] is False
def test_blocks_observation_rollback_and_expansion(tmp_path):
 for i,e in enumerate([('observation',{'final_decision':'wrong'}),('limited_activation_rollback_package',{'rollback_public_port':999}),('observation',{'miner_traffic_allowed':True}),('observation',{'abuse_automation_enabled':True}),('observation',{'ui_allowed':True}),('observation',{'telegram_allowed':True})]): assert _run(tmp_path/str(i),e)['final_decision']=='BLOCKED'
def test_blocks_open_gate(monkeypatch,tmp_path):
 monkeypatch.setattr(service,'validate_current_phase_gate',lambda b:b.append('current_phase_gate_open:ui_allowed')); assert _run(tmp_path)['final_decision']=='BLOCKED'
