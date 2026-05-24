import json
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_stratum_transcript_evidence_service as svc

def _cfg(): return load_config(Path('configs/mpf.example.yaml'))

def test_valid_and_invalid(tmp_path):
    ok=tmp_path/'ok.json'; ok.write_text(json.dumps({'connect_port':20101,'worker_name':'limited-btc-001.worker-001','messages':[{'direction':'rx','id':1},{'direction':'rx','id':2,'result':True},{'direction':'rx','method':'mining.notify'}]}))
    r=svc.build_phase11_single_customer_stratum_transcript_evidence_report(_cfg(),transcript_json=ok)
    assert r['stratum_transcript_ready'] is True
    bad=tmp_path/'bad.json'; bad.write_text(json.dumps({'connect_port':20001,'messages':[]}))
    rb=svc.build_phase11_single_customer_stratum_transcript_evidence_report(_cfg(),transcript_json=bad)
    assert rb['final_decision']=='BLOCKED'
