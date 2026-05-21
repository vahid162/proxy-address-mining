from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryHostApplyExecutor:
    def _run(self, argv: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(argv, shell=False, check=False, capture_output=True, **kwargs)

    def execute(self, report: dict[str, object], payload: str) -> dict[str, object]:
        if os.environ.get("CI"):
            return {"status": "blocked", "error": "single_canary_host_apply_not_allowed_in_ci"}
        for env in ("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE"):
            if os.environ.get(env) != "allow":
                return {"status": "blocked", "error": "single_canary_host_apply_execution_not_confirmed"}

        target = report.get("single_canary_backend_target", {}) if isinstance(report.get("single_canary_backend_target"), dict) else {}
        thost = target.get("target_host")
        tport = target.get("target_port")
        if not isinstance(thost, str) or thost.startswith("127.") or tport != 60010:
            return {"status": "blocked", "error": "single_canary_backend_target_invalid"}
        if f"--to-destination {thost}:60010" not in payload or "--to-destination 127.0.0.1:60010" in payload:
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}
        if sum("--dport 20001" in l for l in payload.splitlines()) != 1:
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}

        live_nat = self._run(["iptables-save", "-t", "nat"], text=True)
        if live_nat.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_save_before_apply_failed"}
        lines = live_nat.stdout.splitlines()
        chain_count = sum(l.startswith(":MPF_NAT_PRE ") for l in lines)
        hook_count = sum("-A PREROUTING" in l and "-j MPF_NAT_PRE" in l for l in lines)
        canary_count = sum("canary-btc-001" in l and "--dport 20001" in l for l in lines)
        if chain_count != 1 or hook_count != 1 or canary_count > 0:
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}

        before_sha = hashlib.sha256(live_nat.stdout.encode()).hexdigest()
        test = self._run(["iptables-restore", "--test", "--noflush"], input=payload, text=True)
        if test.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_restore_test_failed", "mutation_performed": False}
        apply = self._run(["iptables-restore", "--noflush"], input=payload, text=True)
        if apply.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_restore_apply_failed", "mutation_performed": False}

        post_nat = self._run(["iptables-save", "-t", "nat"], text=True)
        post_sha = hashlib.sha256(post_nat.stdout.encode()).hexdigest() if post_nat.returncode == 0 else None
        return {"status": "ok", "applied": True, "iptables_restore_used": True, "mutation_performed": True, "firewall_mutation_performed": True, "nat_mutation_performed": True, "pre_apply_nat_sha256": before_sha, "post_apply_nat_sha256": post_sha}
