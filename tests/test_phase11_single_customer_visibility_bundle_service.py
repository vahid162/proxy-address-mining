import hashlib, json
from pathlib import Path
from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import phase11_single_customer_visibility_bundle_service as svc


def _cfg(): return load_config(Path('configs/mpf.example.yaml'))
def _w(p,o): p.write_text(json.dumps(o),encoding='utf-8'); return p

def _runtime(**k):
    base={'final_decision':'PHASE11_SINGLE_CUSTOMER_RUNTIME_PATH_EVIDENCE_READY','runtime_path_evidence_ready':True,'post_apply_evidence_ready':True,'controlled_apply_recorded':True,'production_traffic_enabled':False,'miner_traffic_allowed':False,'phase11_accepted':False,'db_activation_allowed':False,'mutation_performed':False,'candidate_customer_key':'limited-btc-001','candidate_lane':'btc','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010'}; base.update(k); return base

def _stratum(**k):
    base={'final_decision':'PHASE11_SINGLE_CUSTOMER_STRATUM_TRANSCRIPT_EVIDENCE_READY','stratum_transcript_ready':True,'production_traffic_enabled':False,'miner_traffic_allowed':False,'phase11_accepted':False,'db_activation_allowed':False,'mutation_performed':False,'candidate_customer_key':'limited-btc-001','candidate_lane':'btc','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010'}; base.update(k); return base

def test_ready_and_failure_matrix(tmp_path):
    rp=_w(tmp_path/'r.json',_runtime()); sp=_w(tmp_path/'s.json',_stratum())
    rs=svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rp,stratum_transcript_evidence_json=sp,runtime_path_evidence_json_sha256=hashlib.sha256(rp.read_bytes()).hexdigest(),stratum_transcript_evidence_json_sha256=hashlib.sha256(sp.read_bytes()).hexdigest())
    assert rs['visibility_bundle_ready'] is True
    assert svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=tmp_path/'x',stratum_transcript_evidence_json=sp)['final_decision']=='BLOCKED'
    (tmp_path/'inv.json').write_text('{',encoding='utf-8')
    assert 'runtime_path_evidence_invalid' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=tmp_path/'inv.json',stratum_transcript_evidence_json=sp)['blockers']
    assert 'runtime_path_evidence_hash_mismatch' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rp,runtime_path_evidence_json_sha256='x',stratum_transcript_evidence_json=sp)['blockers']
    assert 'runtime_path_evidence_not_ready' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=_w(tmp_path/'r2.json',_runtime(final_decision='BLOCKED')),stratum_transcript_evidence_json=sp)['blockers']
    assert 'runtime_path_evidence_scope_mismatch' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=_w(tmp_path/'r3.json',_runtime(candidate_lane='zec')),stratum_transcript_evidence_json=sp)['blockers']
    assert 'runtime_path_evidence_safety_boundary_open' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=_w(tmp_path/'r4.json',_runtime(production_traffic_enabled=True)),stratum_transcript_evidence_json=sp)['blockers']
    assert 'stratum_transcript_evidence_missing' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rp,stratum_transcript_evidence_json=tmp_path/'m.json')['blockers']
    assert 'stratum_transcript_evidence_invalid' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rp,stratum_transcript_evidence_json=tmp_path/'inv.json')['blockers']
    assert 'stratum_transcript_evidence_hash_mismatch' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rp,stratum_transcript_evidence_json=sp,stratum_transcript_evidence_json_sha256='x')['blockers']
    assert 'stratum_transcript_evidence_not_ready' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rp,stratum_transcript_evidence_json=_w(tmp_path/'s2.json',_stratum(final_decision='BLOCKED')))['blockers']
    assert 'stratum_transcript_evidence_scope_mismatch' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rp,stratum_transcript_evidence_json=_w(tmp_path/'s3.json',_stratum(candidate_lane='zec')))['blockers']
    assert 'stratum_transcript_evidence_safety_boundary_open' in svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rp,stratum_transcript_evidence_json=_w(tmp_path/'s4.json',_stratum(miner_traffic_allowed=True)))['blockers']


def test_cli_smoke(tmp_path):
    rp=_w(tmp_path/'r.json',_runtime()); sp=_w(tmp_path/'s.json',_stratum())
    h1=hashlib.sha256(rp.read_bytes()).hexdigest(); h2=hashlib.sha256(sp.read_bytes()).hexdigest()
    r=CliRunner().invoke(app,['production','single-customer-visibility-bundle','--runtime-path-evidence-json',str(rp),'--runtime-path-evidence-json-sha256',h1,'--stratum-transcript-evidence-json',str(sp),'--stratum-transcript-evidence-json-sha256',h2,'--output','json','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0
    rh=CliRunner().invoke(app,['production','single-customer-visibility-bundle','--runtime-path-evidence-json',str(rp),'--stratum-transcript-evidence-json',str(sp),'--output','human','--config','configs/mpf.example.yaml'])
    assert rh.exit_code==0
