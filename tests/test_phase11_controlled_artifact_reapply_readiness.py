from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import phase11_controlled_artifact_reapply_readiness_service as readiness
from mpf.services.phase11_controlled_artifact_reapply_core import NO_REAPPLY as CORE_NO_REAPPLY, build_plan
from tests.test_phase11_controlled_artifact_reapply import PHASE, customers, lanes, target


def _plan(status="ready", *, unknown=False, public=False, blocked=False):
    backend = target()
    if public:
        backend["backend_public_exposure"] = True
    text = "*filter\nCOMMIT\n"
    if unknown:
        text = '*filter\n-A INPUT -m comment --comment "mpf:phase11:customer:unknown:btc:29999" -j ACCEPT\nCOMMIT\n'
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=backend, iptables_save_text=text, ip6tables_save_text="*filter\nCOMMIT\n", phase_status_text=PHASE)
    if blocked:
        plan["final_decision"] = "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"
        plan["blockers"] = ["synthetic_live_plan_blocked"]
    if status == "exact_present":
        plan = build_plan(lanes=lanes(), customers=customers(), backend_target=backend, iptables_save_text=plan["payload"], ip6tables_save_text="*filter\nCOMMIT\n", phase_status_text=PHASE)
        assert plan["final_decision"] == CORE_NO_REAPPLY
        assert plan["artifact_classification"]["status"] == "exact_present"
    return plan


def _patch(monkeypatch, plan):
    monkeypatch.setattr(readiness.gate_service, "build_phase11_current_controlled_artifact_gate_report", lambda **kwargs: {"blockers": [], "unknown_mpf_artifacts": [], "current_phase_gate_ok": True})
    monkeypatch.setattr(readiness.fix_service, "run_phase11_restart_autostart_persistence_fix_plan", lambda config_path: {"safety_blockers": []})
    monkeypatch.setattr(readiness.package_service, "run_controlled_artifact_reapply_plan", lambda config_path, expected_version=None: plan)


def test_ready_path_keeps_execution_and_later_phase_gates_closed(monkeypatch):
    _patch(monkeypatch, _plan())
    report = readiness.run_phase11_controlled_artifact_reapply_readiness()
    assert report["final_decision"] == readiness.READY
    assert report["live_ready_package_available"] is True
    assert report["production_execution_available"] is False
    assert report["controlled_artifact_execute_available"] is False
    assert report["iptables_restore_invocation_allowed"] is False
    for key in ["mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed", "phase12_start_allowed"]:
        assert report[key] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"
    assert report["package_id"]
    assert report["package_sha256"]
    assert report["execution_precondition_fingerprint"]


def test_blocked_when_unknown_mpf_artifacts(monkeypatch):
    _patch(monkeypatch, _plan(unknown=True))
    report = readiness.run_phase11_controlled_artifact_reapply_readiness()
    assert report["final_decision"] == readiness.BLOCKED
    assert report["unknown_mpf_artifacts"]


def test_blocked_when_forbidden_public_runtime_exposure(monkeypatch):
    _patch(monkeypatch, _plan(public=True))
    report = readiness.run_phase11_controlled_artifact_reapply_readiness()
    assert report["final_decision"] == readiness.BLOCKED
    assert report["forbidden_public_runtime_exposure"] is True


def test_blocked_when_package_verification_has_drift(monkeypatch):
    plan = _plan()
    _patch(monkeypatch, plan)
    real = readiness.verification_service.build_controlled_artifact_reapply_verify_report
    def drift(*, package, live_plan=None, config_path=None, expected_version=None):
        package = dict(package)
        package["desired_state_hash"] = "drift"
        return real(package=package, live_plan=live_plan, expected_version=expected_version)
    monkeypatch.setattr(readiness.verification_service, "build_controlled_artifact_reapply_verify_report", drift)
    report = readiness.run_phase11_controlled_artifact_reapply_readiness()
    assert report["final_decision"] == readiness.BLOCKED
    assert "desired_state_hash_mismatch" in report["blockers"]


def test_blocked_when_live_plan_final_decision_is_blocked(monkeypatch):
    _patch(monkeypatch, _plan(blocked=True))
    report = readiness.run_phase11_controlled_artifact_reapply_readiness()
    assert report["final_decision"] == readiness.BLOCKED
    assert "live_plan_final_decision_blocked" in report["blockers"]


def test_no_reapply_path_when_exact_artifacts_present(monkeypatch):
    _patch(monkeypatch, _plan(status="exact_present"))
    report = readiness.run_phase11_controlled_artifact_reapply_readiness()
    assert report["final_decision"] == readiness.NO_REAPPLY
    assert report["live_ready_package_available"] is False


