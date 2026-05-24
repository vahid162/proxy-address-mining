import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from mpf import __version__
from mpf.interfaces.cli import app
from mpf.services.phase11_canary_acceptance_decision_service import build_phase11_canary_acceptance_decision_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path("configs/mpf.example.yaml"))


def _write_pack(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps({"expected_version":"0.1.195","repository_version":"0.1.195","farm5_baseline_version":"0.1.168","customer_key":"canary-btc-001","lane":"btc","public_port":20001,"backend_target":"172.18.0.3:60010","runtime_path_final_decision":"RUNTIME_PATH_EVIDENCE_READY","visibility_bundle_final_decision":"VISIBILITY_READY","acceptance_review_final_decision":"ACCEPTANCE_REVIEW_READY","missing_visibility_primitives":[],"missing_evidence_primitives":[],"next_required_step":"none","mutation_performed":False,"production_traffic_enabled":False,"phase11_accepted":False,"limited_onboarding_allowed":False,"no_onboarding_authorized":True,"failed_collectors":[],"skipped_files":[]}), encoding='utf-8')
    (d / "runtime-path-evidence.json").write_text(json.dumps({"final_decision":"RUNTIME_PATH_EVIDENCE_READY","blockers":[],"generated_evidence":{"customer_key":"canary-btc-001","lane":"btc","port":20001,"backend_target":"172.18.0.3:60010","evidence_source":"live_source_backed_canary_runtime_path","evidence_reference":"ref","source_query_or_artifact":"q","conntrack_assured":True,"forwarder_pool_seen":True,"bridge_loopback_seen":True},"mutation_performed":False,"production_traffic_enabled":False,"phase11_accepted":False,"limited_onboarding_allowed":False,"no_onboarding_authorized":True}), encoding='utf-8')
    (d / "visibility-bundle.json").write_text(json.dumps({"final_decision":"VISIBILITY_READY","blockers":[],"warnings":[],"missing_visibility_primitives":[],"missing_evidence_primitives":[],"next_required_step":"none","runtime_evidence":{"conntrack_assured":True,"forwarder_pool_seen":True,"bridge_loopback_seen":True,"stratum_subscribe_ok":True,"stratum_authorize_ok":True,"stratum_set_difficulty_seen":True,"stratum_notify_seen":True,"canary_nat_rule_present":True,"canary_nat_rule_count":1,"canary_nat_target":"172.18.0.3:60010","no_extra_customer_nat_rules":True,"no_unexpected_mpf_firewall_references":True},"mutation_performed":False,"production_traffic_enabled":False,"phase11_accepted":False,"limited_onboarding_allowed":False,"no_onboarding_authorized":True}), encoding='utf-8')
    (d / "acceptance-review.json").write_text(json.dumps({"final_decision":"ACCEPTANCE_REVIEW_READY","final_decision_reason":"all required gates satisfied","blockers":[],"warnings":[],"missing_visibility_primitives":[],"missing_evidence_primitives":[],"next_required_step":"none","controlled_canary_artifact_present":True,"current_phase_gate_strict_result":"CRITICAL_EXPECTED_FOR_CANARY_ARTIFACT","phase11_accepted":False,"limited_onboarding_allowed":False,"no_onboarding_authorized":True,"production_traffic_enabled":False,"mutation_performed":False,"safety_flags":{"production_traffic_allowed":False,"firewall_apply_allowed":False,"abuse_automation_allowed":False,"ui_allowed":False,"telegram_allowed":False,"scheduler_allowed":False,"worker_enforcement_allowed":False}}), encoding='utf-8')


def _call(pack, **kw):
    return build_phase11_canary_acceptance_decision_report(_cfg(), customer_key='canary-btc-001', lane='btc', port=20001, backend_target='172.18.0.3:60010', expected_version=__version__, farm5_baseline_version='0.1.168', evidence_pack_dir=pack, operator='op', reason='ok', **{
        'operator_confirmed': True,
        'i_have_reviewed_evidence_pack': True,
        'i_confirm_no_real_customer_onboarding': True,
        'i_confirm_no_production_traffic_authorized': True,
        'i_confirm_phase11_not_final_accepted': True,
        **kw,
    })


def test_accepts_exact_farm5_0195_evidence_pack_with_operator_approval(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); a=tmp_path/'a.tar.gz'; a.write_bytes(b'x')
    rep=_call(d,evidence_archive_path=a,expected_archive_sha256=hashlib.sha256(b'x').hexdigest())
    assert rep['final_decision']=='CANARY_ACCEPTANCE_DECISION_ACCEPTED'

