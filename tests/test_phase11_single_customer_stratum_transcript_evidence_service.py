import json
from pathlib import Path

from mpf.config import load_config
from mpf.services import phase11_single_customer_stratum_transcript_evidence_service as svc


def _cfg():
    return load_config(Path('configs/mpf.example.yaml'))


def _write(path: Path, obj):
    path.write_text(json.dumps(obj), encoding='utf-8')
    return path


def test_valid_transcript_ready(tmp_path):
    p=_write(tmp_path/'ok.json',{'connect_port':20101,'worker_name':'limited-btc-001.worker-001','messages':[{'direction':'rx','id':1,'result_present':True},{'direction':'rx','id':2,'result':True},{'direction':'rx','method':'mining.notify'}]})
    r=svc.build_phase11_single_customer_stratum_transcript_evidence_report(_cfg(),transcript_json=p)
    assert r['final_decision'].endswith('READY')


def test_missing_invalid_non_object_and_scope_block(tmp_path):
    r=svc.build_phase11_single_customer_stratum_transcript_evidence_report(_cfg(),transcript_json=tmp_path/'missing.json')
    assert 'transcript_missing' in r['blockers']
    bad=tmp_path/'bad.json'; bad.write_text('{',encoding='utf-8')
    rb=svc.build_phase11_single_customer_stratum_transcript_evidence_report(_cfg(),transcript_json=bad)
    assert 'transcript_invalid' in rb['blockers']
    arr=_write(tmp_path/'arr.json',[1,2])
    ra=svc.build_phase11_single_customer_stratum_transcript_evidence_report(_cfg(),transcript_json=arr)
    assert 'transcript_invalid' in ra['blockers']
    ok=_write(tmp_path/'ok2.json',{'connect_port':20101,'worker_name':'limited-btc-001.w','messages':[{'direction':'rx','id':1,'result_present':True},{'direction':'rx','id':2,'result':True},{'direction':'rx','method':'mining.set_difficulty'}]})
    rs=svc.build_phase11_single_customer_stratum_transcript_evidence_report(_cfg(),transcript_json=ok,candidate_lane='zec')
    assert 'candidate_scope_mismatch' in rs['blockers']


def test_port_and_missing_primitives_block(tmp_path):
    p=_write(tmp_path/'x.json',{'connect_port':20001,'worker_name':'limited-btc-001.w','messages':[{'direction':'rx','id':1,'result_present':True}]})
    r=svc.build_phase11_single_customer_stratum_transcript_evidence_report(_cfg(),transcript_json=p)
    assert 'transcript_port_mismatch' in r['blockers']
    assert 'missing_authorize' in r['blockers']
    assert 'missing_set_difficulty_or_notify' in r['blockers']
    for f in ('production_traffic_enabled','miner_traffic_allowed','phase11_accepted','db_activation_allowed','mutation_performed'):
        assert r[f] is False
