import json
from pathlib import Path
from types import SimpleNamespace
from mpf import __version__
from mpf.services import phase11e_limited_activation_observation_collect_service as service
from tests.test_phase11e_limited_activation_execute_service import _j, _rows, _sha
SCOPE={"candidate_customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}
def _k(p:Path):
 p.mkdir(parents=True,exist_ok=True)
 def add(name,payload):
  q=_j(p/f'{name}.json',payload); return {f'{name}_json':str(q),f'{name}_json_sha256':_sha(q)}
 k={"expected_version":__version__,"operator":"o","reason":"r",**add('activation_execution',{"final_decision":"PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE",**SCOPE}),**add('post_activation_evidence',{"final_decision":"PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY",**SCOPE}),**add('source_evidence',{"db_status":{"ok":True},"proxy_doctor":{"final_verdict":"OK"}}),**add('artifact_gate',{"final_decision":"PASS_NO_CUSTOMER_ARTIFACTS","unknown_mpf_artifacts":[],"forbidden_public_runtime_exposure":False,"production_gates_remain_closed":True})}
 k.update({x:True for x in service.CONFIRMATIONS}); return k
def _run(monkeypatch,p,rows=None,edit=None):
 monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,**k:rows or _rows('active'))
 k=_k(p)
 if edit:
  name,changes=edit; q=Path(k[f'{name}_json']); d=json.loads(q.read_text()); d.update(changes); _j(q,d); k[f'{name}_json_sha256']=_sha(q)
 return service.build_phase11e_limited_activation_observation_collect_report(SimpleNamespace(),**k)
def test_ready_is_read_only(monkeypatch,tmp_path):
 r=_run(monkeypatch,tmp_path); assert r['final_decision']=='PHASE11E_LIMITED_ACTIVATION_OBSERVATION_READY'; assert r['canary_preserved'] is True
 for x in ('mutation_performed','db_mutation_performed','firewall_apply_performed','conntrack_flush_performed','docker_restart_performed','systemd_restart_performed','production_traffic_enabled','miner_traffic_allowed','abuse_automation_enabled','phase11_accepted'): assert r[x] is False
def test_blocks_customer_states(monkeypatch,tmp_path):
 assert _run(monkeypatch,tmp_path/'a',_rows('paused'))['final_decision']=='BLOCKED'; assert _run(monkeypatch,tmp_path/'b',_rows('active','paused'))['final_decision']=='BLOCKED'
def test_blocks_invalid_inputs(monkeypatch,tmp_path):
 for i,e in enumerate([('activation_execution',{'final_decision':'wrong'}),('post_activation_evidence',{'final_decision':'wrong'}),('source_evidence',{'db_status':{'ok':False},'proxy_ok':True}),('artifact_gate',{'unknown_mpf_artifacts':['x']}),('artifact_gate',{'forbidden_public_runtime_exposure':True}),('artifact_gate',{'production_gates_remain_closed':False})]): assert _run(monkeypatch,tmp_path/str(i),edit=e)['final_decision']=='BLOCKED'
def test_blocks_open_current_gate(monkeypatch,tmp_path):
 monkeypatch.setattr(service,'validate_current_phase_gate',lambda b:b.append('current_phase_gate_open:production_traffic')); assert _run(monkeypatch,tmp_path)['final_decision']=='BLOCKED'
