from pathlib import Path
from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_canary_runtime_path_evidence_service import build_phase11_canary_runtime_path_evidence_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path('configs/mpf.example.yaml'))


def test_runtime_path_from_files_happy(tmp_path):
    c=tmp_path/'c.txt'; f=tmp_path/'f.txt'; b=tmp_path/'b.txt'
    c.write_text('tcp 6 431999 ESTABLISHED src=1.1.1.1 dst=2.2.2.2 sport=50000 dport=20001 [ASSURED] src=172.18.0.3 dst=1.1.1.1 sport=60010 dport=50000\n')
    f.write_text('1.1.1.1:50000 -> 172.18.0.3:60010 -> bitcoin.viabtc.io:3333\n')
    b.write_text('172.18.0.3:60010 -> mpf-v2raya:22070 -> 127.0.0.1:20170\n')
    r=build_phase11_canary_runtime_path_evidence_report(_cfg(),customer_key='canary-btc-001',lane='btc',port=20001,expected_version='0.1.189',farm5_baseline_version='0.1.168',source_ip='1.1.1.1',source_port=50000,pool_host='bitcoin.viabtc.io',pool_port=3333,backend_target='172.18.0.3:60010',bridge_target='127.0.0.1:20170',collect_live=False,conntrack_file=c,forwarder_log_file=f,bridge_log_file=b)
    assert r['final_decision']=='RUNTIME_PATH_EVIDENCE_READY'
    assert r['generated_evidence']['conntrack_assured'] is True


def test_cli_smoke_runtime_path():
    runner=CliRunner()
    res=runner.invoke(app,['production','canary-runtime-path-evidence','--output','json','--config','configs/mpf.example.yaml'])
    assert res.exit_code==0
    assert '"mutation_performed": false' in res.stdout
