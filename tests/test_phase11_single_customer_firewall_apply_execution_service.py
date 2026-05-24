from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
from typer.testing import CliRunner
from mpf import __version__
from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_firewall_apply_execution_service import build_phase11_single_customer_firewall_apply_execution_report

def _cfg(): return load_config(Path('configs/mpf.example.yaml'))
def _rows(*r): return customer_read_service.CustomerList(ok=True,message='ok',customers=list(r))
def _staged(status='paused',lane='btc',port=20101,key='limited-btc-001'): return SimpleNamespace(customer_key=key,lane=lane,port=port,status=status)
def _pre(): return '*nat\n:MPF_NAT_PRE - [0:0]\n-A MPF_NAT_PRE -p tcp -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" --dport 20001 -j DNAT --to-destination 172.18.0.3:60010\n*filter\n:MPFC_20001 - [0:0]\n'
def _post(ok=True,extra=''):
    base='*nat\n:MPF_NAT_PRE - [0:0]\n-A MPF_NAT_PRE -p tcp -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" --dport 20001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" --dport 20101 -j DNAT --to-destination 172.18.0.3:60010\n*filter\n:MPFC_20001 - [0:0]\n:MPFC_20101 - [0:0]\n'
    if not ok: base='*nat\n:MPF_NAT_PRE - [0:0]\n*filter\n:MPFC_20001 - [0:0]\n'
    return base+extra

def _gate(**u):
    d={"component":"phase11_single_customer_firewall_apply_gate","expected_version":"0.1.203","repository_version":"0.1.203","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","phase11e_firewall_apply_gate_ready":True,"apply_gate_package_generated":True,"firewall_apply_execution_allowed":False,"firewall_apply_allowed":False,"nat_apply_allowed":False,"iptables_restore_authorized":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"limited_onboarding_allowed":False,"db_mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"conntrack_mutation_performed":False,"docker_mutation_performed":False,"mutation_performed":False,"firewall_plan_gate_json_sha256":"0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438","plan_summary_sha256":"7e971dd7e635f46bde2b568ecf133d6ec9ddd1a211386591a95df97d2ee18a41","live_firewall_summary":{"canary_nat_chain_present":True,"canary_customer_chain_present":True,"canary_20001_nat_rule_count":1,"canary_20001_exact_target_rule_count":1,"canary_20001_loopback_rule_count":0,"canary_comment_present":True,"limited_20101_chain_present":False,"limited_20101_dnat_present":False,"limited_customer_reference_present":False},"blockers":[],"warnings":[],"next_required_step":"phase11e_single_customer_firewall_apply_execution_pr","final_decision":"PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_GATE_READY"}
    d.update(u); return d

def _write(tmp,name,text): p=tmp/name; p.write_text(text); return p
def _kw(tmp,**u):
    g=_write(tmp,'gate.json',json.dumps(_gate())); pre=_write(tmp,'pre.txt',_pre()); rb=_write(tmp,'rb.txt','x'); rs=tmp/'rp'; rs.mkdir(exist_ok=True)
    d=dict(expected_version=__version__,apply_gate_json=g,operator='vahid',reason='ok',operator_confirmed=True,i_understand_single_customer_apply_execution=True,i_understand_firewall_nat_apply_will_mutate_host_in_execute_mode=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_confirm_pre_apply_snapshot_taken=True,i_confirm_restore_point_created=True,i_confirm_operator_lock_acquired=True,i_confirm_rollback_artifact_created=True,i_confirm_canary_20001_must_be_preserved=True,i_confirm_post_apply_verification_required=True,i_confirm_runtime_path_evidence_required_after_apply=True,i_confirm_abuse_1h_evidence_required_before_customer_traffic=True,i_confirm_restart_container_order_evidence_required_before_limited_acceptance=True,live_snapshot_file=pre,pre_apply_snapshot_file=pre,rollback_artifact_file=rb,restore_point_path=rs,operator_lock_id='lock-1',execute=False)
    d.update(u); return d

def _run(tmp,mp,**u): mp.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows(_staged())); return build_phase11_single_customer_firewall_apply_execution_report(_cfg(),**_kw(tmp,**u))

