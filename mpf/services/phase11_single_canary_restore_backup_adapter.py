from __future__ import annotations

import hashlib
import os
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


@dataclass(slots=True)
class SingleCanaryRestoreBackupAdapter:
    expected_version: str = "0.1.164"
    env_gate_var: str = "MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP"
    backup_root: str = "/var/backups/mpf"
    iptables_save_executor: Callable[[], subprocess.CompletedProcess[str]] | None = None

    def _validate(self, report: dict[str, object]) -> str | None:
        req = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
        if req.get("requested_action") != "execute":
            return "single_canary_execute_only"
        if req.get("customer_key") != "canary-btc-001":
            return "wrong_customer_key"
        if req.get("lane") != "btc":
            return "wrong_lane"
        if req.get("port") != 20001:
            return "wrong_customer_port"
        if req.get("expected_version") != self.expected_version:
            return "wrong_expected_version"
        if report.get("scope", {}).get("single_canary_only") is not True:
            return "non_single_canary_scope"
        for flag in ("operator_confirmed", "understand_canary_customer", "understand_firewall_apply", "reviewed_rollback", "fresh_farm5_sync_confirmed"):
            if req.get(flag) is not True:
                return f"missing_{flag}"
        for gate in ("phase_gate", "mpf_doctor", "db_status", "proxy_doctor", "no_customer_nat_baseline", "no_customer_firewall_baseline", "local_only_runtime_baseline"):
            if report.get("preflight_results", {}).get(gate) != "OK":
                return f"precondition_failed:{gate}"
        if os.environ.get(self.env_gate_var) != "allow":
            return "single_canary_restore_backup_context_not_confirmed"
        if os.environ.get("CI"):
            return "single_canary_restore_backup_not_allowed_in_ci"
        return None

    def _save_backup(self) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        host = socket.gethostname()
        d = Path(self.backup_root) / "phase11-single-canary"
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"iptables-save-{host}-{stamp}.txt"
        runner = self.iptables_save_executor
        if runner is None:
            runner = lambda: subprocess.run(["iptables-save"], capture_output=True, text=True, check=False)
        cp = runner()
        if cp.returncode != 0:
            err = (cp.stderr or cp.stdout or "iptables-save failed").strip()
            raise RuntimeError(err)
        content = cp.stdout
        path.write_text(content, encoding="utf-8")
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return str(path), sha

    def run(self, report: dict[str, object]) -> dict[str, object]:
        blocker = self._validate(report)
        if blocker:
            return {"status": "blocked", "error": blocker}
        now = datetime.now(timezone.utc).isoformat()
        host = socket.gethostname()
        try:
            backup_path, backup_sha256 = self._save_backup()
        except Exception as exc:
            return {"status": "error", "error": f"iptables_save_backup_failed: {exc}"}
        return {
            "status": "ok",
            "mode": "single_canary_restore_backup_boundary",
            "created_at": now,
            "host": host,
            "restore_point": {"id": f"phase11-single-canary-{host}", "created_at": now, "mode": "single_canary_restore_backup_boundary"},
            "iptables_save_backup": {"id": f"iptables-save-{host}", "created_at": now, "path": backup_path, "sha256": backup_sha256, "mode": "single_canary_restore_backup_boundary"},
            "backup_path": backup_path,
            "backup_sha256": backup_sha256,
            "mutation_performed": False,
            "firewall_mutation_performed": False,
            "nat_mutation_performed": False,
            "production_traffic_enabled": False,
        }
