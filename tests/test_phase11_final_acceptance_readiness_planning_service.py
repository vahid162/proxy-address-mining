import json
from pathlib import Path
from types import SimpleNamespace
from mpf import __version__
from mpf.services import phase11_final_acceptance_readiness_planning_service as service
from tests.test_phase11e_limited_activation_execute_service import _j,_sha
SCOPE={"candidate_customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}
def _k(p:Path):
 p.mkdir(parents=True,exist_ok=True)
 def add(n,d): q=_j(p/f'{n}.json',d); return {f'{n}_json':str(q),f'{n}_json_sha256':_sha(q)}
 rb={"component":"phase11e_limited_activation_rollback_package","final_decision":"PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY","rollback_customer_key":"limited-btc-001","rollback_lane":"btc","rollback_public_port":20101,"rollback_backend_target":"172.18.0.3:60010"}
 k={"expected_version":__version__,"operator":"o","reason":"r",**add('observation_window',{'final_decision':'PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY',**SCOPE}),**add('acceptance_review',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_ACCEPTANCE_REVIEW_READY',**SCOPE}),**add('rollback_package',rb),**add('artifact_gate',{'final_decision':'PASS_NO_CUSTOMER_ARTIFACTS','unknown_mpf_artifacts':[],'forbidden_public_runtime_exposure':False,'production_gates_remain_closed':True})}; k.update({x:True for x in service.CONFIRMATIONS}); return k
def _run(p,edit=None):
 k=_k(p)
 if edit:
  n,c=edit; q=Path(k[f'{n}_json']); d=json.loads(q.read_text()); d.update(c); _j(q,d); k[f'{n}_json_sha256']=_sha(q)
 return service.build_phase11_final_acceptance_readiness_planning_report(SimpleNamespace(),**k)
def test_ready_is_planning_only(tmp_path):
 r=_run(tmp_path); assert r['final_decision']=='PHASE11_FINAL_ACCEPTANCE_READINESS_PLANNING_READY'; assert r['phase11_final_acceptance_pr_ready'] is True
 for x in ('phase11_final_acceptance_allowed','production_expansion_allowed','miner_traffic_expansion_allowed','abuse_automation_allowed','ui_allowed','telegram_allowed','phase11_accepted'): assert r[x] is False
def test_blocks_window_and_rollback_not_ready(tmp_path):
 assert _run(tmp_path/'a',('observation_window',{'final_decision':'wrong'}))['final_decision']=='BLOCKED'
 assert _run(tmp_path/'b',('rollback_package',{'final_decision':'wrong'}))['final_decision']=='BLOCKED'