def test_01_dry_run_ready(tmp_path,monkeypatch): assert _run(tmp_path,monkeypatch)['final_decision']=='PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTION_PACKAGE_READY'
def test_02_missing_gate(tmp_path,monkeypatch): assert 'apply_gate_json_missing' in _run(tmp_path,monkeypatch,apply_gate_json=tmp_path/'x')['blockers']
def test_03_invalid_gate(tmp_path,monkeypatch): p=_write(tmp_path,'bad.json','{'); assert 'apply_gate_json_invalid' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
def test_04_gate_not_ready(tmp_path,monkeypatch): p=_write(tmp_path,'g.json',json.dumps(_gate(final_decision='X'))); assert 'apply_gate_not_ready' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
def test_05_gate_file_hash_mismatch(tmp_path,monkeypatch): assert 'apply_gate_json_file_hash_mismatch' in _run(tmp_path,monkeypatch,apply_gate_json_file_sha256='x')['blockers']
def test_06_embedded_plan_hash_mismatch(tmp_path,monkeypatch): p=_write(tmp_path,'g.json',json.dumps(_gate(firewall_plan_gate_json_sha256='x'))); assert 'embedded_firewall_plan_gate_hash_mismatch' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
def test_07_embedded_summary_hash_mismatch(tmp_path,monkeypatch): p=_write(tmp_path,'g.json',json.dumps(_gate(plan_summary_sha256='x'))); assert 'embedded_plan_summary_hash_mismatch' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
def test_08_safety_open(tmp_path,monkeypatch): p=_write(tmp_path,'g.json',json.dumps(_gate(firewall_apply_allowed=True))); assert 'apply_gate_not_ready' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
def test_09_mutation_detected(tmp_path,monkeypatch): p=_write(tmp_path,'g.json',json.dumps(_gate(mutation_performed=True))); assert 'apply_gate_not_ready' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
def test_10_live_summary_mismatch(tmp_path,monkeypatch): g=_gate(); g['live_firewall_summary']['canary_nat_chain_present']=False; p=_write(tmp_path,'g.json',json.dumps(g)); assert 'apply_gate_live_summary_mismatch' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
def test_11_wrong_scope(tmp_path,monkeypatch): p=_write(tmp_path,'g.json',json.dumps(_gate(candidate_lane='zec'))); assert 'apply_gate_not_ready' in _run(tmp_path,monkeypatch,apply_gate_json=p)['blockers']
def test_12_missing_confirm(tmp_path,monkeypatch): assert 'operator_not_confirmed' in _run(tmp_path,monkeypatch,operator_confirmed=False)['blockers']
def test_13_db_fail(tmp_path,monkeypatch): monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k: customer_read_service.CustomerList(ok=False,message='x',customers=[])); assert 'db_read_failed' in build_phase11_single_customer_firewall_apply_execution_report(_cfg(),**_kw(tmp_path))['blockers']
def test_14_missing_customer(tmp_path,monkeypatch): monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows()); assert 'staged_customer_missing' in build_phase11_single_customer_firewall_apply_execution_report(_cfg(),**_kw(tmp_path))['blockers']
def test_15_not_paused(tmp_path,monkeypatch): monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows(_staged(status='active'))); assert 'staged_customer_not_paused' in build_phase11_single_customer_firewall_apply_execution_report(_cfg(),**_kw(tmp_path))['blockers']
def test_16_port_collision(tmp_path,monkeypatch): monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows(_staged(),_staged(key='x'))); assert 'candidate_port_collision' in build_phase11_single_customer_firewall_apply_execution_report(_cfg(),**_kw(tmp_path))['blockers']
def test_17_live_20101_exists(tmp_path,monkeypatch): p=_write(tmp_path,'pre2.txt',_pre()+'-A MPF_NAT_PRE -p tcp --dport 20101 -j DNAT --to-destination 172.18.0.3:60010\n'); assert 'live_20101_rule_already_exists' in _run(tmp_path,monkeypatch,live_snapshot_file=p)['blockers']
def test_18_live_canary_missing(tmp_path,monkeypatch): p=_write(tmp_path,'pre3.txt','*nat\n'); assert 'live_canary_20001_artifact_missing_or_ambiguous' in _run(tmp_path,monkeypatch,live_snapshot_file=p)['blockers']
def test_19_dry_never_auth(tmp_path,monkeypatch): assert _run(tmp_path,monkeypatch)['iptables_restore_authorized'] is False
def test_20_dry_no_mutation(tmp_path,monkeypatch): assert _run(tmp_path,monkeypatch)['mutation_performed'] is False
def test_21_ci_block(tmp_path,monkeypatch): monkeypatch.setenv('CI','1'); assert 'execute_forbidden_in_ci' in _run(tmp_path,monkeypatch,execute=True)['blockers']
def test_22_env_block(tmp_path,monkeypatch): assert 'apply_execution_environment_not_confirmed' in _run(tmp_path,monkeypatch,execute=True)['blockers']
def test_23_missing_pre_file(tmp_path,monkeypatch): assert 'pre_apply_snapshot_file_missing' in _run(tmp_path,monkeypatch,execute=True,pre_apply_snapshot_file=tmp_path/'x')['blockers']
def test_24_missing_rb_file(tmp_path,monkeypatch): assert 'rollback_artifact_file_missing' in _run(tmp_path,monkeypatch,execute=True,rollback_artifact_file=tmp_path/'x')['blockers']
def test_25_missing_restore(tmp_path,monkeypatch): assert 'restore_point_missing' in _run(tmp_path,monkeypatch,execute=True,restore_point_path=tmp_path/'x')['blockers']
def test_26_missing_lock(tmp_path,monkeypatch): assert 'operator_lock_missing' in _run(tmp_path,monkeypatch,execute=True,operator_lock_id='')['blockers']
def test_27_exec_order(tmp_path,monkeypatch):
    monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_EXECUTION','allow'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_TARGET','limited-btc-001:btc:20101:172.18.0.3:60010'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_I_UNDERSTAND_HOST_FIREWALL_MUTATION','allow')
    calls=[]
    def f(cmd,**k): calls.append(cmd); return SimpleNamespace(returncode=0,stdout=_post())
    monkeypatch.setattr('mpf.services.phase11_single_customer_firewall_apply_execution_service.subprocess.run',f)
    _run(tmp_path,monkeypatch,execute=True)
    assert calls[0][0:2]==['iptables-restore','--test'] and calls[1][0:2]==['iptables-restore','--noflush']
