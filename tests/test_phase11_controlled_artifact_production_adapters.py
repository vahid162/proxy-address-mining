from __future__ import annotations

import json
import os
from pathlib import Path

from mpf.models import AuditLog, Backup, Event, FirewallApply, FirewallSnapshot, RestorePoint
from mpf.services.phase11_controlled_artifact_reapply_core import (
    CommandResult,
    FileBackupAdapter,
    FlockHostLock,
    ProductionIptablesRestoreRunner,
    execute_package,
)
from tests.test_phase11_controlled_artifact_reapply import readyish_package, _executable_live_plan


def _model_columns(model: object) -> set[str]:
    return {column.name for column in model.__table__.columns}


def _insert_columns(sql: str, table: str) -> set[str]:
    compact = " ".join(sql.split())
    prefix = f"insert into {table} ("
    start = compact.index(prefix) + len(prefix)
    end = compact.index(")", start)
    return {part.strip() for part in compact[start:end].split(",")}


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
    second = adapter.prepare(pkg, iptables_save="*filter\nCOMMIT\n", ip6tables_save="*filter\nCOMMIT\n")
    second_dir = Path(second["backup_dir"])
    assert second_dir != backup_dir
    assert second_dir.exists()
    assert pkg["package_id"] in second_dir.name
    assert result["attempt_id"] != second["attempt_id"]


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
        def record_intent(self, package, operator, reason, **kwargs): calls.append(["intent"]); return {"firewall_apply_id": 1}
        def record_result(self, package, decision, **kwargs): calls.append(["result", decision]); return {"snapshot_after_id": 2}

    result = execute_package(
        package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True,
        env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY":"allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE":"allow"},
        current_hostname=pkg["hostname"], live_plan_builder=lambda: _executable_live_plan(pkg), runner=Runner(), lock=Lock(), backup=Backup(), metadata_repo=Metadata(),
    )
    assert result["final_decision"] == "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"
    assert calls[:4] == [["lock"], ["backup"], ["intent"], ["iptables-restore", "--test", "--noflush"]]
    assert ["iptables-restore", "--noflush"] in calls


