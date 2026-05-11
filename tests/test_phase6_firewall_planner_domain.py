from __future__ import annotations

import json

from mpf.domain.firewall import FirewallPlanMessage, FirewallPlanResult


def test_plan_with_errors_is_not_applyable_and_json_serializable() -> None:
    plan = FirewallPlanResult()
    plan.errors.append(FirewallPlanMessage(code="x", message="err", severity="error"))
    plan.finalize()
    assert plan.applyable is False
    payload = plan.to_dict()
    assert payload["firewall_change"] == "planned_only"
    assert payload["nat_change"] == "planned_only"
    assert payload["runtime_change"] == "no"
    json.dumps(payload, sort_keys=True)


def test_human_output_includes_warning_and_error() -> None:
    plan = FirewallPlanResult()
    plan.warnings.append(FirewallPlanMessage(code="w", message="warn", severity="warning"))
    plan.errors.append(FirewallPlanMessage(code="e", message="err", severity="error"))
    plan.finalize()
    text = plan.to_human()
    assert "WARNING [w] warn" in text
    assert "ERROR [e] err" in text


def test_human_and_json_include_planner_customer_source_fields() -> None:
    plan = FirewallPlanResult(planner_customer_source="config_only", db_customer_input_loaded=False)
    payload = plan.to_dict()
    assert payload["planner_customer_source"] == "config_only"
    assert payload["db_customer_input_loaded"] is False
    text = plan.to_human()
    assert "planner_customer_source: config_only" in text
    assert "db_customer_input_loaded: false" in text
