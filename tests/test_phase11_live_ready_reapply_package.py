from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import phase11_live_ready_reapply_package_service as svc
from mpf.services.phase11_controlled_artifact_reapply_core import SCOPE, build_plan
from mpf.services.phase11_verified_filter_hook_binding_service import binding_backend_target, build_verified_filter_hook_binding_report
from tests.test_phase11_verified_filter_hook_binding import _ready_bundle

PHASE = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
LANES = [{"name": "btc", "enabled": True, "backend_port": 60010}]
CUSTOMERS = [
    {"id": 1, "customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "status": "active", "policy": {"miners": 1, "farms": 1, "maxconn": 10, "rate_per_min": 60, "burst": 10, "ips_mode": "any"}},
    {"id": 2, "customer_key": "limited-btc-001", "lane": "btc", "port": 20101, "status": "active", "policy": {"miners": 1, "farms": 1, "maxconn": 10, "rate_per_min": 60, "burst": 10, "ips_mode": "any"}},
]


def test_ready_path_writes_artifacts_and_keeps_all_execution_gates_closed(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    out = tmp_path / "out"
    report = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=CUSTOMERS, phase_status_text=PHASE, output_dir=out)
    assert report["final_decision"] == svc.READY
    assert report["live_ready_package_available"] is True
    assert report["production_execution_available"] is False
    assert report["controlled_artifact_execute_available"] is False
    assert report["iptables_restore_invocation_allowed"] is False
    assert report["mutation_performed"] is False
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"
    for name in ["controlled-artifact-reapply-plan.json", "controlled-artifact-reapply-package.json", "controlled-artifact-reapply-verify.json", "human-diff.txt", "machine-diff.json", "rollback-plan.json", "manifest.sha256.json"]:
        assert (out / name).exists()


def test_blocked_when_packet_path_evidence_dir_missing(tmp_path):
    report = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=tmp_path / "missing", lanes=LANES, customers=CUSTOMERS, phase_status_text=PHASE)
    assert report["final_decision"] == svc.BLOCKED
    assert "packet_path_evidence_dir_missing" in report["blockers"]


def test_blocked_when_binding_not_ready_and_customer_scope_wrong(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    (bundle / "decision.json").write_text(json.dumps({"final_decision": "BLOCKED"}), encoding="utf-8")
    report = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=CUSTOMERS[:1], phase_status_text=PHASE)
    assert report["final_decision"] == svc.BLOCKED
    assert "verified_filter_hook_binding_not_ready" in report["blockers"]
    assert "controlled_customer_scope_mismatch" in report["blockers"]


def test_blocked_on_public_backend_exposure_unknown_artifacts_and_drift(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    binding = build_verified_filter_hook_binding_report(bundle)
    target = binding_backend_target(binding)
    target["backend_public_exposure"] = True
    drift_plan = build_plan(lanes=LANES, customers=CUSTOMERS, backend_target=target, phase_status_text=PHASE)
    report = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=CUSTOMERS, phase_status_text=PHASE, second_plan=drift_plan)
    assert report["final_decision"] == svc.BLOCKED
    assert "package_verification_drift_or_blocked" in report["blockers"]


def test_stable_package_identity_and_fingerprint_drift(tmp_path, monkeypatch):
    bundle = _ready_bundle(tmp_path, monkeypatch)
    a = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=CUSTOMERS, phase_status_text=PHASE)
    b = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=CUSTOMERS, phase_status_text=PHASE)
    assert a["package_id"] == b["package_id"]
    assert a["package_sha256"] == b["package_sha256"]
    c = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=[{**CUSTOMERS[0], "port": 20002}, CUSTOMERS[1]], phase_status_text=PHASE)
    assert c["execution_precondition_fingerprint"] != a["execution_precondition_fingerprint"]
    assert c["final_decision"] == svc.BLOCKED


def test_generated_live_ready_package_canonical_hash_matches_executor_helper(tmp_path, monkeypatch):
    from mpf.services.phase11_controlled_artifact_reapply_core import _canonical_sha, _package_content_for_hash
    import hashlib

    bundle = _ready_bundle(tmp_path, monkeypatch)
    out = tmp_path / "out"
    report = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=CUSTOMERS, phase_status_text=PHASE, output_dir=out)
    package_path = out / "controlled-artifact-reapply-package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))

    assert report["final_decision"] == svc.READY
    assert package["package_sha256"] == _canonical_sha(_package_content_for_hash(package))
    assert report["package_sha256"] == package["package_sha256"]

    file_sha = hashlib.sha256(package_path.read_bytes()).hexdigest()
    assert file_sha != package["package_sha256"]
    package["__package_file_sha256"] = file_sha
    assert package["package_sha256"] == _canonical_sha(_package_content_for_hash(package))


