from pathlib import Path

from mpf.config import load_config
from mpf.services.firewall_manual_canary_customer_proposal_service import build_manual_canary_customer_proposal_report


def _cfg():
    return load_config(Path(__file__).resolve().parent.parent / 'configs' / 'mpf.example.yaml')


def test_manual_canary_proposal_defaults_blocked():
    report = build_manual_canary_customer_proposal_report(_cfg())
    assert report['component'] == 'firewall_manual_canary_customer_proposal'
    assert report['final_decision'] == 'BLOCKED'
    assert report['execution_allowed'] is False
    assert report['customer_nat_authorized'] is False
    assert report['customer_firewall_rules_authorized'] is False
    assert report['production_traffic_authorized'] is False


def test_proposal_blocker_when_phase_status_missing(tmp_path: Path):
    cfg = _cfg()
    (tmp_path / 'docs').mkdir(parents=True)
    report = build_manual_canary_customer_proposal_report(cfg, repo_root=tmp_path)
    assert 'docs/PHASE_STATUS.md missing' in report['blockers']


def test_proposal_blocker_when_farm5_evidence_missing(tmp_path: Path):
    cfg = _cfg()
    docs = tmp_path / 'docs'
    docs.mkdir(parents=True)
    docs.joinpath('PHASE_STATUS.md').write_text('## Current State\n```text\ncurrent_accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5\n```\n', encoding='utf-8')
    report = build_manual_canary_customer_proposal_report(cfg, repo_root=tmp_path)
    assert 'farm5 0.1.95 sync evidence missing' in report['blockers']


def test_proposal_blocker_when_apply_mode_not_plan_only():
    cfg = _cfg()
    cfg.firewall.apply_mode = 'live_apply'
    report = build_manual_canary_customer_proposal_report(cfg)
    assert 'firewall.apply_mode is not plan_only' in report['blockers']


def test_proposal_blocker_when_runtime_activation_true():
    cfg = _cfg()
    cfg.proxy.runtime_activation_allowed = True
    report = build_manual_canary_customer_proposal_report(cfg)
    assert 'proxy.runtime_activation_allowed is true' in report['blockers']


def test_proposal_safety_flags_exist_and_false():
    report = build_manual_canary_customer_proposal_report(_cfg())
    keys = [
        'live_firewall_write_allowed','live_firewall_apply_allowed','live_firewall_verify_allowed','live_firewall_rollback_allowed',
        'iptables_restore_allowed','iptables_restore_executed','subprocess_firewall_calls_allowed','subprocess_firewall_calls_executed',
        'real_adapter_allowed','real_adapter_executed','db_mutation','db_apply_record_write_allowed','db_apply_record_written',
        'filesystem_write_executed','restore_point_write_allowed','restore_point_written','lock_acquisition_allowed','lock_acquired',
        'customer_nat_allowed','customer_nat_changed','customer_firewall_rules_allowed','customer_firewall_rules_changed',
        'production_traffic_changed','usage_automation_allowed','abuse_automation_allowed_runtime','ui_allowed_runtime','telegram_allowed_runtime'
    ]
    for k in keys:
        assert k in report
        assert report[k] is False
