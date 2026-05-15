from mpf.config import load_config
from mpf.services.phase6_operator_acceptance_decision_service import build_phase6_operator_acceptance_decision_report
from tests.test_smoke import example_config_path


def test_operator_acceptance_decision_report_shape() -> None:
    r = build_phase6_operator_acceptance_decision_report(load_config(example_config_path()))
    assert r['component'] == 'phase6_operator_acceptance_decision'
    assert r['final_decision'] in {'ACCEPTED', 'BLOCKED'}
    assert r['execution_allowed'] is False
    assert r['customer_nat_authorized'] is False
    assert r['customer_firewall_rules_authorized'] is False
    assert r['production_traffic_authorized'] is False
    assert r['firewall_apply_authorized'] is False
    assert r['iptables_restore_authorized'] is False
    for k in ['live_firewall_write_allowed','live_firewall_apply_allowed','live_firewall_verify_allowed','live_firewall_rollback_allowed','db_mutation']:
        assert k in r and r[k] is False
