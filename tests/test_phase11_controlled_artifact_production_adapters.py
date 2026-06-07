from __future__ import annotations

import json
import os
from pathlib import Path

from mpf.services.phase11_controlled_artifact_reapply_core import (
    CommandResult,
    FileBackupAdapter,
    FlockHostLock,
    ProductionIptablesRestoreRunner,
    execute_package,
)
from tests.test_phase11_controlled_artifact_reapply import readyish_package, _executable_live_plan


def test_flock_lock_blocks_concurrent_acquire_and_releases(tmp_path):
    path = tmp_path / "mpf.lock"
    a = FlockHostLock(path)
    b = FlockHostLock(path)
    assert a.acquire() is True
    assert b.acquire() is False
    a.release()
    assert b.acquire() is True
    b.release()


def test_backup_adapter_non_overwrite_modes_and_manifest(tmp_path):
    pkg = readyish_package()
    adapter = FileBackupAdapter(tmp_path)
    result = adapter.prepare(pkg, iptables_save="*filter\nCOMMIT\n", ip6tables_save="*filter\nCOMMIT\n")
    backup_dir = Path(result["backup_dir"])
    assert oct(backup_dir.stat().st_mode & 0o777) == "0o700"
    manifest = json.loads((backup_dir / "manifest.sha256.json").read_text())
    assert "iptables-save.txt" in manifest
    assert oct((backup_dir / "iptables-save.txt").stat().st_mode & 0o777) == "0o600"
    try:
        adapter.prepare(pkg, iptables_save="*filter\nCOMMIT\n", ip6tables_save="*filter\nCOMMIT\n")
    except FileExistsError:
        pass
    else:
        raise AssertionError("backup directory must not be overwritten")


def test_production_runner_allowlist_uses_argv_only(monkeypatch):
    calls = []

    def fake_run(argv, *, shell, check, capture_output, text, input=None):
        calls.append((argv, shell, input))
        return type("Completed", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    monkeypatch.setattr("subprocess.run", fake_run)
    runner = ProductionIptablesRestoreRunner()
    assert runner.run(["iptables-restore", "--test", "--noflush"], input_text="payload").returncode == 0
    assert calls == [(["iptables-restore", "--test", "--noflush"], False, "payload")]
    blocked = runner.run(["iptables", "-A", "INPUT"])
    assert blocked.returncode == 126


def test_execute_blocks_missing_env_and_ci_before_restore():
    pkg = readyish_package()
    result = execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={})
    assert "controlled_artifact_reapply_env_gate_missing" in result["blockers"]
    assert result["iptables_restore_invoked"] is False
    result = execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={"CI":"1", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY":"allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE":"allow"})
    assert "ci_execution_blocked" in result["blockers"]


def test_successful_synthetic_execute_sequence_with_injected_production_fakes():
    pkg = readyish_package()
    calls = []

    class Runner:
        production_ready = True
        def run(self, argv, input_text=None):
            calls.append(argv)
            return CommandResult(0, "", "")
    class Lock:
        production_ready = True
        def acquire(self): calls.append(["lock"]); return True
        def release(self): calls.append(["release"])
    class Backup:
        production_ready = True
        def prepare(self, package, *, iptables_save, ip6tables_save): calls.append(["backup"]); return {"backup_dir":"x"}
    class Metadata:
        production_ready = True
        def record_intent(self, package, operator, reason): calls.append(["intent"])
        def record_result(self, package, decision): calls.append(["result", decision])

    result = execute_package(
        package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True,
        env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY":"allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE":"allow"},
        current_hostname=pkg["hostname"], live_plan_builder=lambda: _executable_live_plan(pkg), runner=Runner(), lock=Lock(), backup=Backup(), metadata_repo=Metadata(),
    )
    assert result["final_decision"] == "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"
    assert calls[:4] == [["lock"], ["backup"], ["intent"], ["iptables-restore", "--test", "--noflush"]]
    assert ["iptables-restore", "--noflush"] in calls
