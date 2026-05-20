from __future__ import annotations

import json

from typer.testing import CliRunner

from mpf.domain.production import ManualCanaryExecutionRunRequest
from mpf.interfaces.cli import app
from mpf.services import phase11_manual_canary_execution_run_service

RUNNER = CliRunner()


def _approved_execute_request() -> ManualCanaryExecutionRunRequest:
    return ManualCanaryExecutionRunRequest(
        requested_action="execute",
        expected_version="0.1.153",
        operator_confirmed=True,
        understand_canary_customer=True,
        understand_firewall_apply=True,
        reviewed_rollback=True,
        fresh_farm5_sync_confirmed=True,
    )


def test_dto_defaults_validate_plan() -> None:
    assert ManualCanaryExecutionRunRequest().validate() == []


def test_dto_execute_requires_approvals_and_expected_version() -> None:
    errors = ManualCanaryExecutionRunRequest(requested_action="execute").validate()
    assert any("operator_confirmed" in e for e in errors)
    assert any("expected_version" in e for e in errors)


def test_dto_guards() -> None:
    assert phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest(lane="zec"))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest(port=20002))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest(customer_key="x"))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest(miners=1, maxconn=2))["final_decision"] == "BLOCKED"


def test_service_plan_mode() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest())
    assert r["component"] == "phase11_manual_canary_execution_run"
    assert r["final_decision"] == "PLAN_READY_FOR_FARM5_SYNC_EVIDENCE"
    assert r["execution_allowed"] is False
    assert r["mutation_performed"] is False
    assert all(v is False for v in r["safety_flags"].values())


def test_execute_mode_without_adapter_is_fail_closed() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request())
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False
    assert r["mutation_performed"] is False
    assert "execution adapter readiness is required" in " ".join(r["blockers"])


def test_execute_mode_with_fake_adapters() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(
        _approved_execute_request(),
        adapters={"simulate_execute": True},
    )
    assert r["final_decision"] == "EXECUTION_READY_REQUIRES_OPERATOR_RUN"
    assert r["execution_allowed"] is True
    assert r["mutation_performed"] is False
    assert r["execution_steps"]


def test_cli_plan_json() -> None:
    result = RUNNER.invoke(app, ["production", "manual-canary-execute", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["component"] == "phase11_manual_canary_execution_run"
    assert data["execution_allowed"] is False
