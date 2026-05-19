import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.domain.production import ManualCanaryAcceptanceRequest
from mpf.interfaces.cli import app
from mpf.services import phase11_manual_canary_acceptance_service

RUNNER = CliRunner()


def test_service_identity_and_fail_closed_flags() -> None:
    r = phase11_manual_canary_acceptance_service.build_phase11_manual_canary_acceptance_report(ManualCanaryAcceptanceRequest())
    assert r["component"] == "phase11_manual_canary_acceptance"
    assert r["phase"] == "Phase 11D — Manual canary customer acceptance package"
    assert r["execution_allowed"] is False
    assert r["mutation_performed"] is False
    assert r["live_canary_performed"] is False
    assert r["production_traffic_enabled"] is False
    assert r["customer_db_mutation_performed"] is False
    assert r["firewall_mutation_performed"] is False
    assert r["nat_mutation_performed"] is False
    assert r["conntrack_mutation_performed"] is False
    assert r["acceptance_package_mode"] is True


def test_safety_flags_and_acceptance_criteria_and_evidence() -> None:
    r = phase11_manual_canary_acceptance_service.build_phase11_manual_canary_acceptance_report(ManualCanaryAcceptanceRequest())
    assert all(v is False for v in r["safety_flags"].values())
    joined = "\n".join(r["acceptance_criteria"])
    assert "backup/restore/rollback" in joined
    assert "operator explicitly confirms" in joined
    assert "abuse 1h coverage" in joined
    required = r["required_pre_execution_evidence"]
    assert required["production_readiness_required"] is True
    assert required["canary_plan_required"] is True
    assert required["activation_harness_required"] is True


def test_blocked_paths_and_blockers_present() -> None:
    r_accept = phase11_manual_canary_acceptance_service.build_phase11_manual_canary_acceptance_report(ManualCanaryAcceptanceRequest(requested_action="accept"))
    r_execute = phase11_manual_canary_acceptance_service.build_phase11_manual_canary_acceptance_report(ManualCanaryAcceptanceRequest(requested_action="execute"))
    r_no_confirm = phase11_manual_canary_acceptance_service.build_phase11_manual_canary_acceptance_report(ManualCanaryAcceptanceRequest(require_operator_confirmation=False))
    assert r_accept["final_decision"] == "BLOCKED"
    assert r_execute["final_decision"] == "BLOCKED"
    assert r_no_confirm["final_decision"] == "BLOCKED"

    for field in (
        "require_farm5_phase11c_evidence",
        "require_backup_reference",
        "require_restore_plan_reference",
        "require_rollback_plan",
        "require_no_customer_nat_baseline",
        "require_no_customer_firewall_baseline",
        "require_local_only_runtime_baseline",
    ):
        request = ManualCanaryAcceptanceRequest()
        setattr(request, field, False)
        blocked = phase11_manual_canary_acceptance_service.build_phase11_manual_canary_acceptance_report(request)
        assert blocked["final_decision"] == "BLOCKED"

    blockers = "\n".join(r_accept["blockers"])
    assert "Phase 11D package sync/test evidence" in blockers
    assert "actual manual canary execution remains forbidden" in blockers
    assert "firewall apply remains forbidden" in blockers
    assert "production traffic remains none" in blockers


def test_cli_command_exists_json_valid_and_calls_service(monkeypatch) -> None:
    result = RUNNER.invoke(app, ["production", "canary-acceptance", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["component"] == "phase11_manual_canary_acceptance"

    called = {"ok": False}

    def _fake(_request: ManualCanaryAcceptanceRequest) -> dict[str, object]:
        called["ok"] = True
        return {"component": "phase11_manual_canary_acceptance", "final_decision": "BLOCKED", "authorization_status": "MANUAL_CANARY_PACKAGE_NON_AUTHORIZING", "execution_allowed": False, "acceptance_package_mode": True, "mutation_performed": False, "blockers": [], "validation_errors": []}

    monkeypatch.setattr("mpf.interfaces.cli.phase11_manual_canary_acceptance_service.build_phase11_manual_canary_acceptance_report", _fake)
    result2 = RUNNER.invoke(app, ["production", "canary-acceptance", "--output", "json"])
    assert result2.exit_code == 0
    assert called["ok"] is True


def test_no_forbidden_runtime_calls_in_phase11d_service_or_cli() -> None:
    targets = [Path("mpf/services/phase11_manual_canary_acceptance_service.py"), Path("mpf/interfaces/cli.py")]
    forbidden = ["subprocess.run(", "os.system("]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text


def test_phase_status_not_marked_phase11_accepted() -> None:
    content = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 11" not in content
