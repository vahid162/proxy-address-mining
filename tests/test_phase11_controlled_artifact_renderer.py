from __future__ import annotations

from dataclasses import replace

from mpf.services.phase11_controlled_artifact_reapply_core import build_plan, classify_controlled_artifacts, render_payload
from mpf.services.firewall_restore_payload_renderer import render_restore_contract
from tests.test_phase11_controlled_artifact_reapply import PHASE, customers, lanes, target


def _plan():
    return build_plan(lanes=lanes(), customers=customers(whitelist=True), backend_target=target(), phase_status_text=PHASE)


def test_renderer_outputs_executable_source_backed_rules_without_placeholders():
    plan = _plan()
    payload = plan["payload"]
    assert plan["final_decision"] == "CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY"
    assert "# mpf:planned-only" not in payload
    assert "--connlimit-above 10" in payload
    assert "--hashlimit-above 60/minute" in payload
    assert "--hashlimit-burst 10" in payload
    assert "--hashlimit-mode srcip" in payload
    assert "-s 203.0.113.10/32" in payload
    assert "-s 203.0.113.11/32" in payload
    assert "-j MPFC_20001" in payload
    assert "-j DNAT --to-destination 172.19.0.5:60010" in payload
    assert "127.0.0.1" not in payload
    assert "172.18.0.3" not in payload


def test_renderer_rejects_duplicate_unsupported_and_historical_target():
    plan = _plan()["desired_state"]["planner"]
    # Rebuild typed plan through service to avoid importing private helpers.
    from mpf.services import firewall_planner_service

    typed = firewall_planner_service.build_plan(lanes=lanes(), customers=customers(), planner_customer_source="postgresql_snapshot", db_customer_input_loaded=True)
    typed.rules.append(typed.rules[0])
    assert any(e.code == "duplicate_rule_key" for e in render_restore_contract(typed).errors)

    typed = firewall_planner_service.build_plan(lanes=lanes(), customers=customers(), planner_customer_source="postgresql_snapshot", db_customer_input_loaded=True)
    typed.rules[0] = replace(typed.rules[0], rule_kind="unsupported")
    assert any(e.code == "unsupported_rule_kind" for e in render_restore_contract(typed).errors)

    blocked = build_plan(lanes=lanes(), customers=customers(), backend_target=target(ip="172.18.0.3"), phase_status_text=PHASE)
    assert "historical_backend_target_forbidden" in blocked["blockers"]


def test_classifier_exact_missing_partial_stale_duplicate_ipv6_and_unrelated_ignored():
    plan = _plan()
    desired = plan["desired_state"]
    full_text = "\n".join(item.split(":", 1)[1] for item in desired["artifact_lines"])
    assert classify_controlled_artifacts(iptables_save_text=full_text, ip6tables_save_text="", desired_state=desired)["status"] == "exact_present"
    assert classify_controlled_artifacts(iptables_save_text="", ip6tables_save_text="", desired_state=desired)["status"] == "exact_missing"
    partial = "\n".join(item.split(":", 1)[1] for item in desired["artifact_lines"][:3])
    assert classify_controlled_artifacts(iptables_save_text=partial, ip6tables_save_text="", desired_state=desired)["status"] == "safe_exact_partial"
    stale = full_text.replace("172.19.0.5:60010", "172.19.0.6:60010", 1)
    assert "stale_target_detected" in classify_controlled_artifacts(iptables_save_text=stale, ip6tables_save_text="", desired_state=desired)["blockers"]
    dup = desired["artifact_lines"][0].split(":", 1)[1] + "\n" + desired["artifact_lines"][0].split(":", 1)[1]
    assert "duplicate_controlled_artifact_detected" in classify_controlled_artifacts(iptables_save_text=dup, ip6tables_save_text="", desired_state=desired)["blockers"]
    assert "unknown_mpf_artifacts_detected" in classify_controlled_artifacts(iptables_save_text="", ip6tables_save_text="-A INPUT -m comment --comment mpf:x -j ACCEPT", desired_state=desired)["blockers"]
    assert classify_controlled_artifacts(iptables_save_text="-A INPUT -j ACCEPT", ip6tables_save_text="", desired_state=desired)["unknown_mpf"] == []


def test_render_payload_blocks_forbidden_operations_and_is_deterministic():
    missing = _plan()["artifact_classification"]["exact_missing"]
    p1, h1, b1 = render_payload(missing)
    p2, h2, b2 = render_payload(missing)
    assert (p1, h1, b1) == (p2, h2, b2)
    assert b1 == []
    _, _, blockers = render_payload(["raw:-F INPUT"])
    assert "payload_table_not_allowed" in blockers