def test_blocks_missing_operator_approval(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); rep=_call(d,operator_confirmed=False)
    assert 'operator_not_confirmed' in rep['blockers']

def test_blocks_missing_evidence_file(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); (d/'manifest.json').unlink(); rep=_call(d)
    assert 'evidence_file_missing:manifest.json' in rep['blockers']

def test_blocks_invalid_json(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); (d/'manifest.json').write_text('{',encoding='utf-8'); rep=_call(d)
    assert 'evidence_file_invalid_json:manifest.json' in rep['blockers']

def test_blocks_archive_sha256_mismatch(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); a=tmp_path/'a.tar.gz'; a.write_bytes(b'x'); rep=_call(d,evidence_archive_path=a,expected_archive_sha256='bad')
    assert 'evidence_archive_sha256_mismatch' in rep['blockers']

def test_blocks_wrong_scope(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); rep=build_phase11_canary_acceptance_decision_report(_cfg(), customer_key='bad', lane='btc', port=20001, backend_target='172.18.0.3:60010', expected_version=__version__, farm5_baseline_version='0.1.168', evidence_pack_dir=d, operator='op', reason='ok', operator_confirmed=True, i_have_reviewed_evidence_pack=True, i_confirm_no_real_customer_onboarding=True, i_confirm_no_production_traffic_authorized=True, i_confirm_phase11_not_final_accepted=True)
    assert 'canary_acceptance_scope_mismatch' in rep['blockers']

def test_blocks_if_runtime_not_ready(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); j=json.loads((d/'runtime-path-evidence.json').read_text()); j['final_decision']='BLOCKED'; (d/'runtime-path-evidence.json').write_text(json.dumps(j)); rep=_call(d); assert 'runtime_path_not_ready' in rep['blockers']

def test_blocks_if_visibility_not_ready(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); j=json.loads((d/'visibility-bundle.json').read_text()); j['final_decision']='BLOCKED'; (d/'visibility-bundle.json').write_text(json.dumps(j)); rep=_call(d); assert 'visibility_bundle_not_ready' in rep['blockers']

def test_blocks_if_acceptance_review_not_ready(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); j=json.loads((d/'acceptance-review.json').read_text()); j['final_decision']='BLOCKED'; (d/'acceptance-review.json').write_text(json.dumps(j)); rep=_call(d); assert 'acceptance_review_not_ready' in rep['blockers']

def test_blocks_if_any_mutation_or_authorization_flag_true(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); j=json.loads((d/'manifest.json').read_text()); j['phase11_accepted']=True; (d/'manifest.json').write_text(json.dumps(j)); rep=_call(d); assert 'evidence_mutation_flag_detected' in rep['blockers']

def test_blocks_if_required_runtime_primitive_missing(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); j=json.loads((d/'runtime-path-evidence.json').read_text()); j['generated_evidence']['conntrack_assured']=False; (d/'runtime-path-evidence.json').write_text(json.dumps(j)); rep=_call(d); assert 'canary_runtime_primitive_missing' in rep['blockers']

def test_blocks_if_acceptance_safety_flag_open(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); j=json.loads((d/'acceptance-review.json').read_text()); j['safety_flags']['ui_allowed']=True; (d/'acceptance-review.json').write_text(json.dumps(j)); rep=_call(d); assert 'acceptance_safety_flag_open' in rep['blockers']

def test_cli_canary_acceptance_decision_json_smoke(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); r=CliRunner().invoke(app,['production','canary-acceptance-decision','--evidence-pack-dir',str(d),'--operator','op','--reason','ok','--operator-confirmed','--i-have-reviewed-evidence-pack','--i-confirm-no-real-customer-onboarding','--i-confirm-no-production-traffic-authorized','--i-confirm-phase11-not-final-accepted','--output','json','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0 and 'phase11_canary_acceptance_decision' in r.stdout

def test_cli_canary_acceptance_decision_human_smoke(tmp_path):
    d=tmp_path/'pack'; _write_pack(d); r=CliRunner().invoke(app,['production','canary-acceptance-decision','--evidence-pack-dir',str(d),'--operator','op','--reason','ok','--operator-confirmed','--i-have-reviewed-evidence-pack','--i-confirm-no-real-customer-onboarding','--i-confirm-no-production-traffic-authorized','--i-confirm-phase11-not-final-accepted','--output','human','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0 and 'final_decision:' in r.stdout
