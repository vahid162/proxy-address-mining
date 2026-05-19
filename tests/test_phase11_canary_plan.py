from __future__ import annotations

import json

from typer.testing import CliRunner

from mpf.domain.production import CanaryPlanRequest
from mpf.interfaces.cli import app
from mpf.services import phase11_canary_plan_service

RUNNER = CliRunner()


def test_phase11_canary_plan_service_identity_and_fail_closed() -> None:
    report = phase11_canary_plan_service.build_phase11_canary_plan_report(CanaryPlanRequest(customer_key="canary-btc-001"))
    assert report["component"] == "phase11_canary_plan"
    assert report["phase"] == "Phase 11B — CLI canary plan/report only"
    assert report["execution_allowed"] is False
    assert report["mutation_performed"] is False
    assert report["report_only"] is True


def test_phase11_canary_plan_safety_flags_false_and_preview_only() -> None:
    report = phase11_canary_plan_service.build_phase11_canary_plan_report(CanaryPlanRequest(customer_key="canary-btc-001"))
    assert all(v is False for v in report["safety_flags"].values())
    assert report["preview"]["would_generate_customer_nat_preview"] is True
    assert report["preview"]["would_generate_customer_firewall_rules_preview"] is True


def test_phase11_canary_blockers_and_intent_present() -> None:
    req = CanaryPlanRequest(customer_key="canary-btc-001", lane="btc", port=20001, name="Phase 11 canary")
    report = phase11_canary_plan_service.build_phase11_canary_plan_report(req)
    blockers = "\n".join(report["blockers"])
    assert "farm5 Phase 11A sync/test evidence required" in blockers
    assert "actual canary execution remains forbidden" in blockers
    assert "firewall apply remains forbidden" in blockers
    assert report["canary_intent"]["customer_key"] == "canary-btc-001"


def test_phase11_canary_cli_exists_and_json_output_valid() -> None:
    result = RUNNER.invoke(app, ["production", "canary-plan", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["component"] == "phase11_canary_plan"
    assert data["execution_allowed"] is False
    assert data["authorization_status"] == "REPORT_ONLY_NON_AUTHORIZING"
    assert data["safety_flags"]["firewall_apply_authorized"] is False


def test_phase11_canary_cli_calls_service_layer(monkeypatch) -> None:
    called = {"ok": False}

    def _fake(req):
        called["ok"] = True
        return {"component": "phase11_canary_plan", "final_decision": "BLOCKED", "authorization_status": "REPORT_ONLY_NON_AUTHORIZING", "execution_allowed": False, "report_only": True, "mutation_performed": False, "blockers": [], "validation_errors": []}

    monkeypatch.setattr("mpf.interfaces.cli.phase11_canary_plan_service.build_phase11_canary_plan_report", _fake)
    result = RUNNER.invoke(app, ["production", "canary-plan", "--output", "json"])
    assert result.exit_code == 0
    assert called["ok"] is True
