import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase10_readiness_service import build_phase10_readiness_report


def cfg():
    return load_config(Path('configs/mpf.example.yaml'))


def test_phase10_readiness_accepted():
    r = build_phase10_readiness_report(cfg())
    assert r['final_decision'] == 'ACCEPTED'
    assert r['readiness_status'] == 'PHASE10_PLANNING_READINESS_ACCEPTED'
    assert r['latest_recorded_farm5_sync_evidence'] == '0.1.130'
    assert r['farm5_0_1_128_sync_test_evidence_present'] is True
    assert r['farm5_0_1_130_sync_test_evidence_present'] is True
    assert r['phase9_final_acceptance_status'] == 'ACCEPTED'
    assert r['aggregate_dangerous_authorization_flag'] is False


def test_phase10_readiness_fail_closed_missing_evidence(tmp_path: Path):
    (tmp_path / 'docs').mkdir()
    phase = Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
    (tmp_path / 'docs/PHASE_STATUS.md').write_text(phase, encoding='utf-8')
    r = build_phase10_readiness_report(cfg(), repo_root=tmp_path)
    assert r['final_decision'] == 'BLOCKED'
    assert 'farm5_0_1_130_sync_test_evidence_missing' in r['blockers']


def test_phase10_cli_json():
    out = CliRunner().invoke(app, ['phase10', 'readiness', '--config', 'configs/mpf.example.yaml', '--output', 'json'])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data['component'] == 'phase10_readiness'
    assert data['latest_recorded_farm5_sync_evidence'] == '0.1.130'
