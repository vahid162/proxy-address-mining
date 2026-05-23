import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence, build_phase11_canary_visibility_bundle_report
from mpf.services.phase11_external_canary_stratum_transcript_import_service import build_phase11_external_canary_stratum_transcript_import_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path('configs/mpf.example.yaml'))


def _tx(worker='canary-btc-001.worker-001', connect_port=20001):
    return {
      'captured_at':'2026-05-23T00:00:00Z','captured_by':'op','external_client':'windows-powershell','connect_host':'85.198.11.110','connect_port':connect_port,
      'worker_name':worker,'source_ip_observed_by_operator':'213.195.38.200',
      'messages':[{'direction':'tx','method':'mining.subscribe','raw':'a'},{'direction':'rx','id':1,'result_present':True,'error_is_null':True,'raw':'b'},{'direction':'tx','method':'mining.authorize','worker_name':worker,'raw':'c'},{'direction':'rx','id':2,'result':True,'error_is_null':True,'raw':'d'},{'direction':'rx','method':'mining.set_difficulty','raw':'e'},{'direction':'rx','method':'mining.notify','raw':'f'}]
    }


def test_valid_import(tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.186',farm5_baseline_version='0.1.168',transcript_json=p)
    assert r['worker_evidence']['worker_visibility_ok'] is True
    assert r['worker_evidence']['stratum_subscribe_ok'] is True
    assert r['worker_evidence']['stratum_authorize_ok'] is True
    assert r['worker_evidence']['stratum_set_difficulty_seen'] is True
    assert r['worker_evidence']['stratum_notify_seen'] is True
    assert r['mutation_performed'] is False


def test_fail_closed_cases(tmp_path):
    t=_tx(); t['messages']=[m for m in t['messages'] if not (m.get('id')==1 and m.get('direction')=='rx')]
    p=tmp_path/'m1.json'; p.write_text(json.dumps(t),encoding='utf-8')
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.186',farm5_baseline_version='0.1.168',transcript_json=p)
    assert r['worker_evidence']['worker_visibility_ok'] is False

    t2=_tx();
    for m in t2['messages']:
        if m.get('id')==2 and m.get('direction')=='rx': m['result']=False
    p2=tmp_path/'m2.json'; p2.write_text(json.dumps(t2),encoding='utf-8')
    r2=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.186',farm5_baseline_version='0.1.168',transcript_json=p2)
    assert r2['worker_evidence']['worker_visibility_ok'] is False


def test_bundle_and_acceptance_lift(tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    rr=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.186',farm5_baseline_version='0.1.168',transcript_json=p)
    ev=Phase11CanaryVisibilityEvidence.from_dict(rr['generated_evidence'])
    b=build_phase11_canary_visibility_bundle_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.186',farm5_baseline_version='0.1.168',evidence=ev)
    assert 'unique_workers_visibility' not in b['missing_visibility_primitives']


def test_cli_command(tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    out=tmp_path/'e.json'
    r=CliRunner().invoke(app,['production','canary-external-stratum-transcript-import','--transcript-json',str(p),'--write-evidence-json',str(out),'--overwrite-evidence-json','--output','json','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0
    assert out.exists()
