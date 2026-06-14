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
