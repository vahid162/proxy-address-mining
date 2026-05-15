from mpf.config import load_config
from mpf.services.phase6_operator_acceptance_decision_service import build_phase6_operator_acceptance_decision_report
from tests.test_smoke import example_config_path


def test_phase6_operator_acceptance_final_service_values() -> None:
    r = build_phase6_operator_acceptance_decision_report(load_config(example_config_path()))
    assert r["component"] == "phase6_operator_acceptance_decision"
    assert r["final_decision"] == "BLOCKED"
    assert r["acceptance_status"] in {"PHASE6_ACCEPTED_PLANNER_REPORTING_ONLY", "PHASE6_NOT_ACCEPTED"}
    assert r["authorization_status"] in {"PHASE6_ACCEPTED_WITH_RUNTIME_GATES_CLOSED", "FINAL_OPERATOR_ACCEPTANCE_NOT_GRANTED"}
    assert r["phase6_accepted"] in {True, False}
    assert r["phase6_acceptance_allowed"] in {True, False}
    assert r["next_phase"] != ""
    assert r["phase7_start_allowed"] in {True, False}
    assert r["phase8_start_allowed"] is False
    for k in ["execution_allowed","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","firewall_apply_authorized","iptables_restore_authorized","usage_automation_authorized","abuse_automation_authorized"]:
        assert r[k] is False
