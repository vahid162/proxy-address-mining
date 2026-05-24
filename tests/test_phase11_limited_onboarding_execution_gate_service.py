import json
from pathlib import Path

from typer.testing import CliRunner

from mpf import __version__
from mpf.interfaces.cli import app
from mpf.services.phase11_limited_onboarding_execution_gate_service import build_phase11_limited_onboarding_execution_gate_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path("configs/mpf.example.yaml"))


def _base():
    return {
        "component": "phase11_limited_onboarding_gate",
        "expected_version": "0.1.198",
        "repository_version": "0.1.198",
        "phase11d_canary_accepted": True,
        "phase11e_gate_ready": True,
        "phase11e_execution_allowed": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "production_traffic_enabled": False,
        "no_onboarding_authorized": True,
        "mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "db_mutation_performed": False,
        "final_decision": "PHASE11E_LIMITED_ONBOARDING_GATE_READY",
        "next_required_step": "phase11e_limited_onboarding_execution_gate_pr",
        "blockers": [],
        "warnings": [],
    }


def _write(tmp_path, data):
    p = tmp_path / "gate.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _call(path, **kw):
    args = dict(
        expected_version=__version__, farm5_baseline_version="0.1.168", limited_onboarding_gate_json=path,
        candidate_customer_key="limited-btc-001", candidate_lane="btc", candidate_public_port=20101,
        candidate_backend_target="172.18.0.3:60010", candidate_description="desc", operator="vahid", reason="ok",
        operator_confirmed=True, i_understand_this_does_not_onboard_customer=True,
        i_understand_no_firewall_apply_yet=True, i_understand_no_production_traffic_yet=True,
        i_understand_next_pr_must_execute_controlled_single_customer=True,
        i_confirm_rollback_plan_required=True, i_confirm_restart_test_required=True,
        i_confirm_abuse_1h_coverage_required=True,
    )
    args.update(kw)
    return build_phase11_limited_onboarding_execution_gate_report(_cfg(), **args)


def test_execution_gate_ready_from_valid_limited_onboarding_gate(tmp_path):
    r = _call(_write(tmp_path, _base())); assert r["final_decision"] == "PHASE11E_LIMITED_ONBOARDING_EXECUTION_GATE_READY"

def test_blocks_missing_limited_onboarding_gate_json(tmp_path):
    r = _call(tmp_path / "none.json"); assert "limited_onboarding_gate_json_missing" in r["blockers"]

def test_blocks_invalid_limited_onboarding_gate_json(tmp_path):
    p = tmp_path / "x.json"; p.write_text("{"); r = _call(p); assert "limited_onboarding_gate_json_invalid" in r["blockers"]

def test_blocks_when_limited_onboarding_gate_not_ready(tmp_path):
    d = _base(); d["phase11e_gate_ready"] = False; r = _call(_write(tmp_path, d)); assert "limited_onboarding_gate_not_ready" in r["blockers"]

def test_blocks_when_limited_onboarding_gate_execution_allowed_true(tmp_path):
    d = _base(); d["phase11e_execution_allowed"] = True; r = _call(_write(tmp_path, d)); assert "limited_onboarding_gate_not_ready" in r["blockers"]

def test_blocks_when_limited_onboarding_allowed_true(tmp_path):
    d = _base(); d["limited_onboarding_allowed"] = True; r = _call(_write(tmp_path, d)); assert "limited_onboarding_gate_safety_boundary_open" in r["blockers"]

def test_blocks_when_production_traffic_enabled_true(tmp_path):
    d = _base(); d["production_traffic_enabled"] = True; r = _call(_write(tmp_path, d)); assert "limited_onboarding_gate_safety_boundary_open" in r["blockers"]

def test_blocks_when_no_onboarding_authorized_false(tmp_path):
    d = _base(); d["no_onboarding_authorized"] = False; r = _call(_write(tmp_path, d)); assert "limited_onboarding_gate_safety_boundary_open" in r["blockers"]

def test_blocks_when_any_mutation_flag_true(tmp_path):
    d = _base(); d["db_mutation_performed"] = True; r = _call(_write(tmp_path, d)); assert "limited_onboarding_gate_mutation_flag_detected" in r["blockers"]

def test_blocks_candidate_key_without_limited_btc_prefix(tmp_path):
    r = _call(_write(tmp_path, _base()), candidate_customer_key="foo"); assert "candidate_customer_key_invalid" in r["blockers"]

def test_blocks_candidate_lane_not_btc(tmp_path):
    r = _call(_write(tmp_path, _base()), candidate_lane="zec"); assert "candidate_lane_not_allowed" in r["blockers"]

def test_blocks_candidate_port_20001_canary_collision(tmp_path):
    r = _call(_write(tmp_path, _base()), candidate_public_port=20001); assert "candidate_public_port_collides_with_canary" in r["blockers"]

def test_blocks_candidate_port_out_of_range(tmp_path):
    r = _call(_write(tmp_path, _base()), candidate_public_port=20130); assert "candidate_public_port_out_of_range" in r["blockers"]

def test_blocks_candidate_backend_target_wrong(tmp_path):
    r = _call(_write(tmp_path, _base()), candidate_backend_target="172.18.0.3:60011"); assert "candidate_backend_target_invalid" in r["blockers"]

def test_blocks_missing_candidate_description(tmp_path):
    r = _call(_write(tmp_path, _base()), candidate_description=""); assert "candidate_description_missing" in r["blockers"]

