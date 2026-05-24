from __future__ import annotations
import hashlib, json
from pathlib import Path
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from mpf.config import load_config
from types import SimpleNamespace
from mpf.services import phase11_single_customer_runtime_probe_diagnostics_service as svc, customer_read_service


def _cfg(): return load_config(Path("configs/mpf.example.yaml"))

def _sha(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def _w(p: Path, t: str): p.write_text(t, encoding='utf-8'); return p

def _files(tmp: Path, assured=False):
    post=_w(tmp/'post.json', json.dumps({'final_decision':'PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY','post_apply_evidence_ready':True,'controlled_apply_recorded':True,'production_traffic_enabled':False,'miner_traffic_allowed':False,'phase11_accepted':False,'db_activation_allowed':False,'mutation_performed':False,'candidate_customer_key':'limited-btc-001','candidate_lane':'btc','candidate_public_port':20101,'candidate_backend_target':'172.18.0.3:60010'}))
    live=_w(tmp/'live.txt','-A PREROUTING -p tcp --dport 20001\n-A PREROUTING -p tcp --dport 20101 -j DNAT --to-destination 172.18.0.3:60010\n-A MPFC_20101 -m connlimit\n-A MPFC_20101 -m hashlimit')
    conn='tcp 6 120 SYN_SENT src=172.18.0.2 dst=85.1 dport=20101 [UNREPLIED] src=172.18.0.3 sport=60010'
    if assured: conn='tcp ASSURED dport=20101 src=172.18.0.3 sport=60010'
    connp=_w(tmp/'conn.txt',conn)
    fwd=_w(tmp/'fwd.txt','limited-btc-001 20101 172.18.0.3:60010 127.0.0.1:60010')
    br=_w(tmp/'br.txt','127.0.0.1:20170 -> 172.18.0.3 172.18.0.3:60010')
    return post,live,connp,fwd,br

def _rows(status='paused'):
    c=SimpleNamespace(customer_key="limited-btc-001", lane="btc", port=20101, status=status)
    return customer_read_service.CustomerList(ok=True,message='ok',customers=[c])

def _run(tmp, monkeypatch, assured=False, **u):
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows())
    post,live,conn,fwd,br=_files(tmp,assured)
    kw=dict(expected_version='0.1.207',post_apply_evidence_json=post,post_apply_evidence_json_sha256=_sha(post),live_snapshot_file=live,live_snapshot_sha256=_sha(live),conntrack_snapshot_file=conn,conntrack_snapshot_sha256=_sha(conn),forwarder_log_file=fwd,forwarder_log_sha256=_sha(fwd),bridge_log_file=br,bridge_log_sha256=_sha(br),operator='op',reason='r',operator_confirmed=True,i_understand_probe_diagnostics_only=True,i_understand_no_runtime_acceptance=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True,i_confirm_stratum_transcript_required=True,i_confirm_visibility_bundle_required=True,i_confirm_abuse_1h_required_before_customer_traffic=True,i_confirm_restart_container_order_required_before_limited_acceptance=True)
    kw.update(u)
    return svc.build_phase11_single_customer_runtime_probe_diagnostics_report(_cfg(),**kw)

def test_core(tmp_path, monkeypatch):
    r=_run(tmp_path,monkeypatch); assert r['final_decision'] in ('BLOCKED','PHASE11_SINGLE_CUSTOMER_RUNTIME_PROBE_DIAGNOSTICS_READY_BLOCKED_RUNTIME') and not r['runtime_path_evidence_ready']
    a=_run(tmp_path,monkeypatch,assured=True); assert a['conntrack_assured_seen'] is True

def test_blockers(tmp_path, monkeypatch):
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows('active'))
    post,live,conn,fwd,br=_files(tmp_path)
    bad=svc.build_phase11_single_customer_runtime_probe_diagnostics_report(_cfg(),post_apply_evidence_json=tmp_path/'x.json',post_apply_evidence_json_sha256='x',live_snapshot_file=live,conntrack_snapshot_file=conn,forwarder_log_file=fwd,bridge_log_file=br)
    assert 'post_apply_evidence_json_missing' in bad['blockers']
    post.write_text('{')
    inv=svc.build_phase11_single_customer_runtime_probe_diagnostics_report(_cfg(),post_apply_evidence_json=post,post_apply_evidence_json_sha256='x',live_snapshot_file=live,conntrack_snapshot_file=conn,forwarder_log_file=fwd,bridge_log_file=br)
    assert 'post_apply_evidence_json_invalid' in inv['blockers']

def test_cli_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows())
    post,live,conn,fwd,br=_files(tmp_path)
    runner=CliRunner()
    base=['production','single-customer-runtime-probe-diagnostics','--post-apply-evidence-json',str(post),'--post-apply-evidence-json-sha256',_sha(post),'--live-snapshot-file',str(live),'--conntrack-snapshot-file',str(conn),'--forwarder-log-file',str(fwd),'--bridge-log-file',str(br),'--operator','x','--reason','y','--operator-confirmed','--i-understand-probe-diagnostics-only','--i-understand-no-runtime-acceptance','--i-understand-no-production-traffic-acceptance','--i-understand-no-miner-traffic-acceptance','--i-understand-no-db-activation','--i-confirm-stratum-transcript-required','--i-confirm-visibility-bundle-required','--i-confirm-abuse-1h-required-before-customer-traffic','--i-confirm-restart-container-order-required-before-limited-acceptance']
    assert runner.invoke(app,base+['--output','json','--config','configs/mpf.example.yaml']).exit_code==0
    assert runner.invoke(app,base+['--output','human','--config','configs/mpf.example.yaml']).exit_code==0
