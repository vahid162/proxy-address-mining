from __future__ import annotations

import json

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import phase11_production_readiness_service

RUNNER = CliRunner()


def test_phase11_readiness_service_identity_and_fail_closed() -> None:
    report = phase11_production_readiness_service.build_phase11_production_readiness_report()
    assert report["component"] == "phase11_production_readiness"
    assert report["phase"] == "Phase 11A — Production readiness inventory"
    assert report["final_decision"] in {"BLOCKED", "READY_FOR_SERVER_SYNC_EVIDENCE"}
    assert report["execution_allowed"] is False
    assert report["authorization_status"] == "REPORT_ONLY_NON_AUTHORIZING"


def test_phase11_readiness_safety_flags_all_false() -> None:
    report = phase11_production_readiness_service.build_phase11_production_readiness_report()
    assert all(value is False for value in report["safety_flags"].values())


def test_phase11_readiness_contains_required_blockers_and_gate_wording() -> None:
    report = phase11_production_readiness_service.build_phase11_production_readiness_report()
    blockers = "\n".join(report["blockers"])
    assert "farm5 sync/test evidence required after merge" in blockers
    assert "controlled CLI canary remains future Phase 11B/11C/11D gated" in blockers
    assert "firewall apply remains forbidden" in blockers
    assert "customer onboarding remains db_only" in blockers
    gate = report["current_gate"]
    assert gate["accepted_phase"] == "Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5"
    assert gate["working_phase"] == "Phase 11 — Production / Customer Activation Gate planning/readiness"


def test_phase11_cli_command_exists_and_json_output_valid() -> None:
    result = RUNNER.invoke(app, ["production", "readiness", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["component"] == "phase11_production_readiness"
    assert data["execution_allowed"] is False
    assert data["readiness_checks"]["cli_command_defined"] is True
    assert data["readiness_checks"]["ai_safe_runtime_first_present"] is True
    assert data["readiness_checks"]["no_runtime_authorization"] is True
    assert data["safety_flags"]["controlled_cli_canary_authorized"] is False
    assert data["safety_flags"]["firewall_apply_authorized"] is False
    assert data["safety_flags"]["customer_nat_authorized"] is False
    assert data["safety_flags"]["customer_firewall_rules_authorized"] is False
    assert data["safety_flags"]["abuse_automation_authorized"] is False
    assert data["safety_flags"]["ui_authorized"] is False
    assert data["safety_flags"]["telegram_authorized"] is False