def test_28_exec_success_needs_post_verify(tmp_path,monkeypatch):
    monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_EXECUTION','allow'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_TARGET','limited-btc-001:btc:20101:172.18.0.3:60010'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_I_UNDERSTAND_HOST_FIREWALL_MUTATION','allow')
    seq=[SimpleNamespace(returncode=0,stdout=''),SimpleNamespace(returncode=0,stdout=''),SimpleNamespace(returncode=0,stdout=_post())]
    monkeypatch.setattr('mpf.services.phase11_single_customer_firewall_apply_execution_service.subprocess.run',lambda *a,**k: seq.pop(0))
    assert _run(tmp_path,monkeypatch,execute=True)['final_decision']=='PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTED_PENDING_REVIEW'
def test_29_exec_apply_fail(tmp_path,monkeypatch):
    monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_EXECUTION','allow'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_TARGET','limited-btc-001:btc:20101:172.18.0.3:60010'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_I_UNDERSTAND_HOST_FIREWALL_MUTATION','allow')
    seq=[SimpleNamespace(returncode=1,stdout='')]
    monkeypatch.setattr('mpf.services.phase11_single_customer_firewall_apply_execution_service.subprocess.run',lambda *a,**k: seq.pop(0))
    assert _run(tmp_path,monkeypatch,execute=True)['final_decision']=='FAILED_APPLY_EXECUTION'