def test_generated_live_ready_package_hash_is_stable_with_file_sha_injection(tmp_path, monkeypatch):
    from mpf.services.phase11_controlled_artifact_reapply_core import _canonical_sha, _package_content_for_hash

    bundle = _ready_bundle(tmp_path, monkeypatch)
    report = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=CUSTOMERS, phase_status_text=PHASE)
    from mpf.services.phase11_controlled_artifact_reapply_core import build_package_from_plan, build_plan
    package = build_package_from_plan(build_plan(lanes=LANES, customers=CUSTOMERS, backend_target=binding_backend_target(build_verified_filter_hook_binding_report(bundle)), phase_status_text=PHASE))
    package["production_execution_available"] = False
    package["controlled_artifact_execute_available"] = False
    package["iptables_restore_invocation_allowed"] = False
    package["live_ready_package_available"] = True
    package["package_sha256"] = _canonical_sha(_package_content_for_hash(package))
    package["__package_file_sha256"] = "runtime-file-sha"

    assert report["package_sha256"] == _canonical_sha(_package_content_for_hash(package))


def test_cli_json_shape_stable(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, "run_live_ready_reapply_package_report", lambda *a, **k: {"component": "phase11_live_ready_reapply_package", "final_decision": svc.READY, "live_ready_package_available": True, "production_execution_available": False, "controlled_artifact_execute_available": False, "iptables_restore_invocation_allowed": False, "mutation_performed": False})
    result = CliRunner().invoke(app, ["production", "live-ready-controlled-artifact-reapply-package", "--packet-path-evidence-dir", str(tmp_path), "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["component"] == "phase11_live_ready_reapply_package"


def test_static_safety_no_execute_or_iptables_restore_apply_tokens():
    service = Path("mpf/services/phase11_live_ready_reapply_package_service.py").read_text()
    assert "controlled-artifact-reapply-execute" not in service
    assert "iptables-restore" not in service


def test_script_live_ready_package_writes_artifacts_without_env_gates(tmp_path):
    import os
    import subprocess

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_mpf = fake_bin / "mpf"
    fake_mpf.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        "args=sys.argv[1:]\n"
        "out=args[args.index('--output-dir')+1] if '--output-dir' in args else None\n"
        "if out:\n"
        " p=pathlib.Path(out); p.mkdir(parents=True, exist_ok=True); (p/'manifest.sha256.json').write_text('{}')\n"
        "print(json.dumps({'component':'phase11_live_ready_reapply_package','final_decision':'READY_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE','mutation_performed':False,'production_execution_available':False,'controlled_artifact_execute_available':False,'iptables_restore_invocation_allowed':False}))\n",
        encoding="utf-8",
    )
    fake_mpf.chmod(0o755)
    out = tmp_path / "out"
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    result = subprocess.run(
        ["scripts/phase11_controlled_artifact_reapply.sh", "--live-ready-package", "--packet-path-evidence-dir", str(evidence), "--out-dir", str(out)],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": ""},
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (out / "manifest.sha256.json").exists()
    assert "controlled-artifact-reapply-execute" not in result.stdout + result.stderr


def test_cli_exception_fallback_returns_full_closed_shape(monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(svc, "run_live_ready_reapply_package_report", boom)
    result = CliRunner().invoke(app, ["production", "live-ready-controlled-artifact-reapply-package", "--packet-path-evidence-dir", str(tmp_path), "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["final_decision"] == svc.BLOCKED
    assert "live_ready_reapply_package_failed_closed" in data["blockers"]
    for key in ["live_ready_package_available", "production_execution_available", "controlled_artifact_execute_available", "iptables_restore_invocation_allowed", "mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed", "phase12_start_allowed"]:
        assert data[key] is False
    assert data["worker_enforcement_allowed"] == "no"
    assert data["ui_allowed"] == "no"
    assert data["telegram_allowed"] == "no"


def _execution_gate_package_file(tmp_path, monkeypatch):
    import hashlib
    bundle = _ready_bundle(tmp_path, monkeypatch)
    out = tmp_path / "execution-gate"
    report = svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LANES, customers=CUSTOMERS, phase_status_text=PHASE, output_dir=out)
    assert report["final_decision"] == svc.READY
    package_path = out / "controlled-artifact-reapply-package.json"
    file_sha = hashlib.sha256(package_path.read_bytes()).hexdigest()
    package = json.loads(package_path.read_text(encoding="utf-8"))
    return package_path, file_sha, package


def test_execution_gate_preflight_ready_for_live_ready_package(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_execution_gate_preflight_service as gate

    package_path, file_sha, package = _execution_gate_package_file(tmp_path, monkeypatch)
    report = gate.run_execution_gate_preflight_report(package_json=package_path, package_sha256=file_sha, package_id=package["package_id"], operator="op", reason="review")
    assert report["final_decision"] == gate.READY
    assert report["next_required_step"] == gate.NEXT_READY
    assert report["package_integrity_ready"] is True
    assert report["execution_gate_preflight_ready"] is True
    assert report["backup_requirements_ready"] is True
    assert report["rollback_plan_ready"] is True
    assert report["lock_requirements_ready"] is True
    assert report["operator_confirmations_ready"] is True
    assert report["production_execution_available"] is False
    assert report["controlled_artifact_execute_available"] is False
    assert report["iptables_restore_invocation_allowed"] is False
    for flag in ["mutation_performed", "firewall_apply_performed", "db_mutation_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed", "phase12_start_allowed"]:
        assert report[flag] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"
    assert report["blockers"] == []


def test_execution_gate_preflight_cli_ready(tmp_path, monkeypatch):
    package_path, file_sha, package = _execution_gate_package_file(tmp_path, monkeypatch)
    result = CliRunner().invoke(app, ["production", "controlled-artifact-reapply-execution-gate-preflight", "--package-json", str(package_path), "--package-sha256", file_sha, "--package-id", package["package_id"], "--operator", "op", "--reason", "review", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["final_decision"] == "READY_CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_GATE_PREFLIGHT"
    assert data["iptables_restore_invocation_allowed"] is False


def test_execution_gate_preflight_blocks_wrong_file_sha_and_package_id(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_execution_gate_preflight_service as gate

    package_path, file_sha, package = _execution_gate_package_file(tmp_path, monkeypatch)
    wrong_sha = "0" * 64
    report = gate.run_execution_gate_preflight_report(package_json=package_path, package_sha256=wrong_sha, package_id="wrong", operator="op", reason="review")
    assert report["final_decision"] == gate.BLOCKED
    assert "package_file_sha256_mismatch" in report["blockers"]
    assert "package_id_mismatch" in report["blockers"]
    assert report["package_integrity_ready"] is False


def test_execution_gate_preflight_blocks_tampered_payload_preserved_embedded_hash(tmp_path, monkeypatch):
    import hashlib
    from mpf.services import phase11_controlled_artifact_reapply_execution_gate_preflight_service as gate

    package_path, _, package = _execution_gate_package_file(tmp_path, monkeypatch)
    package["payload"] = str(package["payload"]) + "# tamper\n"
    package_path.write_text(json.dumps(package, indent=2, sort_keys=True), encoding="utf-8")
    file_sha = hashlib.sha256(package_path.read_bytes()).hexdigest()
    report = gate.run_execution_gate_preflight_report(package_json=package_path, package_sha256=file_sha, package_id=package["package_id"], operator="op", reason="review")
    assert report["final_decision"] == gate.BLOCKED
    assert "package_canonical_sha256_mismatch" in report["blockers"]


def test_execution_gate_preflight_blocks_missing_safety_requirements_and_open_gates(tmp_path, monkeypatch):
    import hashlib
    from mpf.services import phase11_controlled_artifact_reapply_execution_gate_preflight_service as gate
    from mpf.services.phase11_controlled_artifact_reapply_core import _canonical_sha, _package_content_for_hash

    package_path, _, package = _execution_gate_package_file(tmp_path, monkeypatch)
    package.pop("backup_requirements")
    package.pop("rollback_plan")
    package.pop("lock_requirements")
    package["mutation_performed"] = True
    package["controlled_artifact_execute_available"] = True
    package["iptables_restore_invocation_allowed"] = True
    package["phase12_start_allowed"] = True
    package["worker_enforcement_allowed"] = "yes"
    package["package_sha256"] = _canonical_sha(_package_content_for_hash(package))
    package_path.write_text(json.dumps(package, indent=2, sort_keys=True), encoding="utf-8")
    file_sha = hashlib.sha256(package_path.read_bytes()).hexdigest()
    report = gate.run_execution_gate_preflight_report(package_json=package_path, package_sha256=file_sha, package_id=package["package_id"], operator="op", reason="review")
    assert report["final_decision"] == gate.BLOCKED
    for blocker in ["backup_requirements_missing", "rollback_plan_missing", "lock_requirements_missing", "mutation_performed_unexpected_true", "controlled_artifact_execute_available_unexpected_true", "iptables_restore_invocation_allowed_unexpected_true", "phase12_start_allowed_unexpected_true", "worker_enforcement_allowed_unexpected_open"]:
        assert blocker in report["blockers"]
