from pathlib import Path

from mpf.config import load_config
from mpf.services.firewall_manual_canary_customer_acceptance_readiness_service import build_manual_canary_customer_acceptance_readiness_report


def _cfg():
    return load_config(Path(__file__).resolve().parent.parent / 'configs' / 'mpf.example.yaml')


def test_manual_canary_acceptance_defaults_blocked():
    report = build_manual_canary_customer_acceptance_readiness_report(_cfg())
    assert report['component'] == 'firewall_manual_canary_customer_acceptance_readiness'
    assert report['final_decision'] == 'BLOCKED'


def test_acceptance_safety_flags_exist_and_false():
    report = build_manual_canary_customer_acceptance_readiness_report(_cfg())
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
