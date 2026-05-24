import json
from pathlib import Path

from typer.testing import CliRunner

from mpf import __version__
from mpf.interfaces.cli import app
from mpf.services.phase11_limited_onboarding_gate_service import build_phase11_limited_onboarding_gate_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path("configs/mpf.example.yaml"))


def _base():
    return {"component":"phase11_canary_acceptance_decision","expected_version":"0.1.197","repository_version":"0.1.197","farm5_baseline_version":"0.1.168","customer_key":"canary-btc-001","lane":"btc","public_port":20001,"backend_target":"172.18.0.3:60010","archive_sha256_expected":"x","archive_sha256_actual":"x","operator":"vahid","phase11d_canary_accepted":True,"phase11_accepted":False,"limited_onboarding_allowed":False,"production_traffic_enabled":False,"no_onboarding_authorized":True,"mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"conntrack_mutation_performed":False,"docker_mutation_performed":False,"db_mutation_performed":False,"accepted_evidence_summary":{"runtime_path_final_decision":"RUNTIME_PATH_EVIDENCE_READY","visibility_bundle_final_decision":"VISIBILITY_READY","acceptance_review_final_decision":"ACCEPTANCE_REVIEW_READY","conntrack_assured":True,"forwarder_pool_seen":True,"bridge_loopback_seen":True,"stratum_subscribe_ok":True,"stratum_authorize_ok":True,"stratum_set_difficulty_seen":True,"stratum_notify_seen":True},"blockers":[],"warnings":[],"next_required_step":"phase11e_limited_onboarding_gate_design","final_decision":"CANARY_ACCEPTANCE_DECISION_ACCEPTED"}


def _write(tmp_path, data):
    p=tmp_path/'decision.json'; p.write_text(json.dumps(data), encoding='utf-8'); return p


def _call(path, **kw):
    args = dict(expected_version=__version__, farm5_baseline_version='0.1.168', canary_acceptance_decision_json=path, operator='vahid', reason='ok', operator_confirmed=True, i_understand_no_real_customer_onboarding_yet=True, i_understand_no_production_traffic_yet=True, i_understand_phase11e_requires_separate_execution_gate=True)
    args.update(kw)
    return build_phase11_limited_onboarding_gate_report(_cfg(), **args)


def test_phase11e_limited_onboarding_gate_ready_from_valid_canary_decision(tmp_path):
    r=_call(_write(tmp_path,_base())); assert r['final_decision']=='PHASE11E_LIMITED_ONBOARDING_GATE_READY'

def test_blocks_missing_decision_json(tmp_path):
    r=_call(tmp_path/'none.json'); assert 'canary_acceptance_decision_json_missing' in r['blockers']

def test_blocks_invalid_decision_json(tmp_path):
    p=tmp_path/'x.json'; p.write_text('{'); r=_call(p); assert 'canary_acceptance_decision_json_invalid' in r['blockers']

def test_blocks_when_canary_decision_not_accepted(tmp_path):
    d=_base(); d['final_decision']='BLOCKED'; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_decision_not_accepted' in r['blockers']

def test_blocks_hash_mismatch(tmp_path):
    d=_base(); d['archive_sha256_actual']='y'; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_hash_mismatch' in r['blockers']

def test_blocks_scope_mismatch(tmp_path):
    d=_base(); d['customer_key']='x'; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_scope_mismatch' in r['blockers']

def test_blocks_if_phase11_accepted_true(tmp_path):
    d=_base(); d['phase11_accepted']=True; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_safety_boundary_open' in r['blockers']

def test_blocks_if_limited_onboarding_allowed_true(tmp_path):
    d=_base(); d['limited_onboarding_allowed']=True; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_safety_boundary_open' in r['blockers']

def test_blocks_if_production_traffic_enabled_true(tmp_path):
    d=_base(); d['production_traffic_enabled']=True; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_safety_boundary_open' in r['blockers']

def test_blocks_if_no_onboarding_authorized_false(tmp_path):
    d=_base(); d['no_onboarding_authorized']=False; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_safety_boundary_open' in r['blockers']

def test_blocks_if_mutation_flag_true(tmp_path):
    d=_base(); d['mutation_performed']=True; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_mutation_flag_detected' in r['blockers']

def test_blocks_if_evidence_summary_missing_runtime_ready(tmp_path):
    d=_base(); d['accepted_evidence_summary']['runtime_path_final_decision']='X'; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_evidence_summary_incomplete' in r['blockers']

def test_blocks_if_evidence_summary_missing_stratum_authorize(tmp_path):
    d=_base(); d['accepted_evidence_summary']['stratum_authorize_ok']=False; r=_call(_write(tmp_path,d)); assert 'canary_acceptance_evidence_summary_incomplete' in r['blockers']

def test_blocks_without_operator_confirmation(tmp_path):
    r=_call(_write(tmp_path,_base()),operator_confirmed=False); assert 'operator_not_confirmed' in r['blockers']

def test_cli_limited_onboarding_gate_json_smoke(tmp_path):
    p=_write(tmp_path,_base()); r=CliRunner().invoke(app,['production','limited-onboarding-gate','--expected-version',__version__,'--farm5-baseline-version','0.1.168','--canary-acceptance-decision-json',str(p),'--operator','vahid','--reason','ok','--operator-confirmed','--i-understand-no-real-customer-onboarding-yet','--i-understand-no-production-traffic-yet','--i-understand-phase11e-requires-separate-execution-gate','--output','json','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0 and 'phase11_limited_onboarding_gate' in r.stdout

def test_cli_limited_onboarding_gate_human_smoke(tmp_path):
    p=_write(tmp_path,_base()); r=CliRunner().invoke(app,['production','limited-onboarding-gate','--expected-version',__version__,'--farm5-baseline-version','0.1.168','--canary-acceptance-decision-json',str(p),'--operator','vahid','--reason','ok','--operator-confirmed','--i-understand-no-real-customer-onboarding-yet','--i-understand-no-production-traffic-yet','--i-understand-phase11e-requires-separate-execution-gate','--output','human','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0 and 'final_decision:' in r.stdout
