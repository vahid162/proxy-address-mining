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

        lines = [x.strip() for x in payload.splitlines() if x.strip()]
        if "*nat" not in payload or "COMMIT" not in payload:
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}
        if any(k in payload for k in ("*filter", "*mangle", "*raw", "-F", "-X", "-Z")):
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}
        if sum("--dport 20001" in l for l in lines) != 1 or sum("127.0.0.1:60010" in l for l in lines) != 1:
            return {"status": "blocked", "error": "single_canary_payload_scope_mismatch"}
        if any("--dport" in l and "--dport 20001" not in l for l in lines):
            return {"status": "blocked", "error": "single_canary_broad_payload_blocked"}

        has_jump_in_payload = any("-A PREROUTING" in l and "-j MPF_NAT_PRE" in l for l in lines)
        has_chain_create = any(l.startswith("-N MPF_NAT_PRE") for l in lines)
        live_nat = self._run(["iptables-save", "-t", "nat"], text=False)
        if live_nat.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_save_before_apply_failed"}
        nat_text = live_nat.stdout.decode("utf-8", errors="replace")
        jump_exists_live = any("-A PREROUTING" in l and "-j MPF_NAT_PRE" in l for l in nat_text.splitlines())
        chain_exists_live = any(l.strip() == ":MPF_NAT_PRE - [0:0]" for l in nat_text.splitlines())

        if not has_jump_in_payload and not jump_exists_live:
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}
        if has_chain_create and chain_exists_live:
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}

        before_sha = hashlib.sha256(live_nat.stdout).hexdigest()
        test = self._run(["iptables-restore", "--test", "--noflush"], input=payload, text=True)
        if test.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_restore_test_failed", "mutation_performed": False}

        apply = self._run(["iptables-restore", "--noflush"], input=payload, text=True)
        if apply.returncode != 0:
            return {"status": "blocked", "error": "single_canary_iptables_restore_apply_failed", "mutation_performed": False}

        post_nat = self._run(["iptables-save", "-t", "nat"], text=False)
        post_sha = hashlib.sha256(post_nat.stdout).hexdigest() if post_nat.returncode == 0 else None
        return {
            "status": "ok",
            "applied": True,
            "iptables_restore_used": True,
            "mutation_performed": True,
            "firewall_mutation_performed": True,
            "pre_apply_nat_sha256": before_sha,
            "post_apply_nat_sha256": post_sha,
        }
