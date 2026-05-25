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


def test_forwarder_signal_without_customer_key_but_with_backend_pool_correlation(tmp_path, monkeypatch):
    p = tmp_path / "post.json"
    p.write_text(json.dumps({"final_decision":"PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY","controlled_apply_recorded":True,"post_apply_evidence_ready":True,"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,"has_20101_chain":True,"has_20101_ref":True,"candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","blockers":[],"warnings":[]}))
    conn = tmp_path / "conn.txt"; conn.write_text("tcp SYN_SENT src=172.18.0.2 dport=20101 [UNREPLIED] src=172.18.0.3 sport=60010")
    fwd = tmp_path / "fwd.txt"; fwd.write_text("213.195.38.240:35189 - 172.18.0.3:60010\n213.195.38.240:35189 <-> bitcoin.viabtc.io:3333\n")
    bridge = tmp_path / "bridge.txt"; bridge.write_text("127.0.0.1:20170 -> 172.18.0.3:60010")
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k: customer_read_service.CustomerList(ok=True,message='ok',customers=[_row()]))
    r = svc.build_phase11_single_customer_runtime_path_evidence_report(_cfg(), post_apply_evidence_json=p, post_apply_evidence_json_sha256=sha, conntrack_snapshot_file=conn, forwarder_log_file=fwd, bridge_log_file=bridge, operator_confirmed=True, i_understand_runtime_evidence_only=True, i_understand_no_production_traffic_acceptance=True, i_understand_no_miner_traffic_acceptance=True, i_understand_no_db_activation=True, i_confirm_stratum_transcript_required=True, i_confirm_visibility_bundle_required=True, i_confirm_abuse_1h_required_before_customer_traffic=True, i_confirm_restart_container_order_required_before_limited_acceptance=True)
    assert r["forwarder_pool_seen"] is True
    assert r["conntrack_assured_seen"] is False
    assert r["final_decision"] == "BLOCKED"
    assert "missing_conntrack_assured_runtime_signal" in r["blockers"]


def test_default_expected_version_uses_package_version(tmp_path, monkeypatch):
    p = tmp_path / "post.json"
    p.write_text(json.dumps({"final_decision":"PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY","controlled_apply_recorded":True,"post_apply_evidence_ready":True,"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,"has_20101_chain":True,"has_20101_ref":True,"candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","blockers":[],"warnings":[]}))
    conn = tmp_path / "conn.txt"; conn.write_text("tcp ASSURED dport=20101 src=172.18.0.3 sport=60010")
    fwd = tmp_path / "fwd.txt"; fwd.write_text("213.195.38.240:35189 - 172.18.0.3:60010\n213.195.38.240:35189 <-> bitcoin.viabtc.io:3333\n")
    bridge = tmp_path / "bridge.txt"; bridge.write_text("127.0.0.1:20170 -> 172.18.0.3:60010")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    monkeypatch.setattr(customer_read_service, 'list_customer_status', lambda *a, **k: customer_read_service.CustomerList(ok=True, message='ok', customers=[_row()]))
    r = svc.build_phase11_single_customer_runtime_path_evidence_report(_cfg(), post_apply_evidence_json=p, post_apply_evidence_json_sha256=sha, conntrack_snapshot_file=conn, forwarder_log_file=fwd, bridge_log_file=bridge, operator_confirmed=True, i_understand_runtime_evidence_only=True, i_understand_no_production_traffic_acceptance=True, i_understand_no_miner_traffic_acceptance=True, i_understand_no_db_activation=True, i_confirm_stratum_transcript_required=True, i_confirm_visibility_bundle_required=True, i_confirm_abuse_1h_required_before_customer_traffic=True, i_confirm_restart_container_order_required_before_limited_acceptance=True)
    from mpf import __version__
    assert r["expected_version"] == __version__


def test_ready_with_assured_and_exact_scope_even_without_customer_key_in_forwarder(tmp_path, monkeypatch):
    p = tmp_path / "post.json"
    p.write_text(json.dumps({"final_decision":"PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY","controlled_apply_recorded":True,"post_apply_evidence_ready":True,"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,"has_20101_chain":True,"has_20101_ref":True,"candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","blockers":[],"warnings":[]}))
    conn = tmp_path / "conn.txt"; conn.write_text("tcp ASSURED dport=20101 src=172.18.0.3 sport=60010")
    fwd = tmp_path / "fwd.txt"; fwd.write_text("213.195.38.240:35189 - 172.18.0.3:60010\n213.195.38.240:35189 <-> bitcoin.viabtc.io:3333\n")
    bridge = tmp_path / "bridge.txt"; bridge.write_text("127.0.0.1:20170 -> 172.18.0.3:60010")
    live = tmp_path / "live.txt"
    live.write_text(":MPFC_20001 - [0:0]\n:MPFC_20101 - [0:0]\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20001 -m comment --comment mpf:canary-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20101 -m comment --comment mpf:limited-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m connlimit --connlimit-above 10 -m comment --comment mpf:limited-btc-001:customer_connlimit_reject -j REJECT\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m hashlimit --hashlimit-upto 100/min --hashlimit-burst 100 --hashlimit-mode srcip --hashlimit-name x -m comment --comment mpf:limited-btc-001:customer_hashlimit_reject -j REJECT")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    monkeypatch.setattr(customer_read_service, 'list_customer_status', lambda *a, **k: customer_read_service.CustomerList(ok=True, message='ok', customers=[_row()]))
    r = svc.build_phase11_single_customer_runtime_path_evidence_report(_cfg(), post_apply_evidence_json=p, post_apply_evidence_json_sha256=sha, live_snapshot_file=live, conntrack_snapshot_file=conn, forwarder_log_file=fwd, bridge_log_file=bridge, operator_confirmed=True, i_understand_runtime_evidence_only=True, i_understand_no_production_traffic_acceptance=True, i_understand_no_miner_traffic_acceptance=True, i_understand_no_db_activation=True, i_confirm_stratum_transcript_required=True, i_confirm_visibility_bundle_required=True, i_confirm_abuse_1h_required_before_customer_traffic=True, i_confirm_restart_container_order_required_before_limited_acceptance=True)
    assert r["runtime_path_evidence_ready"] is True
    assert r["final_decision"] == "PHASE11_SINGLE_CUSTOMER_RUNTIME_PATH_EVIDENCE_READY"
