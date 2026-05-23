from pathlib import Path
from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_canary_evidence_pack_service import build_phase11_canary_evidence_pack_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path('configs/mpf.example.yaml'))


def test_manifest_safety(tmp_path, monkeypatch):
    monkeypatch.setattr('mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report', lambda *a, **k: {'evidence': {'canary_nat_target':'172.18.0.3:60010'}})
    r=build_phase11_canary_evidence_pack_report(_cfg(), out_dir=tmp_path/'o', collect_live=True, expected_version='0.1.191', farm5_baseline_version='0.1.168')
    assert r['mutation_performed'] is False and r['phase11_accepted'] is False and r['limited_onboarding_allowed'] is False and r['no_onboarding_authorized'] is True


def test_out_dir_safety(tmp_path):
    p=tmp_path/'x'; p.mkdir()
    try:
        build_phase11_canary_evidence_pack_report(_cfg(), out_dir=p, overwrite_out_dir=False)
    except ValueError:
        assert True


def test_cli_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr('mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report', lambda *a, **k: {'evidence': {'canary_nat_target':'172.18.0.3:60010'}})
    runner=CliRunner()
    res=runner.invoke(app,['production','canary-evidence-pack','--out-dir',str(tmp_path/'pack'),'--output','json','--config','configs/mpf.example.yaml'])
    assert res.exit_code==0
    assert (tmp_path/'pack'/'manifest.json').exists()