def test_verification_uses_fresh_second_live_plan_and_blocks_drift(monkeypatch):
    ready_plan = _plan()
    drifted_plan = dict(ready_plan)
    drifted_plan["desired_state_hash"] = "fresh-live-plan-drift"
    calls = iter([ready_plan, drifted_plan])
    monkeypatch.setattr(readiness.gate_service, "build_phase11_current_controlled_artifact_gate_report", lambda **kwargs: {"blockers": [], "unknown_mpf_artifacts": [], "current_phase_gate_ok": True})
    monkeypatch.setattr(readiness.fix_service, "run_phase11_restart_autostart_persistence_fix_plan", lambda config_path: {"safety_blockers": []})
    monkeypatch.setattr(readiness.package_service, "run_controlled_artifact_reapply_plan", lambda config_path, expected_version=None: next(calls))

    report = readiness.run_phase11_controlled_artifact_reapply_readiness()

    assert report["final_decision"] == readiness.BLOCKED
    assert "desired_state_hash_mismatch" in report["blockers"]


def test_verification_uses_fresh_second_live_plan_and_blocks_fresh_plan_failure(monkeypatch):
    ready_plan = _plan()
    blocked_fresh_plan = dict(ready_plan)
    blocked_fresh_plan["final_decision"] = "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"
    blocked_fresh_plan["blockers"] = ["fresh_live_plan_blocked"]
    calls = iter([ready_plan, blocked_fresh_plan])
    monkeypatch.setattr(readiness.gate_service, "build_phase11_current_controlled_artifact_gate_report", lambda **kwargs: {"blockers": [], "unknown_mpf_artifacts": [], "current_phase_gate_ok": True})
    monkeypatch.setattr(readiness.fix_service, "run_phase11_restart_autostart_persistence_fix_plan", lambda config_path: {"safety_blockers": []})
    monkeypatch.setattr(readiness.package_service, "run_controlled_artifact_reapply_plan", lambda config_path, expected_version=None: next(calls))

    report = readiness.run_phase11_controlled_artifact_reapply_readiness()

    assert report["final_decision"] == readiness.BLOCKED
    assert "fresh_live_plan_blocked" in report["blockers"]


def test_cli_json_command_stable_closed_flags(monkeypatch):
    monkeypatch.setattr(readiness, "run_phase11_controlled_artifact_reapply_readiness", lambda *a, **k: {"component": "phase11_controlled_artifact_reapply_readiness", "final_decision": readiness.BLOCKED, "production_execution_available": False, "controlled_artifact_execute_available": False, "iptables_restore_invocation_allowed": False, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no", "mutation_performed": False, "blockers": ["x"]})
    result = CliRunner().invoke(app, ["production", "controlled-artifact-reapply-readiness", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["component"] == "phase11_controlled_artifact_reapply_readiness"
    assert data["production_execution_available"] is False
    assert data["iptables_restore_invocation_allowed"] is False


def test_cli_exception_fallback_returns_stable_closed_key_set(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(readiness, "run_phase11_controlled_artifact_reapply_readiness", boom)
    result = CliRunner().invoke(app, ["production", "controlled-artifact-reapply-readiness", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["final_decision"] == readiness.BLOCKED
    assert data["next_required_step"] == "prepare_live_ready_controlled_artifact_reapply_package"
    for key in ["mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed", "production_execution_available", "controlled_artifact_execute_available", "iptables_restore_invocation_allowed", "phase12_start_allowed", "live_ready_package_available"]:
        assert data[key] is False
    assert data["worker_enforcement_allowed"] == "no"
    assert data["ui_allowed"] == "no"
    assert data["telegram_allowed"] == "no"


def test_static_safety_no_readiness_execute_or_iptables_restore():
    service = Path("mpf/services/phase11_controlled_artifact_reapply_readiness_service.py").read_text()
    assert "execute_controlled_artifact_reapply_package" not in service
    assert "execute_package" not in service
    assert "iptables-restore" not in service
    script = Path("scripts/phase11_controlled_artifact_reapply.sh").read_text()
    readiness_case = script.split('  readiness)', 1)[1].split('  package)', 1)[0]
    assert "controlled-artifact-reapply-execute" not in readiness_case
    assert "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY" not in readiness_case
    assert "iptables-restore" not in readiness_case


def test_script_readiness_mode_writes_json_and_manifest_without_execute_env_gates(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.txt"
    mpf = bin_dir / "mpf"
    mpf.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        f"pathlib.Path({str(calls)!r}).write_text(' '.join(sys.argv[1:]))\n"
        "assert 'controlled-artifact-reapply-execute' not in sys.argv\n"
        "print(json.dumps({'component':'phase11_controlled_artifact_reapply_readiness','final_decision':'BLOCKED_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE','mutation_performed':False}))\n",
        encoding="utf-8",
    )
    mpf.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{__import__('os').environ['PATH']}")
    monkeypatch.delenv("MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY", raising=False)
    monkeypatch.delenv("MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE", raising=False)
    out = tmp_path / "out"
    import subprocess
    result = subprocess.run(["bash", "scripts/phase11_controlled_artifact_reapply.sh", "--readiness", "--out-dir", str(out)], shell=False, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (out / "controlled-artifact-reapply-readiness.json").exists()
    assert (out / "manifest.sha256").exists()
    assert "controlled-artifact-reapply-readiness" in calls.read_text(encoding="utf-8")
