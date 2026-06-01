import json
from pathlib import Path
from types import SimpleNamespace
from mpf import __version__
from mpf.services import phase11e_limited_customer_observation_window_service as service
from tests.test_phase11e_limited_activation_execute_service import _j, _sha
SCOPE={"candidate_customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}
def _rows(limited='active',canary='active'):
 return SimpleNamespace(ok=True,customers=[SimpleNamespace(customer_key='limited-btc-001',lane='btc',port=20101,status=limited),SimpleNamespace(customer_key='canary-btc-001',lane='btc',port=20001,status=canary)])
def _k(p:Path):
 p.mkdir(parents=True,exist_ok=True)
 def add(n,d): q=_j(p/f'{n}.json',d); return {f'{n}_json':str(q),f'{n}_json_sha256':_sha(q)}
 k={"expected_version":__version__,"operator":"o","reason":"r","window_start":"2026-06-01T00:00:00Z","window_end":"2026-06-01T00:01:00Z","sample_interval_seconds":0,"min_samples":2,
 **add('observation',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_OBSERVATION_READY',**SCOPE}),**add('acceptance_review',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_ACCEPTANCE_REVIEW_READY',**SCOPE}),**add('source_evidence',{'db_ok':True,'proxy_ok':True}),**add('artifact_gate',{'final_decision':'PASS_NO_CUSTOMER_ARTIFACTS','unknown_mpf_artifacts':[],'forbidden_public_runtime_exposure':False,'production_gates_remain_closed':True})}
 k.update({x:True for x in service.CONFIRMATIONS}); return k
def _run(monkeypatch,p,limited='active',canary='active',edit=None):
 k=_k(p); monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,**kw:_rows(limited,canary))
 if edit:
  n,c=edit; q=Path(k[f'{n}_json']); d=json.loads(q.read_text()); d.update(c); _j(q,d); k[f'{n}_json_sha256']=_sha(q)
 return service.build_phase11e_limited_customer_observation_window_report(SimpleNamespace(),**k)
def test_ready_collects_read_only_samples(monkeypatch,tmp_path):
 r=_run(monkeypatch,tmp_path); assert r['final_decision']=='PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY'; assert r['samples_collected']==2; assert r['doctor_ok'] is True
 for x in ('mutation_performed','db_mutation_performed','firewall_apply_performed','conntrack_flush_performed','docker_restart_performed','systemd_restart_performed','production_traffic_enabled','miner_traffic_allowed','abuse_automation_enabled','ui_allowed','telegram_allowed','phase11_accepted'): assert r[x] is False
def test_blocks_inactive_limited(monkeypatch,tmp_path): assert _run(monkeypatch,tmp_path,limited='paused')['final_decision']=='BLOCKED'
def test_blocks_inactive_canary(monkeypatch,tmp_path): assert _run(monkeypatch,tmp_path,canary='paused')['final_decision']=='BLOCKED'
def test_blocks_not_ready_inputs_and_unsafe_artifact(monkeypatch,tmp_path):
 for i,e in enumerate([('acceptance_review',{'final_decision':'wrong'}),('observation',{'final_decision':'wrong'}),('artifact_gate',{'forbidden_public_runtime_exposure':True})]): assert _run(monkeypatch,tmp_path/str(i),edit=e)['final_decision']=='BLOCKED'
def test_blocks_open_current_gate(monkeypatch,tmp_path):
 monkeypatch.setattr(service,'validate_current_phase_gate',lambda b:b.append('current_phase_gate_open:production_traffic')); assert _run(monkeypatch,tmp_path)['final_decision']=='BLOCKED'
def test_blocks_hash_mismatch(monkeypatch,tmp_path):
 k=_k(tmp_path); k['observation_json_sha256']='bad'; monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,**kw:_rows()); assert service.build_phase11e_limited_customer_observation_window_report(SimpleNamespace(),**k)['final_decision']=='BLOCKED'