def test_30_post_verify_fail(tmp_path,monkeypatch):
    monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_EXECUTION','allow'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_TARGET','limited-btc-001:btc:20101:172.18.0.3:60010'); monkeypatch.setenv('MPF_PHASE11_SINGLE_CUSTOMER_APPLY_I_UNDERSTAND_HOST_FIREWALL_MUTATION','allow')
    seq=[SimpleNamespace(returncode=0,stdout=''),SimpleNamespace(returncode=0,stdout=''),SimpleNamespace(returncode=0,stdout=_post(False))]
    monkeypatch.setattr('mpf.services.phase11_single_customer_firewall_apply_execution_service.subprocess.run',lambda *a,**k: seq.pop(0))
    assert _run(tmp_path,monkeypatch,execute=True)['final_decision']=='FAILED_POST_APPLY_VERIFICATION'
def test_31_cli_json(tmp_path,monkeypatch):
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows(_staged())); g=_write(tmp_path,'g.json',json.dumps(_gate())); pre=_write(tmp_path,'pre.txt',_pre()); rb=_write(tmp_path,'rb.txt','x'); rs=tmp_path/'rp'; rs.mkdir();
    r=CliRunner().invoke(app,['production','single-customer-firewall-apply-execute','--apply-gate-json',str(g),'--operator','vahid','--reason','ok','--operator-confirmed','--i-understand-single-customer-apply-execution','--i-understand-firewall-nat-apply-will-mutate-host-in-execute-mode','--i-understand-no-production-traffic-acceptance','--i-understand-no-miner-traffic-acceptance','--i-confirm-pre-apply-snapshot-taken','--i-confirm-restore-point-created','--i-confirm-operator-lock-acquired','--i-confirm-rollback-artifact-created','--i-confirm-canary-20001-must-be-preserved','--i-confirm-post-apply-verification-required','--i-confirm-runtime-path-evidence-required-after-apply','--i-confirm-abuse-1h-evidence-required-before-customer-traffic','--i-confirm-restart-container-order-evidence-required-before-limited-acceptance','--pre-apply-snapshot-file',str(pre),'--rollback-artifact-file',str(rb),'--restore-point-path',str(rs),'--operator-lock-id','lock-1','--live-snapshot-file',str(pre),'--output','json','--config','configs/mpf.example.yaml']); assert r.exit_code==0
def test_32_cli_human(tmp_path,monkeypatch):
    monkeypatch.setattr(customer_read_service,'list_customer_status',lambda *a,**k:_rows(_staged())); g=_write(tmp_path,'g2.json',json.dumps(_gate())); pre=_write(tmp_path,'pre2.txt',_pre()); rb=_write(tmp_path,'rb2.txt','x'); rs=tmp_path/'rp2'; rs.mkdir();
    r=CliRunner().invoke(app,['production','single-customer-firewall-apply-execute','--apply-gate-json',str(g),'--operator','vahid','--reason','ok','--operator-confirmed','--i-understand-single-customer-apply-execution','--i-understand-firewall-nat-apply-will-mutate-host-in-execute-mode','--i-understand-no-production-traffic-acceptance','--i-understand-no-miner-traffic-acceptance','--i-confirm-pre-apply-snapshot-taken','--i-confirm-restore-point-created','--i-confirm-operator-lock-acquired','--i-confirm-rollback-artifact-created','--i-confirm-canary-20001-must-be-preserved','--i-confirm-post-apply-verification-required','--i-confirm-runtime-path-evidence-required-after-apply','--i-confirm-abuse-1h-evidence-required-before-customer-traffic','--i-confirm-restart-container-order-evidence-required-before-limited-acceptance','--pre-apply-snapshot-file',str(pre),'--rollback-artifact-file',str(rb),'--restore-point-path',str(rs),'--operator-lock-id','lock-1','--live-snapshot-file',str(pre),'--output','human','--config','configs/mpf.example.yaml']); assert r.exit_code==0
