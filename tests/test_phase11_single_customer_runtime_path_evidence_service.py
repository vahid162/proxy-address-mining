import hashlib, json
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_runtime_path_evidence_service as svc, customer_read_service
from types import SimpleNamespace


def _cfg(): return load_config(Path('configs/mpf.example.yaml'))

def _row(status='paused'): return SimpleNamespace(customer_key='limited-btc-001', lane='btc', port=20101, status=status)

def test_blocked_missing_runtime_files(tmp_path, monkeypatch):
    p=tmp_path/'post.json'; p.write_text(json.dumps({'final_decision':'PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY','controlled_apply_recorded':True,'post_apply_evidence_ready':True,'production_traffic_enabled':False,'miner_traffic_allowed':False,'phase11_accepted':False,'db_activation_allowed':False,'has_20101_chain':True,'has_20101_ref':True}))
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k: customer_read_service.CustomerList(ok=True,message='ok',customers=[_row()]))
    r=svc.build_phase11_single_customer_runtime_path_evidence_report(_cfg(),post_apply_evidence_json=p,post_apply_evidence_json_sha256=sha,operator_confirmed=True,i_understand_runtime_evidence_only=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True,i_confirm_stratum_transcript_required=True,i_confirm_visibility_bundle_required=True,i_confirm_abuse_1h_required_before_customer_traffic=True,i_confirm_restart_container_order_required_before_limited_acceptance=True)
    assert r['final_decision']=='BLOCKED'

def test_hash_mismatch(tmp_path, monkeypatch):
    p=tmp_path/'post.json'; p.write_text('{}'); monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k: customer_read_service.CustomerList(ok=True,message='ok',customers=[_row()]))
    r=svc.build_phase11_single_customer_runtime_path_evidence_report(_cfg(),post_apply_evidence_json=p,post_apply_evidence_json_sha256='x')
    assert 'post_apply_evidence_json_hash_mismatch' in r['blockers']


def test_invalid_json_and_non_object_block(tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k: customer_read_service.CustomerList(ok=True,message='ok',customers=[SimpleNamespace(customer_key='limited-btc-001',lane='btc',port=20101,status='paused')]))
    bad=tmp_path/'bad.json'; bad.write_text('{',encoding='utf-8')
    r=svc.build_phase11_single_customer_runtime_path_evidence_report(_cfg(),post_apply_evidence_json=bad,post_apply_evidence_json_sha256='x')
    assert 'post_apply_evidence_json_invalid' in r['blockers']
    arr=tmp_path/'arr.json'; arr.write_text('[1]',encoding='utf-8')
    ra=svc.build_phase11_single_customer_runtime_path_evidence_report(_cfg(),post_apply_evidence_json=arr,post_apply_evidence_json_sha256='x')
    assert 'post_apply_evidence_json_invalid' in ra['blockers']

def test_db_exception_scope_and_safety_block(tmp_path, monkeypatch):
    p=tmp_path/'post.json'
    p.write_text(json.dumps({'final_decision':'PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY','controlled_apply_recorded':True,'post_apply_evidence_ready':True,'production_traffic_enabled':True,'miner_traffic_allowed':False,'phase11_accepted':False,'db_activation_allowed':False,'mutation_performed':False,'has_20101_chain':True,'has_20101_ref':True,'candidate_customer_key':'x','candidate_lane':'btc','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010','blockers':[],'warnings':[]}))
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k: (_ for _ in ()).throw(RuntimeError('db')))
    r=svc.build_phase11_single_customer_runtime_path_evidence_report(_cfg(),post_apply_evidence_json=p,post_apply_evidence_json_sha256=sha,operator_confirmed=True,i_understand_runtime_evidence_only=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True,i_confirm_stratum_transcript_required=True,i_confirm_visibility_bundle_required=True,i_confirm_abuse_1h_required_before_customer_traffic=True,i_confirm_restart_container_order_required_before_limited_acceptance=True)
    assert 'db_read_failed' in r['blockers']
    assert 'post_apply_evidence_scope_mismatch' in r['blockers']
    assert 'post_apply_evidence_safety_boundary_open' in r['blockers']
    for f in ('production_traffic_enabled','miner_traffic_allowed','phase11_accepted','db_activation_allowed','mutation_performed'):
        assert r[f] is False
