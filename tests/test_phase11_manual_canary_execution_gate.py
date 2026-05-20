from pathlib import Path

from typer.testing import CliRunner

from mpf.domain.production import ManualCanaryExecutionGateRequest
from mpf.interfaces.cli import app
from mpf.services import phase11_manual_canary_execution_gate_service

RUNNER = CliRunner()


def test_service_default_safe_gate_request() -> None:
    r = phase11_manual_canary_execution_gate_service.build_phase11_manual_canary_execution_gate_report(ManualCanaryExecutionGateRequest())
    assert r["component"] == "phase11_manual_canary_execution_gate"
    assert r["final_decision"] == "READY_FOR_FARM5_SYNC_EVIDENCE"
    assert r["authorization_status"] == "MANUAL_CANARY_EXECUTION_GATE_NON_AUTHORIZING"
    assert r["execution_allowed"] is False
    assert r["mutation_performed"] is False
    assert r["actual_canary_execution_performed"] is False
    assert r["production_traffic_enabled"] is False
    assert all(v is False for v in r["safety_flags"].values())


def test_service_blocks_unsafe_inputs() -> None:
    assert phase11_manual_canary_execution_gate_service.build_phase11_manual_canary_execution_gate_report(ManualCanaryExecutionGateRequest(requested_action="execute"))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_gate_service.build_phase11_manual_canary_execution_gate_report(ManualCanaryExecutionGateRequest(require_operator_confirmation=False))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_gate_service.build_phase11_manual_canary_execution_gate_report(ManualCanaryExecutionGateRequest(lane="zec"))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_gate_service.build_phase11_manual_canary_execution_gate_report(ManualCanaryExecutionGateRequest(port=19999))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_gate_service.build_phase11_manual_canary_execution_gate_report(ManualCanaryExecutionGateRequest(miners=1, maxconn=2))["final_decision"] == "BLOCKED"


def test_cli_json_and_service_path(monkeypatch) -> None:
    result = RUNNER.invoke(app, ["production", "canary-execution-gate", "--output", "json"])
    assert result.exit_code == 0
    assert "phase11_manual_canary_execution_gate" in result.output

    called = {"ok": False}

    def _fake(request):
        called["ok"] = True
        return {"component": "phase11_manual_canary_execution_gate", "final_decision": "BLOCKED", "authorization_status": "MANUAL_CANARY_EXECUTION_GATE_NON_AUTHORIZING", "execution_allowed": False, "mutation_performed": False, "blockers": [], "validation_errors": []}

    monkeypatch.setattr("mpf.interfaces.cli.phase11_manual_canary_execution_gate_service.build_phase11_manual_canary_execution_gate_report", _fake)
    result2 = RUNNER.invoke(app, ["production", "canary-execution-gate", "--output", "json"])
    assert result2.exit_code == 0
    assert called["ok"] is True


def test_docs_and_plan_alignment() -> None:
    d = Path("docs/PHASE_11D_MANUAL_CANARY_EXECUTION_GATE.md").read_text(encoding="utf-8")
    assert "mpf production canary-execution-gate --output json" in d
    assert "does **not** authorize execution" in d

    rem = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "latest recorded farm5 sync evidence is 0.1.151" in rem
    assert "Next target: farm5 sync/test evidence for actual operator-approved manual canary execution run package" in rem
    assert "Phase 11D actual execution remains not accepted" in rem
    assert "Phase 11 is accepted" not in rem
    assert "production traffic remains none" in rem
    assert "firewall apply remains no" in rem
    assert "abuse automation remains no" in rem
    assert "customer onboarding remains db_only" in rem
