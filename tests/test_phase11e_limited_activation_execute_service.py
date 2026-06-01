from __future__ import annotations
import hashlib,json
from pathlib import Path
from types import SimpleNamespace
from mpf import __version__
from mpf.services import phase11e_limited_activation_execute_service as service

def _j(p:Path,x:dict):p.write_text(json.dumps(x));return p
def _sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def _rows(limited_status='paused',canary_status='active',limited_lane='btc',limited_port=20101):return SimpleNamespace(ok=True,customers=[SimpleNamespace(customer_key='limited-btc-001',status=limited_status,lane=limited_lane,port=limited_port),SimpleNamespace(customer_key='canary-btc-001',status=canary_status,lane='btc',port=20001)])
def _kwargs(tmp_path):
 scope={'candidate_customer_key':'limited-btc-001','lane':'btc','public_port':20101,'backend_target':'172.18.0.3:60010'}
 files=[]
 for n,d in [('limited_activation_decision',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_DECISION_READY',**scope}),('limited_activation_execution_package',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_EXECUTION_PACKAGE_READY',**scope}),('limited_activation_rollback_package',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY',**scope}),('artifact_gate',{'final_decision':'PASS_NO_CUSTOMER_ARTIFACTS','unknown_mpf_artifacts':[],'forbidden_public_runtime_exposure':False,'production_gates_remain_closed':True})]:
  p=_j(tmp_path/f'{n}.json',d);files += [(f'{n}_json',str(p)),(f'{n}_json_sha256',_sha(p))]
 k=dict(files);k.update(expected_version=__version__,operator='op',reason='test')
 for c in service.CONFIRMATIONS:k[c]=True
 return k
def test_execute_is_exact_scope_hash_backed_and_changes_only_limited(monkeypatch,tmp_path):
 monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,**k:_rows())
 called=[];monkeypatch.setattr(service.customer_mutation_service,'activate_phase11e_limited_customer',lambda *a,**k:(called.append(k) or SimpleNamespace(ok=True,message='OK')))
 r=service.build_phase11e_limited_activation_execute_report(SimpleNamespace(),**_kwargs(tmp_path))
 assert r['final_decision']=='PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE';assert r['changed_customers']==['limited-btc-001'];assert r['after_customer_status']=='active';assert called[0]['customer_key']=='limited-btc-001';assert all(r[x] is False for x in ['firewall_apply_performed','conntrack_flush_performed','docker_restart_performed','systemd_restart_performed'])
def test_execute_blocks_missing_confirmation_without_mutation(monkeypatch,tmp_path):
 monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,**k:_rows());monkeypatch.setattr(service.customer_mutation_service,'activate_phase11e_limited_customer',lambda *a,**k:(_ for _ in ()).throw(AssertionError('mutation')))
 k=_kwargs(tmp_path);k['operator_confirmed']=False;r=service.build_phase11e_limited_activation_execute_report(SimpleNamespace(),**k);assert r['final_decision']=='BLOCKED';assert r['mutation_performed'] is False
def test_execute_blocks_each_hash_mismatch(monkeypatch,tmp_path):
 monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,**k:_rows())
 for key in ['limited_activation_decision_json_sha256','limited_activation_execution_package_json_sha256','limited_activation_rollback_package_json_sha256','artifact_gate_json_sha256']:
  k=_kwargs(tmp_path);k[key]='bad';r=service.build_phase11e_limited_activation_execute_report(SimpleNamespace(),**k);assert r['final_decision']=='BLOCKED'
def test_execute_blocks_wrong_version_customer_state_scope_and_gate(monkeypatch,tmp_path):
 for rows,change in [(_rows('active'),{}),(_rows(canary_status='paused'),{}),(_rows(limited_lane='ltc'),{}),(_rows(),{'expected_version':'0.0.0'})]:
  monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,_rows=rows,**k:_rows);k=_kwargs(tmp_path);k.update(change);assert service.build_phase11e_limited_activation_execute_report(SimpleNamespace(),**k)['final_decision']=='BLOCKED'
def test_execute_blocks_artifact_exposure_unknown_and_not_ready_packages(monkeypatch,tmp_path):
 monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,**k:_rows())
 for filename,change in [('artifact_gate',{'unknown_mpf_artifacts':['x']}),('artifact_gate',{'forbidden_public_runtime_exposure':True}),('limited_activation_decision',{'final_decision':'BLOCKED'}),('limited_activation_execution_package',{'final_decision':'BLOCKED'}),('limited_activation_rollback_package',{'final_decision':'BLOCKED'})]:
  k=_kwargs(tmp_path);p=Path(k[f'{filename}_json']);d=json.loads(p.read_text());d.update(change);_j(p,d);k[f'{filename}_json_sha256']=_sha(p);assert service.build_phase11e_limited_activation_execute_report(SimpleNamespace(),**k)['final_decision']=='BLOCKED'

def test_repository_wrapper_rejects_non_exact_scope_without_db():
 from mpf.repositories.customer_write_repo import activate_phase11e_limited_customer, rollback_phase11e_limited_customer
 cfg=SimpleNamespace(database=SimpleNamespace(url='must-not-connect'))
 assert not activate_phase11e_limited_customer(cfg,customer_key='other',lane='btc',port=20101,operator='op',reason='r').ok
 assert not rollback_phase11e_limited_customer(cfg,customer_key='limited-btc-001',lane='btc',port=9999,operator='op',reason='r').ok
