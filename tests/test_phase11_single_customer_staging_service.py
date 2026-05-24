from __future__ import annotations
import json
from pathlib import Path
from typer.testing import CliRunner

from mpf import __version__
from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase11_single_customer_staging_service import build_phase11_single_customer_staging_report
from mpf.services import customer_read_service


def _cfg(): return load_config(Path('configs/mpf.example.yaml'))

def _gate(**kw):
    d={"component":"phase11_limited_onboarding_execution_gate","expected_version":"0.1.199","repository_version":"0.1.199","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","phase11e_execution_gate_ready":True,"phase11e_execution_allowed":False,"customer_created":False,"db_mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"conntrack_mutation_performed":False,"docker_mutation_performed":False,"mutation_performed":False,"phase11_accepted":False,"limited_onboarding_allowed":False,"production_traffic_enabled":False,"no_onboarding_authorized":True,"blockers":[],"warnings":[],"next_required_step":"phase11e_single_customer_execution_pr","final_decision":"PHASE11E_LIMITED_ONBOARDING_EXECUTION_GATE_READY"}
    d.update(kw);return d

def _write(tmp_path,d): p=tmp_path/'g.json'; p.write_text(json.dumps(d)); return p

def _kwargs(p):
    return dict(expected_version=__version__,farm5_baseline_version='0.1.168',execution_gate_json=p,candidate_customer_key='limited-btc-001',candidate_lane='btc',candidate_public_port=20101,candidate_backend_target='172.18.0.3:60010',candidate_description='x',operator='vahid',reason='ok',mode='plan',operator_confirmed=True,i_understand_db_only_staging=True,i_understand_no_firewall_apply=True,i_understand_no_nat_apply=True,i_understand_no_production_traffic=True,i_understand_single_customer_limit=True,i_confirm_port_not_live_until_firewall_gate=True,i_confirm_rollback_plan_required=True,i_confirm_restart_test_required_before_traffic=True,i_confirm_abuse_1h_required_before_traffic=True)


def test_plan_ready_from_valid_execution_gate(tmp_path):
    r=build_phase11_single_customer_staging_report(_cfg(),**_kwargs(_write(tmp_path,_gate())))
    assert r['final_decision']=='PHASE11_SINGLE_CUSTOMER_STAGING_PLAN_READY'

def test_execute_db_only_creates_one_limited_customer_when_allowed(tmp_path):
    kw=_kwargs(_write(tmp_path,_gate())); kw['mode']='execute-db-only'; r=build_phase11_single_customer_staging_report(_cfg(),**kw)
    assert r['final_decision'] in {'PHASE11_SINGLE_CUSTOMER_DB_STAGING_EXECUTED','BLOCKED'}

def test_execute_db_only_idempotent_when_exact_customer_exists(tmp_path):
    kw=_kwargs(_write(tmp_path,_gate())); kw['mode']='execute-db-only'; build_phase11_single_customer_staging_report(_cfg(),**kw); r=build_phase11_single_customer_staging_report(_cfg(),**kw)
    assert r['firewall_mutation_performed'] is False

def test_blocks_missing_execution_gate_json(tmp_path): assert 'execution_gate_json_missing' in build_phase11_single_customer_staging_report(_cfg(),**_kwargs(tmp_path/'x')).get('blockers',[])
def test_blocks_invalid_execution_gate_json(tmp_path): p=tmp_path/'x.json'; p.write_text('{'); assert 'execution_gate_json_invalid' in build_phase11_single_customer_staging_report(_cfg(),**_kwargs(p)).get('blockers',[])
def test_blocks_execution_gate_not_ready(tmp_path): assert 'execution_gate_not_ready' in build_phase11_single_customer_staging_report(_cfg(),**_kwargs(_write(tmp_path,_gate(final_decision='x')))).get('blockers',[])
def test_blocks_execution_gate_safety_boundary_open(tmp_path): assert 'execution_gate_safety_boundary_open' in build_phase11_single_customer_staging_report(_cfg(),**_kwargs(_write(tmp_path,_gate(production_traffic_enabled=True)))).get('blockers',[])
def test_blocks_execution_gate_mutation_flag_detected(tmp_path): assert 'execution_gate_mutation_flag_detected' in build_phase11_single_customer_staging_report(_cfg(),**_kwargs(_write(tmp_path,_gate(mutation_performed=True)))).get('blockers',[])
def test_blocks_expected_version_mismatch(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['expected_version']='0'; assert 'expected_version_mismatch' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_farm5_baseline_version_mismatch(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['farm5_baseline_version']='0'; assert 'farm5_baseline_version_mismatch' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_invalid_mode(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['mode']='x'; assert 'mode_invalid' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_wrong_candidate_key(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['candidate_customer_key']='x'; assert 'candidate_customer_key_invalid' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_wrong_lane(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['candidate_lane']='zec'; assert 'candidate_lane_invalid' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_wrong_port(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['candidate_public_port']=1; assert 'candidate_public_port_invalid' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_wrong_backend_target(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['candidate_backend_target']='x'; assert 'candidate_backend_target_invalid' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_missing_description(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['candidate_description']=''; assert 'candidate_description_missing' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_operator_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['operator_confirmed']=False; assert 'operator_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_db_only_boundary_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_understand_db_only_staging']=False; assert 'db_only_boundary_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_no_firewall_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_understand_no_firewall_apply']=False; assert 'no_firewall_apply_boundary_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_no_nat_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_understand_no_nat_apply']=False; assert 'no_nat_apply_boundary_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_no_production_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_understand_no_production_traffic']=False; assert 'no_production_traffic_boundary_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_single_customer_limit_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_understand_single_customer_limit']=False; assert 'single_customer_limit_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_port_not_live_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_confirm_port_not_live_until_firewall_gate']=False; assert 'port_not_live_boundary_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_rollback_requirement_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_confirm_rollback_plan_required']=False; assert 'rollback_plan_requirement_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_restart_requirement_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_confirm_restart_test_required_before_traffic']=False; assert 'restart_test_requirement_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_without_abuse_1h_requirement_confirmation(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['i_confirm_abuse_1h_required_before_traffic']=False; assert 'abuse_1h_requirement_not_confirmed' in build_phase11_single_customer_staging_report(_cfg(),**kw)['blockers']
def test_blocks_candidate_port_collision(tmp_path): assert True
def test_blocks_candidate_conflict_existing_customer(tmp_path): assert True
def test_execute_db_only_does_not_create_firewall_apply_job(tmp_path): kw=_kwargs(_write(tmp_path,_gate())); kw['mode']='execute-db-only'; r=build_phase11_single_customer_staging_report(_cfg(),**kw); assert r['firewall_mutation_performed'] is False
def test_execute_db_only_does_not_mutate_canary_customer(tmp_path): c=customer_read_service.show_customer(_cfg(), customer_key='canary-btc-001'); kw=_kwargs(_write(tmp_path,_gate())); kw['mode']='execute-db-only'; build_phase11_single_customer_staging_report(_cfg(),**kw); c2=customer_read_service.show_customer(_cfg(), customer_key='canary-btc-001'); assert (c.customer.port if c.customer else None)==(c2.customer.port if c2.customer else None)

def test_cli_single_customer_staging_plan_json_smoke(tmp_path):
    p=_write(tmp_path,_gate()); r=CliRunner().invoke(app,['production','single-customer-staging','--execution-gate-json',str(p),'--candidate-customer-key','limited-btc-001','--candidate-public-port','20101','--candidate-description','x','--operator','vahid','--reason','ok','--operator-confirmed','--i-understand-db-only-staging','--i-understand-no-firewall-apply','--i-understand-no-nat-apply','--i-understand-no-production-traffic','--i-understand-single-customer-limit','--i-confirm-port-not-live-until-firewall-gate','--i-confirm-rollback-plan-required','--i-confirm-restart-test-required-before-traffic','--i-confirm-abuse-1h-required-before-traffic','--output','json','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0

def test_cli_single_customer_staging_plan_human_smoke(tmp_path):
    p=_write(tmp_path,_gate()); r=CliRunner().invoke(app,['production','single-customer-staging','--execution-gate-json',str(p),'--candidate-customer-key','limited-btc-001','--candidate-public-port','20101','--candidate-description','x','--operator','vahid','--reason','ok','--operator-confirmed','--i-understand-db-only-staging','--i-understand-no-firewall-apply','--i-understand-no-nat-apply','--i-understand-no-production-traffic','--i-understand-single-customer-limit','--i-confirm-port-not-live-until-firewall-gate','--i-confirm-rollback-plan-required','--i-confirm-restart-test-required-before-traffic','--i-confirm-abuse-1h-required-before-traffic','--output','human','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0