def test_audit_repo_uses_real_schema_columns_and_short_statuses(monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_audit_service as audit

    executed = []

    class Cursor:
        def execute(self, sql, params=()):
            executed.append((" ".join(sql.split()), params))
        def fetchone(self):
            return (101,)
        def __enter__(self): return self
        def __exit__(self, *args): return False
    class Conn:
        def cursor(self): return Cursor()
        def __enter__(self): return self
        def __exit__(self, *args): return False

    repo = audit.ControlledArtifactReapplyAuditRepo(type("Cfg", (), {"database": type("Db", (), {"url": "postgresql://example"})()})())
    monkeypatch.setattr(repo, "_connect", lambda: Conn())
    pkg = readyish_package()
    backup_result = {"backup_dir": "/var/backups/mpf/phase11-controlled-artifact-reapply/pkg", "manifest": {"iptables-save.txt": "abc"}, "manifest_sha256": "manifest-sha"}
    refs = repo.record_intent(pkg, "operator", "reason", backup_result=backup_result, pre_iptables_save="*filter\nCOMMIT\n")
    result_refs = repo.record_result(pkg, "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW", backup_result=backup_result, post_iptables_save="*filter\nCOMMIT\n")
    sql = "\n".join(item[0] for item in executed)

    assert "verify" + "_message" not in sql
    assert "firewall_snapshots (backend, iptables_save_text, checksum, created_by, reason)" in sql
    assert "backups (backup_type, path, checksum, status, created_by, verified_at, error_message, metadata_json)" in sql
    assert "restore_points (restore_type, subject_type, subject_id, snapshot_id, backup_id, metadata_json, created_by, reason, checksum)" in sql
    assert "events (event_type, severity, subject_type, subject_id, message, data_json, created_by, correlation_id)" in sql
    assert "audit_log (actor_type, actor_id, action, resource_type, resource_id, before_json, after_json, reason, correlation_id)" in sql
    assert "firewall_applies (action, status, apply_mode, backend, restore_point_id, snapshot_before_id, snapshot_after_id, plan_json, summary, started_at, created_by, error_message, correlation_id)" in sql
    assert "update firewall_applies set status=%s" in sql

    model_by_table = {
        "firewall_snapshots": FirewallSnapshot,
        "backups": Backup,
        "restore_points": RestorePoint,
        "firewall_applies": FirewallApply,
        "events": Event,
        "audit_log": AuditLog,
    }
    for table, model in model_by_table.items():
        for statement, _ in executed:
            if f"insert into {table} (" in statement:
                assert _insert_columns(statement, table) <= _model_columns(model)
        if table == "firewall_applies":
            assert {"status", "snapshot_after_id", "plan_json", "summary", "finished_at", "error_message"} <= _model_columns(model)

    backup_params = next(params for statement, params in executed if "insert into backups" in statement)
    assert backup_params[1].endswith("/phase11-controlled-artifact-reapply/pkg")
    assert backup_params[3] == "prepared"
    assert backup_params[5] is None
    backup_metadata = json.loads(backup_params[6])
    assert backup_metadata["package_id"] == pkg["package_id"]
    assert backup_metadata["backup_manifest_sha256"] == backup_params[2]
    assert backup_metadata["canonical_package_sha256"] == pkg["package_sha256"]
    assert backup_metadata["payload_sha256"] == pkg["payload_sha256"]
    assert backup_metadata["backup_dir"].endswith("/phase11-controlled-artifact-reapply/pkg")
    assert any(params and params[0] == "verified" for _, params in executed if params)
    assert refs["backup_dir"].endswith("pkg")
    assert result_refs["short_status"] == "verified"
    assert len(result_refs["short_status"]) <= 32


def test_snapshot_command_failures_and_invalid_output_block_ready(monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_package_service as service

    assert service._snapshot_structure_blockers(service.FirewallSnapshotCommandResult(["iptables-save"], "iptables-save", 127, "", "missing"), family="iptables") == ["iptables_save_read_failed"]
    assert service._snapshot_structure_blockers(service.FirewallSnapshotCommandResult(["iptables-save"], "iptables-save", 1, "", "bad"), family="iptables") == ["iptables_save_read_failed"]
    assert service._snapshot_structure_blockers(service.FirewallSnapshotCommandResult(["iptables-save"], "iptables-save", 0, "", ""), family="iptables") == ["iptables_snapshot_empty_or_invalid"]
    assert service._snapshot_structure_blockers(service.FirewallSnapshotCommandResult(["iptables-save"], "iptables-save", 0, "*filter\n", ""), family="iptables") == ["iptables_snapshot_empty_or_invalid"]
    assert service._snapshot_structure_blockers(service.FirewallSnapshotCommandResult(["iptables-save"], "iptables-save", 0, "*filter\nCOMMIT\n", ""), family="iptables") == []


def test_audit_repo_local_peer_root_uses_sudo_psql_not_psycopg(monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_audit_service as audit

    calls = []
    monkeypatch.setattr(audit.os, "geteuid", lambda: 0)
    monkeypatch.setattr("psycopg.connect", lambda *a, **k: (_ for _ in ()).throw(AssertionError("psycopg must not be used")))

    def fake_run(argv, input, text, capture_output, check, shell):
        calls.append((argv, input))
        assert argv[:3] == ["sudo", "-u", "mpf"]
        assert "ON_ERROR_STOP=1" in argv
        if "firewall_apply_prepared" in input:
            out = json.dumps({"snapshot_before_id": 1, "backup_id": 2, "restore_point_id": 3, "firewall_apply_id": 4, "correlation_id": "pkg", "backup_dir": "/b", "backup_manifest_sha256": "h"})
        else:
            out = json.dumps({"snapshot_after_id": 5, "firewall_apply_id": 4, "correlation_id": "pkg", "short_status": "verified"})
        return type("Completed", (), {"returncode": 0, "stdout": out + "\n", "stderr": ""})()

    monkeypatch.setattr(audit.subprocess, "run", fake_run)
    repo = audit.ControlledArtifactReapplyAuditRepo(type("Cfg", (), {"database": type("Db", (), {"url": "postgresql:///mpf"})()})())
    pkg = readyish_package(); pkg["package_id"] = "pkg"
    refs = repo.record_intent(pkg, "operator", "reason", backup_result={"backup_dir": "/b", "manifest": {}}, pre_iptables_save="*filter\nCOMMIT\n")
    result = repo.record_result(pkg, "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW", backup_result={"backup_dir": "/b"}, post_iptables_save="*filter\nCOMMIT\n")
    assert refs["firewall_apply_id"] == 4
    assert result["short_status"] == "verified"
    assert len(calls) == 2


def test_execute_failure_after_backup_before_intent_preserves_backup_and_stage():
    pkg = readyish_package()
    calls = []

    class Runner:
        production_ready = True
        def run(self, argv, input_text=None): calls.append(argv); return CommandResult(0, "", "")
    class Lock:
        production_ready = True
        def acquire(self): return True
        def release(self): pass
    class Backup:
        production_ready = True
        def prepare(self, package, *, iptables_save, ip6tables_save): return {"backup_dir": "/backup/attempt"}
    class Metadata:
        production_ready = True
        def record_intent(self, *a, **k): raise RuntimeError("db root role missing")

    result = execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True,
        env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY":"allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE":"allow"},
        current_hostname=pkg["hostname"], live_plan_builder=lambda: _executable_live_plan(pkg), runner=Runner(), lock=Lock(), backup=Backup(), metadata_repo=Metadata())
    assert result["final_decision"] == "FAILED_PRE_APPLY"
    assert result["error_stage"] == "audit_record_intent_failed"
    assert result["backup"]["backup_dir"] == "/backup/attempt"
    assert result["iptables_restore_invoked"] is False
    assert calls == []


def test_execution_gate_preflight_blocks_missing_local_peer_root_strategy(monkeypatch, tmp_path):
    from mpf.services import phase11_controlled_artifact_reapply_execution_gate_preflight_service as gate
    from tests.test_phase11_live_ready_reapply_package import _execution_gate_package_file
    from mpf.services import phase11_controlled_artifact_reapply_audit_service as audit

    monkeypatch.setattr(audit.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(gate, "load_config", lambda _p: type("Cfg", (), {"database": type("Db", (), {"url": "postgresql:///mpf"})()})())
    package_path, file_sha, package = _execution_gate_package_file(tmp_path, monkeypatch)
    report = gate.run_execution_gate_preflight_report(package_json=package_path, package_sha256=file_sha, package_id=package["package_id"], operator="op", reason="review")
    assert "audit_metadata_local_peer_root_strategy_missing" in report["blockers"]
    assert report["final_decision"] == gate.BLOCKED


def test_execution_gate_preflight_passes_with_local_peer_root_strategy(monkeypatch, tmp_path):
    from mpf.services import phase11_controlled_artifact_reapply_execution_gate_preflight_service as gate
    from tests.test_phase11_live_ready_reapply_package import _execution_gate_package_file
    from mpf.services import phase11_controlled_artifact_reapply_audit_service as audit

    monkeypatch.setattr(audit.os, "geteuid", lambda: 0)
    monkeypatch.setattr(gate, "load_config", lambda _p: type("Cfg", (), {"database": type("Db", (), {"url": "postgresql:///mpf"})()})())
    package_path, file_sha, package = _execution_gate_package_file(tmp_path, monkeypatch)
    report = gate.run_execution_gate_preflight_report(package_json=package_path, package_sha256=file_sha, package_id=package["package_id"], operator="op", reason="review")
    assert "audit_metadata_local_peer_root_strategy_missing" not in report["blockers"]
    assert report["final_decision"] == gate.READY
