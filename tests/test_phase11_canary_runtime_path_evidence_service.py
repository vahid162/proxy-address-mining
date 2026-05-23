from pathlib import Path
from typer.testing import CliRunner
import subprocess

from mpf.interfaces.cli import app
from mpf.services.phase11_canary_runtime_path_evidence_service import build_phase11_canary_runtime_path_evidence_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path('configs/mpf.example.yaml'))


def _base_kwargs(**overrides):
    d=dict(customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.193',farm5_baseline_version='0.1.168',source_ip='1.1.1.1',source_port=50000,pool_host='bitcoin.viabtc.io',pool_port=3333,backend_target='172.18.0.3:60010',bridge_target='127.0.0.1:20170',collect_live=False)
    d.update(overrides)
    return d


def test_runtime_path_from_files_happy(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp 6 431999 ESTABLISHED src=1.1.1.1 dst=2.2.2.2 sport=50000 dport=20001 [ASSURED] src=172.18.0.3 dst=1.1.1.1 sport=60010 dport=50000\n')
    f.write_text('1.1.1.1:50000 -> 172.18.0.3:60010 -> bitcoin.viabtc.io:3333\n')
    b.write_text('172.18.0.3:60010 -> mpf-v2raya:22070 -> 127.0.0.1:20170\n')
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b))
    assert r['final_decision']=='RUNTIME_PATH_EVIDENCE_READY'


def test_conntrack_no_assured_blocked(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp src=1.1.1.1 sport=50000 dport=20001 src=172.18.0.3 dport=50000\n')
    f.write_text('1.1.1.1:50000 -> 172.18.0.3:60010 -> bitcoin.viabtc.io:3333\n')
    b.write_text('172.18.0.3:60010 -> mpf-v2raya:22070 -> 127.0.0.1:20170\n')
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b))
    assert r['final_decision']=='BLOCKED' and 'missing_conntrack_assured_canary_flow' in r['blockers']


def test_conntrack_wrong_backend_or_source_blocked(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp [ASSURED] src=9.9.9.9 sport=12345 dport=20001 src=172.18.0.99 sport=60010 dport=12345\n')
    f.write_text('9.9.9.9:12345 -> 172.18.0.3:60010 -> bitcoin.viabtc.io:3333\n')
    b.write_text('172.18.0.3:60010 -> mpf-v2raya:22070 -> 127.0.0.1:20170\n')
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b))
    assert r['final_decision']=='BLOCKED'


def test_conntrack_generic_line_blocked(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp state established\n')
    f.write_text('1.1.1.1:50000 -> 172.18.0.3:60010 -> bitcoin.viabtc.io:3333\n')
    b.write_text('172.18.0.3:60010 -> mpf-v2raya:22070 -> 127.0.0.1:20170\n')
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b))
    assert r['final_decision']=='BLOCKED'


def test_unreadable_files_fail_closed(tmp_path):
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=tmp_path/'missing-c.txt',forwarder_log_file=tmp_path/'missing-f.txt',bridge_log_file=tmp_path/'missing-b.txt'))
    assert r['final_decision']=='BLOCKED'
    assert 'conntrack_read_failed' in r['blockers']
    assert 'forwarder_log_read_failed' in r['blockers']
    assert 'bridge_log_read_failed' in r['blockers']


def test_forwarder_negative_cases(tmp_path):
    c=tmp_path/'c.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp [ASSURED] src=1.1.1.1 sport=50000 dport=20001 src=172.18.0.3 sport=60010 dport=50000\n')
    b.write_text('172.18.0.3:60010 -> mpf-v2raya:22070 -> 127.0.0.1:20170\n')
    for txt in ['bitcoin.viabtc.io:3333 only\n','172.18.0.3:60010 only\n','startup done\n']:
        f=tmp_path/'f.txt'; f.write_text(txt)
        r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(forwarder_log_file=f,conntrack_file=c,bridge_log_file=b))
        assert r['final_decision']=='BLOCKED'


