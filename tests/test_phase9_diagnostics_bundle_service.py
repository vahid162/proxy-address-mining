from pathlib import Path
from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase9_diagnostics_bundle_service import build_phase9_diagnostics_bundle_report
from mpf.services.phase9_diagnostics_common import DANGEROUS_AUTHORIZATION_FLAGS


def test_phase9_diagnostics_bundle_safe() -> None:
    r = build_phase9_diagnostics_bundle_report(load_config(Path('configs/mpf.example.yaml')))
    assert r['component'] == 'phase9_diagnostics_bundle'
    assert r['report_only'] is True
    assert r['all_dangerous_authorization_flags_false'] is True
    for k in DANGEROUS_AUTHORIZATION_FLAGS:
        assert r[k] is False


def test_phase9_diagnostics_fail_closed_missing_tokens(tmp_path: Path) -> None:
    (tmp_path / 'docs/history').mkdir(parents=True)
    (tmp_path / 'docs/history/PHASE_STATUS_LEGACY_0.1.302.md').write_text('x', encoding='utf-8')
    r = build_phase9_diagnostics_bundle_report(load_config(Path('configs/mpf.example.yaml')), repo_root=tmp_path)
    assert r['final_decision'] == 'BLOCKED'
    assert r['blockers']


def test_phase9_diagnostics_cli_and_focused_json() -> None:
    runner = CliRunner()
    for cmd in [
        ['phase9', 'diagnostics'],
        ['phase9', 'customer-diagnostics'],
        ['phase9', 'abuse-visibility'],
        ['phase9', 'usage-visibility'],
        ['phase9', 'policy-reject-visibility'],
        ['phase9', 'proxy-runtime-diagnostics'],
        ['phase9', 'evidence-pack'],
        ['phase9', 'troubleshooting-summary'],
    ]:
        res = runner.invoke(app, [*cmd, '--config', 'configs/mpf.example.yaml', '--output', 'json'])
        assert res.exit_code == 0
        assert '"report_only": true' in res.output
