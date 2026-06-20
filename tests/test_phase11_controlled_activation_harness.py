from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.domain.production import ControlledActivationHarnessRequest
from mpf.interfaces.cli import app
from mpf.services import phase11_controlled_activation_harness_service

RUNNER = CliRunner()


def test_service_identity_and_fail_closed_flags() -> None:
    r = phase11_controlled_activation_harness_service.build_phase11_controlled_activation_harness_report(ControlledActivationHarnessRequest())
    assert r["component"] == "phase11_controlled_activation_harness"
    assert r["phase"] == "Phase 11C — Controlled activation harness"
    assert r["execution_allowed"] is False
    assert r["mutation_performed"] is False
    assert r["live_apply_performed"] is False
    assert r["customer_db_mutation_performed"] is False
    assert r["firewall_mutation_performed"] is False
    assert r["nat_mutation_performed"] is False
    assert r["conntrack_mutation_performed"] is False
    assert r["harness_mode"] is True
    assert r["report_only"] is False
    assert all(v is False for v in r["safety_flags"].values())


def test_activation_package_and_blockers_present() -> None:
    r = phase11_controlled_activation_harness_service.build_phase11_controlled_activation_harness_report(ControlledActivationHarnessRequest())
    assert r["activation_package"]["would_prepare_customer_nat_preview"] is True
    assert r["activation_package"]["would_prepare_customer_firewall_rules_preview"] is True
    blockers = "\n".join(r["blockers"])
    assert "farm5 Phase 11C sync/test evidence required after merge" in blockers
    assert "firewall apply remains forbidden in this PR" in blockers
    assert "customer NAT/customer firewall rules remain preview-only" in blockers
    assert "production traffic remains none" in blockers


def test_apply_no_dry_run_and_no_confirmation_are_blocked() -> None:
    r_apply = phase11_controlled_activation_harness_service.build_phase11_controlled_activation_harness_report(ControlledActivationHarnessRequest(requested_action="apply"))
    assert r_apply["final_decision"] == "BLOCKED"
    assert r_apply["execution_boundary"]["requested_apply_blocked"] is True

    r_no_dry = phase11_controlled_activation_harness_service.build_phase11_controlled_activation_harness_report(ControlledActivationHarnessRequest(dry_run=False))
    assert r_no_dry["final_decision"] == "BLOCKED"
    assert r_no_dry["execution_boundary"]["no_dry_run_blocked"] is True

    r_no_confirmation = phase11_controlled_activation_harness_service.build_phase11_controlled_activation_harness_report(ControlledActivationHarnessRequest(require_operator_confirmation=False))
    assert r_no_confirmation["final_decision"] == "BLOCKED"
    assert r_no_confirmation["execution_allowed"] is False
    assert r_no_confirmation["mutation_performed"] is False
    assert "operator confirmation remains required before any controlled activation step" in r_no_confirmation["validation_errors"]


def test_cli_json_valid_and_calls_service_layer(monkeypatch) -> None:
    result = RUNNER.invoke(app, ["production", "activation-harness", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["component"] == "phase11_controlled_activation_harness"

    called = {"ok": False}

    def _fake(req):
        called["ok"] = True
        return {"component": "phase11_controlled_activation_harness", "final_decision": "BLOCKED", "authorization_status": "CONTROLLED_HARNESS_NON_AUTHORIZING", "execution_allowed": False, "harness_mode": True, "report_only": False, "mutation_performed": False, "blockers": [], "validation_errors": []}

    monkeypatch.setattr("mpf.interfaces.cli.phase11_controlled_activation_harness_service.build_phase11_controlled_activation_harness_report", _fake)
    result2 = RUNNER.invoke(app, ["production", "activation-harness", "--output", "json"])
    assert result2.exit_code == 0
    assert called["ok"] is True


def test_static_no_forbidden_runtime_calls_in_new_surface() -> None:
    files = [
        Path("mpf/services/phase11_controlled_activation_harness_service.py"),
    ]
    joined = "\n".join(f.read_text(encoding="utf-8") for f in files)
    for token in ["iptables-restore", "subprocess.run", "os.system", "docker"]:
        assert token not in joined


def test_phase_status_not_marked_phase11_accepted() -> None:
    t = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 10" in t
    assert "current_working_phase: Phase 11" in t