def test_forwarder_source_ip_without_port_blocked(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp [ASSURED] src=1.1.1.1 sport=50000 dport=20001 src=172.18.0.3 sport=60010 dport=50000\n')
    f.write_text('1.1.1.1:50000 -> 172.18.0.3:60010 -> bitcoin.viabtc.io:3333\n')
    b.write_text('172.18.0.3:60010 -> mpf-v2raya:22070 -> 127.0.0.1:20170\n')
    kw=_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b,source_port=None)
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **kw)
    assert r['final_decision']=='BLOCKED'


def test_bridge_negative_cases(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'
    c.write_text('tcp [ASSURED] src=1.1.1.1 sport=50000 dport=20001 src=172.18.0.3 sport=60010 dport=50000\n')
    f.write_text('1.1.1.1:50000 -> 172.18.0.3:60010 -> bitcoin.viabtc.io:3333\n')
    for txt in ['127.0.0.1:20170\n','bridge startup ok\n','mpf-v2raya:22070 -> 127.0.0.1:20170\n']:
        b=tmp_path/'b.txt'; b.write_text(txt)
        r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b))
        assert r['final_decision']=='BLOCKED'



def test_partial_bridge_preserved_when_others_missing(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp src=1.1.1.1 sport=50000 dport=20001 src=172.18.0.3 dport=50000\n')
    f.write_text('startup done\n')
    b.write_text('172.18.0.3:60010 -> mpf-v2raya:22070 -> 127.0.0.1:20170\n')
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b))
    ev=r['generated_evidence']
    assert r['final_decision']=='BLOCKED'
    assert ev['bridge_loopback_seen'] is True
    assert ev['conntrack_assured'] is False
    assert ev['forwarder_pool_seen'] is False
    assert 'missing_conntrack_assured_canary_flow' in r['blockers']
    assert 'missing_forwarder_pool_correlation' in r['blockers']
    assert 'missing_bridge_loopback_correlation' not in r['blockers']


def test_partial_conntrack_preserved_when_others_missing(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp 6 431999 ESTABLISHED src=1.1.1.1 dst=2.2.2.2 sport=50000 dport=20001 [ASSURED] src=172.18.0.3 dst=1.1.1.1 sport=60010 dport=50000\n')
    f.write_text('startup done\n')
    b.write_text('bridge startup ok\n')
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b))
    ev=r['generated_evidence']
    assert ev['conntrack_assured'] is True
    assert ev['forwarder_pool_seen'] is False
    assert ev['bridge_loopback_seen'] is False
    assert r['final_decision']=='BLOCKED'


def test_partial_forwarder_preserved_when_others_missing(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp src=1.1.1.1 sport=50000 dport=20001 src=172.18.0.3 dport=50000\n')
    f.write_text('1.1.1.1:50000 -> 172.18.0.3:60010 -> bitcoin.viabtc.io:3333\n')
    b.write_text('bridge startup ok\n')
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(conntrack_file=c,forwarder_log_file=f,bridge_log_file=b))
    ev=r['generated_evidence']
    assert ev['conntrack_assured'] is False
    assert ev['forwarder_pool_seen'] is True
    assert ev['bridge_loopback_seen'] is False
    assert r['final_decision']=='BLOCKED'


def test_live_command_failure_no_crash(monkeypatch):
    def _raise(*a, **k):
        raise FileNotFoundError('missing cmd')
    monkeypatch.setattr(subprocess, 'run', _raise)
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(), **_base_kwargs(collect_live=True, backend_target='172.18.0.3:60010'))
    assert r['final_decision']=='BLOCKED'
    assert r['mutation_performed'] is False


def test_cli_smoke_runtime_path():
    runner=CliRunner()
    res=runner.invoke(app,['production','canary-runtime-path-evidence','--output','json','--config','configs/mpf.example.yaml'])
    assert res.exit_code==0