def test_blocks_missing_operator_confirmation(tmp_path):
    r = _call(_write(tmp_path, _base()), operator_confirmed=False); assert "operator_not_confirmed" in r["blockers"]

def test_blocks_missing_no_customer_onboarding_boundary_confirmation(tmp_path):
    r = _call(_write(tmp_path, _base()), i_understand_this_does_not_onboard_customer=False); assert "no_customer_onboarding_boundary_not_confirmed" in r["blockers"]

def test_blocks_missing_no_firewall_apply_boundary_confirmation(tmp_path):
    r = _call(_write(tmp_path, _base()), i_understand_no_firewall_apply_yet=False); assert "no_firewall_apply_boundary_not_confirmed" in r["blockers"]

def test_blocks_missing_no_production_traffic_boundary_confirmation(tmp_path):
    r = _call(_write(tmp_path, _base()), i_understand_no_production_traffic_yet=False); assert "no_production_traffic_boundary_not_confirmed" in r["blockers"]

def test_blocks_missing_next_pr_execution_boundary_confirmation(tmp_path):
    r = _call(_write(tmp_path, _base()), i_understand_next_pr_must_execute_controlled_single_customer=False); assert "next_pr_execution_boundary_not_confirmed" in r["blockers"]

def test_blocks_missing_rollback_requirement_confirmation(tmp_path):
    r = _call(_write(tmp_path, _base()), i_confirm_rollback_plan_required=False); assert "rollback_plan_requirement_not_confirmed" in r["blockers"]

def test_blocks_missing_restart_requirement_confirmation(tmp_path):
    r = _call(_write(tmp_path, _base()), i_confirm_restart_test_required=False); assert "restart_test_requirement_not_confirmed" in r["blockers"]

def test_blocks_missing_abuse_1h_requirement_confirmation(tmp_path):
    r = _call(_write(tmp_path, _base()), i_confirm_abuse_1h_coverage_required=False); assert "abuse_1h_requirement_not_confirmed" in r["blockers"]

def test_cli_limited_onboarding_execution_gate_json_smoke(tmp_path):
    p = _write(tmp_path, _base()); r = CliRunner().invoke(app, ["production", "limited-onboarding-execution-gate", "--expected-version", __version__, "--farm5-baseline-version", "0.1.168", "--limited-onboarding-gate-json", str(p), "--candidate-customer-key", "limited-btc-001", "--candidate-lane", "btc", "--candidate-public-port", "20101", "--candidate-backend-target", "172.18.0.3:60010", "--candidate-description", "desc", "--operator", "vahid", "--reason", "ok", "--operator-confirmed", "--i-understand-this-does-not-onboard-customer", "--i-understand-no-firewall-apply-yet", "--i-understand-no-production-traffic-yet", "--i-understand-next-pr-must-execute-controlled-single-customer", "--i-confirm-rollback-plan-required", "--i-confirm-restart-test-required", "--i-confirm-abuse-1h-coverage-required", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert r.exit_code == 0 and "phase11_limited_onboarding_execution_gate" in r.stdout

def test_cli_limited_onboarding_execution_gate_human_smoke(tmp_path):
    p = _write(tmp_path, _base()); r = CliRunner().invoke(app, ["production", "limited-onboarding-execution-gate", "--expected-version", __version__, "--farm5-baseline-version", "0.1.168", "--limited-onboarding-gate-json", str(p), "--candidate-customer-key", "limited-btc-001", "--candidate-lane", "btc", "--candidate-public-port", "20101", "--candidate-backend-target", "172.18.0.3:60010", "--candidate-description", "desc", "--operator", "vahid", "--reason", "ok", "--operator-confirmed", "--i-understand-this-does-not-onboard-customer", "--i-understand-no-firewall-apply-yet", "--i-understand-no-production-traffic-yet", "--i-understand-next-pr-must-execute-controlled-single-customer", "--i-confirm-rollback-plan-required", "--i-confirm-restart-test-required", "--i-confirm-abuse-1h-coverage-required", "--output", "human", "--config", "configs/mpf.example.yaml"])
    assert r.exit_code == 0 and "final_decision:" in r.stdout


def test_blocks_expected_version_mismatch(tmp_path):
    r = _call(_write(tmp_path, _base()), expected_version="0.1.198")
    assert r["final_decision"] == "BLOCKED"
    assert r["phase11e_execution_gate_ready"] is False
    assert r["phase11e_execution_allowed"] is False
    assert r["customer_created"] is False
    assert r["mutation_performed"] is False
    assert r["db_mutation_performed"] is False
    assert r["firewall_mutation_performed"] is False
    assert r["nat_mutation_performed"] is False
    assert r["conntrack_mutation_performed"] is False
    assert r["docker_mutation_performed"] is False
    assert "expected_version_mismatch" in r["blockers"]


def test_blocks_farm5_baseline_version_mismatch(tmp_path):
    r = _call(_write(tmp_path, _base()), farm5_baseline_version="0.1.167")
    assert r["final_decision"] == "BLOCKED"
    assert r["phase11e_execution_gate_ready"] is False
    assert r["phase11e_execution_allowed"] is False
    assert r["customer_created"] is False
    assert r["mutation_performed"] is False
    assert r["db_mutation_performed"] is False
    assert r["firewall_mutation_performed"] is False
    assert r["nat_mutation_performed"] is False
    assert r["conntrack_mutation_performed"] is False
    assert r["docker_mutation_performed"] is False
    assert "farm5_baseline_version_mismatch" in r["blockers"]
