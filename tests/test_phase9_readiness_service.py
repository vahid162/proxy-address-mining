from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase9_readiness_service import build_phase9_readiness_report


def test_phase9_readiness_report_safe() -> None:
    cfg = load_config(Path('configs/mpf.example.yaml'))
    r = build_phase9_readiness_report(cfg)
    assert r['component'] == 'phase9_readiness'
    assert r['execution_allowed'] is False
    assert r['firewall_apply_authorized'] is False
    assert r['production_traffic_authorized'] is False
    assert r['abuse_runner_authorized'] is False
    assert r['production_db_execution_authorized'] is False
    assert r['customer_nat_authorized'] is False
    assert r['customer_firewall_rules_authorized'] is False
    assert r['ui_authorized'] is False
    assert r['telegram_authorized'] is False


def test_phase9_readiness_report_includes_final_verdict_diagnostics() -> None:
    cfg = load_config(Path('configs/mpf.example.yaml'))
    r = build_phase9_readiness_report(cfg)
    assert r['latest_recorded_farm5_sync_evidence'] == '0.1.124'
    assert r['phase9_check_report_diagnostics_doc_present'] is True
    assert r['check_report_diagnostics_contract_defined'] is True
    assert r['final_verdict_diagnostics_ready'] is True
    assert r['overall_report_verdict'] == 'OK'
    assert r['blockers'] == []


def test_phase9_readiness_cli_json() -> None:
    result = CliRunner().invoke(app, ['phase9', 'readiness', '--config', 'configs/mpf.example.yaml', '--output', 'json'])
    assert result.exit_code == 0
    assert 'phase9_readiness' in result.output
    assert 'final_verdict_diagnostics_ready' in result.output
    assert 'production_traffic_authorized' in result.output
