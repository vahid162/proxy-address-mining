import json
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_visibility_bundle_service as svc

def _cfg(): return load_config(Path('configs/mpf.example.yaml'))

def test_ready_and_blocked(tmp_path):
    rt=tmp_path/'r.json'; st=tmp_path/'s.json'
    rt.write_text(json.dumps({'runtime_path_evidence_ready':True,'post_apply_evidence_ready':True,'final_decision':'R'}))
    st.write_text(json.dumps({'stratum_transcript_ready':True,'final_decision':'S'}))
    r=svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rt,stratum_transcript_evidence_json=st)
    assert r['visibility_bundle_ready'] is True
    st.write_text(json.dumps({'stratum_transcript_ready':False}))
    r2=svc.build_phase11_single_customer_visibility_bundle_report(_cfg(),runtime_path_evidence_json=rt,stratum_transcript_evidence_json=st)
    assert r2['final_decision']=='BLOCKED'
