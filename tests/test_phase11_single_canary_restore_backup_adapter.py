from __future__ import annotations

import os
from pathlib import Path

from mpf import __version__
from mpf.services.phase11_single_canary_restore_backup_adapter import SingleCanaryRestoreBackupAdapter


def _report(**overrides):
    req = {
        "requested_action": "execute",
        "customer_key": "canary-btc-001",
        "lane": "btc",
        "port": 20001,
        "expected_version": __version__,
        "operator_confirmed": True,
        "understand_canary_customer": True,
        "understand_firewall_apply": True,
        "reviewed_rollback": True,
        "fresh_farm5_sync_confirmed": True,
    }
    rep = {
        "request": req,
        "scope": {"single_canary_only": True},
        "preflight_results": {"phase_gate": "OK", "mpf_doctor": "OK", "db_status": "OK", "proxy_doctor": "OK", "no_customer_nat_baseline": "OK", "no_customer_firewall_baseline": "OK", "local_only_runtime_baseline": "OK"},
    }
    rep.update(overrides)
    return rep


def test_blocks_without_context_guard(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", raising=False)
    monkeypatch.delenv("CI", raising=False)
    ad = SingleCanaryRestoreBackupAdapter(backup_root=str(tmp_path))
    out = ad.run(_report())
    assert out["status"] == "blocked"
    assert out["error"] == "single_canary_restore_backup_context_not_confirmed"


def test_blocks_in_ci(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("CI", "1")
    ad = SingleCanaryRestoreBackupAdapter(backup_root=str(tmp_path))
    out = ad.run(_report())
    assert out["status"] == "blocked"


def test_wrong_scope_and_version_block(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.delenv("CI", raising=False)
    ad = SingleCanaryRestoreBackupAdapter(backup_root=str(tmp_path))
    assert ad.run(_report(request={**_report()["request"], "customer_key": "x"}))["status"] == "blocked"
    assert ad.run(_report(scope={"single_canary_only": False}))["error"] == "non_single_canary_scope"
    assert ad.run(_report(request={**_report()["request"], "expected_version": "0.1.158"}))["error"] == "wrong_expected_version"


def test_creates_restore_and_backup(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.delenv("CI", raising=False)

    def _ok_exec():
        import subprocess
        return subprocess.CompletedProcess(args=["iptables-save"], returncode=0, stdout="*filter\nCOMMIT\n", stderr="")

    ad = SingleCanaryRestoreBackupAdapter(backup_root=str(tmp_path), iptables_save_executor=_ok_exec)
    out = ad.run(_report())
    assert out["status"] == "ok"
    assert out["mutation_performed"] is False
    p = Path(out["backup_path"])
    assert p.exists()
    assert len(out["backup_sha256"]) == 64


def test_iptables_save_failure(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.delenv("CI", raising=False)

    def _bad_exec():
        import subprocess
        return subprocess.CompletedProcess(args=["iptables-save"], returncode=1, stdout="", stderr="denied")

    ad = SingleCanaryRestoreBackupAdapter(backup_root=str(tmp_path), iptables_save_executor=_bad_exec)
    out = ad.run(_report())
    assert out["status"] == "error"
    assert "iptables_save_backup_failed" in out["error"]
