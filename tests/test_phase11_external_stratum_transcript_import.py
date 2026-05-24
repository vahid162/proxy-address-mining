import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence, build_phase11_canary_acceptance_review_report
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence, build_phase11_canary_visibility_bundle_report
from mpf.services.phase11_external_canary_stratum_transcript_import_service import (
    _classify_forwarder_pool_seen,
    build_phase11_external_canary_stratum_transcript_import_report,
)


def _cfg():
    from mpf.config import load_config
    return load_config(Path('configs/mpf.example.yaml'))


def _tx(worker='canary-btc-001.worker-001', connect_port=20001):
    return {
      'captured_at':'2026-05-23T00:00:00Z','captured_by':'op','external_client':'windows-powershell','connect_host':'85.198.11.110','connect_port':connect_port,
      'worker_name':worker,'source_ip_observed_by_operator':'213.195.38.200','source_port_observed_by_operator':56704,
      'messages':[{'direction':'tx','method':'mining.subscribe','raw':'a'},{'direction':'rx','id':1,'result_present':True,'error_is_null':True,'raw':'b'},{'direction':'tx','method':'mining.authorize','worker_name':worker,'raw':'c'},{'direction':'rx','id':2,'result':True,'error_is_null':True,'raw':'d'},{'direction':'rx','method':'mining.set_difficulty','raw':'e'},{'direction':'rx','method':'mining.notify','raw':'f'}]
    }


def test_valid_import(tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',transcript_json=p)
    assert r['final_decision']=='WORKER_STRATUM_EVIDENCE_READY'


def test_scope_fail_closed(tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    for kwargs in [dict(customer_key='x',lane='btc',port=20001),dict(customer_key='canary-btc-001',lane='zec',port=20001),dict(customer_key='canary-btc-001',lane='btc',port=20002)]:
        r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),expected_version='0.1.198',farm5_baseline_version='0.1.168',transcript_json=p,**kwargs)
        assert r['final_decision']=='BLOCKED'
        assert 'transcript_scope_mismatch' in r['blockers']


def test_wrong_worker_and_missing_notify(tmp_path):
    t=_tx(worker='wrong.worker'); p=tmp_path/'w.json'; p.write_text(json.dumps(t),encoding='utf-8')
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',transcript_json=p)
    assert r['final_decision']=='BLOCKED'
    t2=_tx(); t2['messages']=[m for m in t2['messages'] if m.get('method')!='mining.notify']; p2=tmp_path/'n.json'; p2.write_text(json.dumps(t2),encoding='utf-8')
    r2=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',transcript_json=p2)
    assert r2['worker_evidence']['stratum_notify_seen'] is False


def test_version_and_baseline_fail_closed(tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.0.0',farm5_baseline_version='0.1.168',transcript_json=p)
    assert 'expected_version_mismatch' in r['blockers']
    r2=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.167',transcript_json=p)
    assert 'farm5_baseline_version_not_allowed' in r2['blockers']


def test_forwarder_correlation_classifier():
    logs='213.195.38.200:56704 - 172.18.0.3:60010\n213.195.38.200:56704 <-> bitcoin.viabtc.io:3333'
    assert _classify_forwarder_pool_seen(source_ip='213.195.38.200',source_port=56704,forwarder_logs=logs) is True
    logs2='172.18.0.3:60010\nbitcoin.viabtc.io:3333\nother'
    assert _classify_forwarder_pool_seen(source_ip='213.195.38.200',source_port=56704,forwarder_logs=logs2) is False
    logs3='213.195.38.200:11111 - 172.18.0.3:60010\n213.195.38.200:22222 <-> bitcoin.viabtc.io:3333'
    assert _classify_forwarder_pool_seen(source_ip='213.195.38.200',source_port=56704,forwarder_logs=logs3) is False


def test_collect_live_checks(monkeypatch,tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    monkeypatch.setattr('mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report',lambda *a,**k:{'evidence':{'canary_customer_db_visible':False}})
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',transcript_json=p,collect_live=True)
    assert r['final_decision']=='BLOCKED'
    assert any(b.startswith('collect_live_check_failed:') for b in r['blockers'])


def test_end_to_end_visibility_acceptance(monkeypatch,tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',transcript_json=p)
    ev=Phase11CanaryVisibilityEvidence.from_dict(r['generated_evidence'])
    b=build_phase11_canary_visibility_bundle_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',evidence=ev)
    assert 'unique_workers_visibility' not in b['missing_visibility_primitives']
    acc=build_phase11_canary_acceptance_review_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',evidence=Phase11CanaryAcceptanceEvidence.from_dict({'canary_customer_db_visible':True,'usage_visibility_ok':True,'reject_visibility_ok':True,'session_visibility_ok':True,'unique_ip_visibility_ok':True,'worker_visibility_ok':True,'stratum_subscribe_ok':True,'stratum_authorize_ok':True,'stratum_set_difficulty_seen':True,'stratum_notify_seen':True}))
    assert acc['final_decision']=='BLOCKED'
    assert acc['phase11_accepted'] is False
    assert acc['limited_onboarding_allowed'] is False
    assert acc['mutation_performed'] is False


def test_cli_command(tmp_path):
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    out=tmp_path/'e.json'
    r=CliRunner().invoke(app,['production','canary-external-stratum-transcript-import','--transcript-json',str(p),'--write-evidence-json',str(out),'--overwrite-evidence-json','--output','json','--config','configs/mpf.example.yaml'])
    assert r.exit_code==0
    assert out.exists()


def test_collect_live_uses_customer_read_service_for_canary_visibility(monkeypatch,tmp_path):
    from types import SimpleNamespace
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    monkeypatch.setattr('mpf.services.customer_read_service.list_customer_status', lambda *a, **k: SimpleNamespace(ok=True, customers=[SimpleNamespace(customer_key='canary-btc-001', lane='btc', port=20001)], message=''))
    monkeypatch.setattr('mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report',lambda *a,**k:{'evidence':{'canary_customer_db_visible':False,'canary_nat_rule_present':True,'canary_nat_rule_count':1,'canary_nat_target':'172.18.0.3:60010','mpf_nat_pre_exists':True,'prerouting_hook_present':True,'no_extra_customer_nat_rules':True,'no_unexpected_mpf_firewall_references':True,'bridge_healthy':True,'bridge_reachable_from_forwarder':True}})
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',transcript_json=p,collect_live=True)
    assert r['final_decision']=='WORKER_STRATUM_EVIDENCE_READY'

def test_collect_live_blocks_when_canary_db_scope_wrong(monkeypatch,tmp_path):
    from types import SimpleNamespace
    p=tmp_path/'t.json'; p.write_text(json.dumps(_tx()),encoding='utf-8')
    monkeypatch.setattr('mpf.services.customer_read_service.list_customer_status', lambda *a, **k: SimpleNamespace(ok=True, customers=[SimpleNamespace(customer_key='canary-btc-001', lane='btc', port=20002)], message=''))
    monkeypatch.setattr('mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report',lambda *a,**k:{'evidence':{'canary_nat_rule_present':True,'canary_nat_rule_count':1,'canary_nat_target':'172.18.0.3:60010','mpf_nat_pre_exists':True,'prerouting_hook_present':True,'no_extra_customer_nat_rules':True,'no_unexpected_mpf_firewall_references':True,'bridge_healthy':True,'bridge_reachable_from_forwarder':True}})
    r=build_phase11_external_canary_stratum_transcript_import_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.198',farm5_baseline_version='0.1.168',transcript_json=p,collect_live=True)
    assert 'collect_live_check_failed:canary_customer_db_visible' in r['blockers']
