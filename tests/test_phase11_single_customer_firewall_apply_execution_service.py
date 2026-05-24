from __future__ import annotations
import json, os
from pathlib import Path
from types import SimpleNamespace
from typer.testing import CliRunner
from mpf import __version__
from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_firewall_apply_execution_service import build_phase11_single_customer_firewall_apply_execution_report

def _cfg(): return load_config(Path('configs/mpf.example.yaml'))
def _rows(*rows): return customer_read_service.CustomerList(ok=True,message='ok',customers=list(rows))
def _staged(status='paused',lane='btc',port=20101,key='limited-btc-001'): return SimpleNamespace(id=1,customer_key=key,lane=lane,port=port,status=status)
def _live(): return '*nat\n:MPF_NAT_PRE - [0:0]\n-A MPF_NAT_PRE -p tcp -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" --dport 20001 -j DNAT --to-destination 172.18.0.3:60010\n*filter\n:MPFC_20001 - [0:0]\n'
def _gate(): return {"component":"phase11_single_customer_firewall_apply_gate","expected_version":"0.1.203","repository_version":"0.1.203","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","phase11e_firewall_apply_gate_ready":True,"apply_gate_package_generated":True,"firewall_apply_execution_allowed":False,"firewall_apply_allowed":False,"nat_apply_allowed":False,"iptables_restore_authorized":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"mutation_performed":False,"firewall_plan_gate_json_sha256":"0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438","plan_summary_sha256":"7e971dd7e635f46bde2b568ecf133d6ec9ddd1a211386591a95df97d2ee18a41","blockers":[],"warnings":[],"next_required_step":"phase11e_single_customer_firewall_apply_execution_pr","final_decision":"PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_GATE_READY"}
def _w(tmp,d,name='g.json'): p=tmp/name; p.write_text(json.dumps(d)); return p
def _s(tmp,t): p=tmp/'s.txt'; p.write_text(t); return p

def _run(tmp,mp,**u):
    mp.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows(_staged()))
    d=dict(expected_version=__version__,apply_gate_json=_w(tmp,_gate(),'base.json'),operator='vahid',reason='ok',operator_confirmed=True,i_understand_single_customer_apply_execution=True,i_understand_firewall_nat_apply_will_mutate_host_in_execute_mode=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_confirm_pre_apply_snapshot_taken=True,i_confirm_restore_point_created=True,i_confirm_operator_lock_acquired=True,i_confirm_rollback_artifact_created=True,i_confirm_canary_20001_must_be_preserved=True,i_confirm_post_apply_verification_required=True,i_confirm_runtime_path_evidence_required_after_apply=True,i_confirm_abuse_1h_evidence_required_before_customer_traffic=True,i_confirm_restart_container_order_evidence_required_before_limited_acceptance=True,live_snapshot_file=_s(tmp,_live()),execute=False)
    d.update(u); return build_phase11_single_customer_firewall_apply_execution_report(_cfg(),**d)

def test_suite(tmp_path,monkeypatch):
    r=_run(tmp_path,monkeypatch); assert r['final_decision']=='PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTION_PACKAGE_READY'
    assert 'apply_gate_json_missing' in _run(tmp_path,monkeypatch,apply_gate_json=tmp_path/'x')['blockers']
    p=tmp_path/'b.json'; p.write_text('{'); assert 'apply_gate_json_invalid' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
    g=_gate(); g['final_decision']='X'; assert 'apply_gate_not_ready' in _run(tmp_path,monkeypatch,apply_gate_json=_w(tmp_path,g,'x1.json'))['blockers']
    g=_gate(); g['plan_summary_sha256']='x'; assert 'apply_gate_hash_mismatch' in _run(tmp_path,monkeypatch,apply_gate_json=_w(tmp_path,g,'x1.json'))['blockers']
    g=_gate(); g['candidate_lane']='zec'; assert 'candidate_scope_invalid' in _run(tmp_path,monkeypatch,apply_gate_json=_w(tmp_path,g,'x1.json'))['blockers']
    assert 'operator_not_confirmed' in _run(tmp_path,monkeypatch,operator_confirmed=False)['blockers']
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k: customer_read_service.CustomerList(ok=False,message='x',customers=[])); assert 'db_read_failed' in build_phase11_single_customer_firewall_apply_execution_report(_cfg(),**_run_defaults(tmp_path))['blockers']

def _run_defaults(tmp):
    return dict(expected_version=__version__,apply_gate_json=_w(tmp,_gate(),'base.json'),operator='vahid',reason='ok',operator_confirmed=True,i_understand_single_customer_apply_execution=True,i_understand_firewall_nat_apply_will_mutate_host_in_execute_mode=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_confirm_pre_apply_snapshot_taken=True,i_confirm_restore_point_created=True,i_confirm_operator_lock_acquired=True,i_confirm_rollback_artifact_created=True,i_confirm_canary_20001_must_be_preserved=True,i_confirm_post_apply_verification_required=True,i_confirm_runtime_path_evidence_required_after_apply=True,i_confirm_abuse_1h_evidence_required_before_customer_traffic=True,i_confirm_restart_container_order_evidence_required_before_limited_acceptance=True,live_snapshot_file=_s(tmp,_live()),execute=False)

def test_execute_and_cli(tmp_path,monkeypatch):
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows(_staged()))
    monkeypatch.setenv('CI','1'); assert 'execute_forbidden_in_ci' in _run(tmp_path,monkeypatch,execute=True)['blockers']; monkeypatch.delenv('CI')
    assert 'apply_execution_environment_not_confirmed' in _run(tmp_path,monkeypatch,execute=True)['blockers']
    calls=[]
    def fr(cmd,**k): calls.append(cmd); return SimpleNamespace(returncode=0,stdout='')
    monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_EXECUTION','allow'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_TARGET','limited-btc-001:btc:20101:172.18.0.3:60010'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_I_UNDERSTAND_HOST_FIREWALL_MUTATION','allow')
    monkeypatch.setattr('mpf.services.phase11_single_customer_firewall_apply_execution_service.subprocess.run',fr)
    rr=_run(tmp_path,monkeypatch,execute=True); assert rr['final_decision']=='PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTED_PENDING_REVIEW'; assert calls[0][1]=='--test' and calls[1][1]=='--noflush'
    runner=CliRunner(); p=_w(tmp_path,_gate()); s=_s(tmp_path,_live())
    cmd=['production','single-customer-firewall-apply-execute','--apply-gate-json',str(p),'--operator','vahid','--reason','ok','--operator-confirmed','--i-understand-single-customer-apply-execution','--i-understand-firewall-nat-apply-will-mutate-host-in-execute-mode','--i-understand-no-production-traffic-acceptance','--i-understand-no-miner-traffic-acceptance','--i-confirm-pre-apply-snapshot-taken','--i-confirm-restore-point-created','--i-confirm-operator-lock-acquired','--i-confirm-rollback-artifact-created','--i-confirm-canary-20001-must-be-preserved','--i-confirm-post-apply-verification-required','--i-confirm-runtime-path-evidence-required-after-apply','--i-confirm-abuse-1h-evidence-required-before-customer-traffic','--i-confirm-restart-container-order-evidence-required-before-limited-acceptance','--live-snapshot-file',str(s),'--output','json','--config','configs/mpf.example.yaml']
    assert runner.invoke(app,cmd).exit_code==0; cmd[-3]='human'; assert runner.invoke(app,cmd).exit_code==0
