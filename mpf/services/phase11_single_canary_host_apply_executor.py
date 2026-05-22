from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryHostApplyExecutor:
    def _run(self, argv: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(argv, shell=False, check=False, capture_output=True, **kwargs)

    def _validate_payload(self, payload: str, target_host: str) -> bool:
        lines = [l.strip() for l in payload.splitlines() if l.strip()]
        if any(k in payload for k in ("-A PREROUTING", "-F", "-X", "-D", "-I", "*mangle", "*raw")):
            return False
        nat = [l for l in lines if l.startswith('-A MPF_NAT_PRE')]
        conn = [l for l in lines if l.startswith('-A MPFC_20001') and 'customer_connlimit_reject' in l]
        hsh = [l for l in lines if l.startswith('-A MPFC_20001') and 'customer_hashlimit_reject' in l]
        if len(nat) != 1 or len(conn) != 1 or len(hsh) != 1:
            return False
        nat_line = nat[0]
        if not all(x in nat_line for x in ('--dport 20001', 'mpf:canary-btc-001:customer_nat_redirect', f'--to-destination {target_host}:60010')):
            return False
        if '--to-destination 127.0.0.1:60010' in payload:
            return False
        conn_line = conn[0]
        hash_line = hsh[0]
        if '--dport 20001' not in conn_line or '-j REJECT' not in conn_line or 'canary-btc-001' not in conn_line:
            return False
        if '--dport 20001' not in hash_line or '-j REJECT' not in hash_line or 'canary-btc-001' not in hash_line:
            return False
        dport20001 = [l for l in lines if '--dport 20001' in l and l.startswith('-A ')]
        allowed = {nat_line, conn_line, hash_line}
        if any(l not in allowed for l in dport20001):
            return False
        if any('canary-btc-001' in l and 'mpf:canary-btc-001:' not in l for l in lines):
            return False
        if any('customer_connlimit_reject' in l and 'mpf:canary-btc-001:customer_connlimit_reject' not in l for l in lines):
            return False
        if any('customer_hashlimit_reject' in l and 'mpf:canary-btc-001:customer_hashlimit_reject' not in l for l in lines):
            return False
        if any('mpf:' in l and 'canary-btc-001' not in l and ('customer_' in l or 'MPFC_20001' in l) for l in lines):
            return False
        return True

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
        if not self._validate_payload(payload, thost):
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
