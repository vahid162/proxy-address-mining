from types import SimpleNamespace
from mpf.services import phase11e_limited_activation_post_evidence_collect_service as service
from tests.test_phase11e_limited_activation_execute_service import _j,_sha,_rows
from mpf import __version__
def _k(t):
 s={'candidate_customer_key':'limited-btc-001','lane':'btc','public_port':20101,'backend_target':'172.18.0.3:60010'};e=_j(t/'e.json',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE',**s});a=_j(t/'a.json',{'final_decision':'PASS_NO_CUSTOMER_ARTIFACTS','unknown_mpf_artifacts':[],'forbidden_public_runtime_exposure':False,'production_gates_remain_closed':True});src=_j(t/'s.json',{'db_ok':True,'proxy_ok':True,'changed_customers':['limited-btc-001']});k={'expected_version':__version__,'activation_execution_json':str(e),'activation_execution_json_sha256':_sha(e),'artifact_gate_json':str(a),'artifact_gate_json_sha256':_sha(a),'source_evidence_json':str(src),'source_evidence_json_sha256':_sha(src),'operator':'op','reason':'r'};k.update({x:True for x in service.CONFIRMATIONS});return k
def test_post_evidence_ready_and_read_only(monkeypatch,tmp_path):
 monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,**k:_rows('active'));r=service.build_phase11e_limited_activation_post_evidence_collect_report(SimpleNamespace(),**_k(tmp_path));assert r['final_decision']=='PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY';assert r['mutation_performed'] is False;assert r['db_mutation_performed'] is False
def test_post_evidence_blocks_hash_unknown_exposure_and_customer_states(monkeypatch,tmp_path):
 for rows,edit in [(_rows('paused'),None),(_rows('active','paused'),None),(_rows('active'),{'unknown_mpf_artifacts':['x']}),(_rows('active'),{'forbidden_public_runtime_exposure':True})]:
  monkeypatch.setattr(service.customer_read_service,'list_customer_status',lambda *a,_rows=rows,**k:_rows);k=_k(tmp_path)
  if edit:
   p=__import__('pathlib').Path(k['artifact_gate_json']);d=__import__('json').loads(p.read_text());d.update(edit);_j(p,d);k['artifact_gate_json_sha256']=_sha(p)
  assert service.build_phase11e_limited_activation_post_evidence_collect_report(SimpleNamespace(),**k)['final_decision']=='BLOCKED'
