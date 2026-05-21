from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryHostApplyExecutor:
    def execute(self, report: dict[str, object], payload: str) -> dict[str, object]:
        if os.environ.get("CI"):
            return {"status": "blocked", "error": "single_canary_host_apply_not_allowed_in_ci"}
        for env in (
            "MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP",
            "MPF_PHASE11_SINGLE_CANARY_HOST_APPLY",
            "MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE",
        ):
            if os.environ.get(env) != "allow":
                return {"status": "blocked", "error": "single_canary_host_apply_execution_not_confirmed"}
        if "*nat" not in payload or "COMMIT" not in payload:
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}
        lines = payload.splitlines()
        if sum("--dport 20001" in l for l in lines) != 1 or sum("127.0.0.1:60010" in l for l in lines) != 1:
            return {"status": "blocked", "error": "single_canary_payload_scope_mismatch"}
        if any("--dport" in l and "--dport 20001" not in l for l in lines):
            return {"status": "blocked", "error": "single_canary_broad_payload_blocked"}
        if any(k in payload for k in ("*filter", "*mangle", "-F", "-X", "-Z")):
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}

        before = subprocess.run(["iptables-save", "-t", "nat"], check=False, capture_output=True, text=False)
        if before.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_save_before_apply_failed"}
        before_sha = hashlib.sha256(before.stdout).hexdigest()

        test = subprocess.run(["iptables-restore", "--test", "--noflush"], input=payload, check=False, capture_output=True, text=True)
        if test.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_restore_test_failed", "mutation_performed": False}

        apply = subprocess.run(["iptables-restore", "--noflush"], input=payload, check=False, capture_output=True, text=True)
        if apply.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_restore_apply_failed", "mutation_performed": False}

        return {"status": "ok", "applied": True, "iptables_restore_used": True, "pre_apply_nat_sha256": before_sha}
