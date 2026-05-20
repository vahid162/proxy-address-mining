import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.domain.production import ManualCanaryExecutionRunPreparationRequest
from mpf.interfaces.cli import app
from mpf.services import phase11_manual_canary_execution_run_preparation_service

RUNNER = CliRunner()


def test_service_default_ready_and_fail_closed_flags() -> None:
    r = phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report(ManualCanaryExecutionRunPreparationRequest())
    assert r["component"] == "phase11_manual_canary_execution_run_preparation"
    assert r["final_decision"] == "READY_FOR_FARM5_SYNC_EVIDENCE"
    assert r["authorization_status"] == "MANUAL_CANARY_EXECUTION_RUN_PREPARATION_NON_AUTHORIZING"
    assert r["execution_allowed"] is False
    assert r["actual_canary_execution_performed"] is False
    assert r["mutation_performed"] is False
    assert r["customer_db_mutation_performed"] is False
    assert r["firewall_mutation_performed"] is False
    assert r["nat_mutation_performed"] is False
    assert r["production_traffic_enabled"] is False
    assert all(v is False for v in r["safety_flags"].values())


def test_blockers_and_validation_cases() -> None:
    assert phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report(ManualCanaryExecutionRunPreparationRequest(requested_action="execute"))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report(ManualCanaryExecutionRunPreparationRequest(require_operator_confirmation=False))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report(ManualCanaryExecutionRunPreparationRequest(require_execution_gate_evidence=False))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report(ManualCanaryExecutionRunPreparationRequest(lane="zec"))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report(ManualCanaryExecutionRunPreparationRequest(port=60010))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report(ManualCanaryExecutionRunPreparationRequest(miners=1, maxconn=2))["final_decision"] == "BLOCKED"


def test_cli_command_json_and_service_path(monkeypatch) -> None:
    result = RUNNER.invoke(app, ["production", "canary-execution-run-prep", "--output", "json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["component"] == "phase11_manual_canary_execution_run_preparation"

    called = {"ok": False}

    def _fake(_request: ManualCanaryExecutionRunPreparationRequest) -> dict[str, object]:
        called["ok"] = True
        return {"component": "phase11_manual_canary_execution_run_preparation", "final_decision": "BLOCKED", "authorization_status": "MANUAL_CANARY_EXECUTION_RUN_PREPARATION_NON_AUTHORIZING", "execution_allowed": False, "mutation_performed": False, "blockers": [], "validation_errors": []}

    monkeypatch.setattr("mpf.interfaces.cli.phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report", _fake)
    result2 = RUNNER.invoke(app, ["production", "canary-execution-run-prep", "--output", "json"])
    assert result2.exit_code == 0
    assert called["ok"] is True


def test_docs_and_plan_alignment() -> None:
    d = Path("docs/PHASE_11D_MANUAL_CANARY_EXECUTION_RUN_PREPARATION.md").read_text(encoding="utf-8")
    assert "mpf production canary-execution-run-prep --output json" in d
    assert "does **not** authorize actual execution" in d

    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Latest recorded farm5 sync evidence is 0.1.149." in readme

    rem = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "latest recorded farm5 sync evidence is 0.1.149" in rem
    assert "next target after this PR: farm5 sync/test evidence for the operator-reviewed manual canary execution run preparation package" in rem
    assert "Current accepted phase is Phase 10." in rem
    assert "Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in rem
    assert "Phase 11 is accepted" not in rem
    assert "production traffic remains none" in rem
    assert "firewall apply remains no" in rem
    assert "abuse automation remains no" in rem
    assert "customer onboarding remains db_only" in rem
