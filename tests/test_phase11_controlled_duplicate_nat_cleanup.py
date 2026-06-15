from pathlib import Path

from mpf.services import phase11_controlled_artifact_refresh_service as svc

BACKEND = {'status':'ok','resolved_ipv4':'172.18.0.2','target_host':'172.18.0.2','target_port':60010,'backend_public_exposure':False,'target_fingerprint':'fp','health_status':'healthy'}


def snap(dup=True, target='172.18.0.2:60010'):
    rules = [
        '*nat', ':MPF_NAT_PRE - [0:0]',
        f'-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination {target}',
        f'-A MPF_NAT_PRE -p tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" -j DNAT --to-destination {target}',
    ]
    if dup:
        rules += rules[2:4]
    return '\n'.join(rules + ['COMMIT',''])


def fake_collect(*a, backend=None, text=None, **k):
    return [], [], (backend or BACKEND).copy(), text if text is not None else snap(True), '', []


def ok_restore(monkeypatch, calls=None):
    def run(self, argv, input_text=None):
        if calls is not None:
            calls.append((argv, input_text))
        return svc.CommandResult(0, 'real stdout', 'real stderr')
    monkeypatch.setattr(svc.ProductionIptablesRestoreRunner, 'run', run)


def test_plan_preview_does_not_fabricate_restore_test(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(svc, '_collect_live_inputs', fake_collect)
    ok_restore(monkeypatch, calls)
    report = svc.run_duplicate_nat_cleanup_plan_report(config_path=tmp_path/'missing')
    assert report['final_decision'] == svc.DUP_READY
    assert report['restore_test_required'] is True
    assert report['restore_test_invoked'] is False
    assert report['package_preview']['restore_test_invoked'] is False
    assert 'restore_test_noflush_required' in report['package_preview']['blockers']
    assert calls == []


def test_package_ready_exact_two_calls_restore_test_and_records_result(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(svc, '_collect_live_inputs', fake_collect)
    ok_restore(monkeypatch, calls)
    report = svc.run_duplicate_nat_cleanup_package_report(config_path=tmp_path/'missing')
    assert report['final_decision'] == svc.DUP_READY
    assert calls and calls[0][0] == ['iptables-restore', '--test', '--noflush']
    assert report['restore_test_result'] == {'returncode': 0, 'stdout': 'real stdout', 'stderr': 'real stderr'}
    pkg = report['package']
    assert pkg['restore_test_invoked'] is True
    assert pkg['duplicate_nat_redirect_count'] == 2
    assert pkg['payload'].count('-D MPF_NAT_PRE') == 2
    assert '--noflush' not in pkg['payload']


def test_package_blocks_on_restore_test_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, '_collect_live_inputs', fake_collect)
    monkeypatch.setattr(svc.ProductionIptablesRestoreRunner, 'run', lambda self, argv, input_text=None: svc.CommandResult(1, 'bad', 'syntax'))
    report = svc.run_duplicate_nat_cleanup_package_report(config_path=tmp_path/'missing')
    assert report['final_decision'] == svc.DUP_BLOCKED
    assert report['restore_test_result']['returncode'] == 1
    assert 'restore_test_noflush_failed' in report['blockers']
    assert 'iptables_restore_test_failed' in report['blockers']


def test_duplicate_cleanup_no_duplicate_blocked(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, '_collect_live_inputs', lambda *a, **k: fake_collect(text=snap(False)))
    report = svc.run_duplicate_nat_cleanup_plan_report(config_path=tmp_path/'missing')
    assert report['final_decision'] == svc.DUP_BLOCKED
    assert 'no_duplicate_nat_redirects' in report['blockers']


def test_duplicate_cleanup_backend_drift_blocked(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, '_collect_live_inputs', lambda *a, **k: fake_collect(text=snap(True, '172.18.0.9:60010')))
    report = svc.run_duplicate_nat_cleanup_plan_report(config_path=tmp_path/'missing')
    assert report['final_decision'] == svc.DUP_BLOCKED
    assert 'unknown_mpf_artifacts_detected' in report['blockers'] or 'backend_target_drift' in report['blockers']


def test_expected_backend_target_mismatch_blocks_without_overriding_live_backend(monkeypatch, tmp_path):
    live = {**BACKEND, 'backend_public_exposure': True, 'health_status': 'unhealthy', 'target_fingerprint': 'live-fp'}
    monkeypatch.setattr(svc, '_collect_live_inputs', lambda *a, **k: fake_collect(backend=live))
    report = svc.run_duplicate_nat_cleanup_plan_report(config_path=tmp_path/'missing', expected_backend_target='172.18.0.9:60010')
    assert report['final_decision'] == svc.DUP_BLOCKED
    assert 'backend_target_drift' in report['blockers']
    assert 'backend_public_exposure_detected' in report['blockers']
    assert report['backend_target']['backend_public_exposure'] is True
    assert report['backend_target']['health_status'] == 'unhealthy'
    assert report['backend_target']['target_fingerprint'] == 'live-fp'


def test_duplicate_cleanup_preflight_hash_mismatch_blocks(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, '_collect_live_inputs', fake_collect)
    ok_restore(monkeypatch)
    pkg = svc.run_duplicate_nat_cleanup_package_report(config_path=tmp_path/'missing')['package']
    p = tmp_path/'pkg.json'; import json; p.write_text(json.dumps(pkg))
    report = svc.run_duplicate_nat_cleanup_execute_preflight_report(package_json=p, package_sha256='bad', config_path=tmp_path/'missing')
    assert report['final_decision'] == svc.DUP_PREFLIGHT_BLOCKED
    assert 'package_file_sha256_mismatch' in report['blockers']


def test_execute_requires_env_and_yes(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, '_collect_live_inputs', fake_collect)
    ok_restore(monkeypatch)
    pkg = svc.run_duplicate_nat_cleanup_package_report(config_path=tmp_path/'missing')['package']
    p = tmp_path/'pkg.json'; import json; p.write_text(json.dumps(pkg))
    sha = svc._text_sha(p.read_text())
    monkeypatch.delenv('MPF_PHASE11_CONTROLLED_DUPLICATE_NAT_CLEANUP', raising=False)
    report = svc.run_duplicate_nat_cleanup_execute_report(package_json=p, package_sha256=sha, config_path=tmp_path/'missing', out_dir=tmp_path/'out')
    assert report['final_decision'] == 'FAILED_PRE_APPLY'
    assert 'controlled_duplicate_nat_cleanup_env_gate_missing' in report['blockers']
    assert 'yes_confirmation_required' in report['blockers']
    assert report['docker_restart_performed'] is False
    assert report['conntrack_flush_performed'] is False


def test_verify_ready_after_duplicates_removed(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, '_collect_live_inputs', lambda *a, **k: fake_collect(text=snap(False)))
    report = svc.run_duplicate_nat_cleanup_verify_report(config_path=tmp_path/'missing')
    assert report['final_decision'] == svc.DUP_VERIFY_READY
    assert report['duplicate_nat_redirect_count'] == 0


def test_post_cleanup_readiness_keeps_phase12_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, '_collect_live_inputs', lambda *a, **k: fake_collect(text=snap(False)))
    monkeypatch.setattr('mpf.services.phase11_operational_completion_gap_inventory_service.run_phase11_operational_completion_gap_inventory_report', lambda *a, **k: {'full_cli_production_operations':'missing_or_partial'})
    report = svc.run_duplicate_nat_cleanup_post_cleanup_readiness_report(config_path=tmp_path/'missing')
    assert report['phase11_operational_completion_accepted'] is False
    assert report['phase12_start_allowed'] is False
