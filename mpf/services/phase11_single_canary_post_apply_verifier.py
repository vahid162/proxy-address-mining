from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryPostApplyVerifier:
    def verify(self, report: dict[str, object]) -> dict[str, object]:
        target = report.get("single_canary_backend_target", {}) if isinstance(report.get("single_canary_backend_target"), dict) else {}
        thost = target.get("target_host")
        if not isinstance(thost, str) or thost.startswith("127."):
            return {"status": "blocked", "error": "single_canary_backend_target_invalid"}

        nat = subprocess.run(["iptables-save", "-t", "nat"], shell=False, check=False, capture_output=True, text=True)
        if nat.returncode != 0:
            return {"status": "error", "error": "single_canary_post_apply_iptables_save_failed"}
        lines = nat.stdout.splitlines()
        if sum(l.startswith(":MPF_NAT_PRE ") for l in lines) != 1:
            return {"status": "blocked", "error": "single_canary_mpf_nat_pre_missing"}
        hook_count = sum("-A PREROUTING" in l and "-j MPF_NAT_PRE" in l for l in lines)
        if hook_count != 1:
            return {"status": "blocked", "error": "single_canary_prerouting_hook_missing" if hook_count == 0 else "single_canary_duplicate_prerouting_hook"}

        canary = [l for l in lines if "-A MPF_NAT_PRE" in l and "--dport 20001" in l and f"--to-destination {thost}:60010" in l and "canary-btc-001" in l]
        if len(canary) == 0:
            return {"status": "blocked", "error": "single_canary_nat_rule_missing"}
        if len(canary) > 1:
            return {"status": "blocked", "error": "single_canary_duplicate_rule_detected"}
        if any("customer_nat_redirect" in l and "canary-btc-001" not in l for l in lines):
            return {"status": "blocked", "error": "single_canary_unrelated_customer_rule_detected"}

        filt = subprocess.run(["iptables-save", "-t", "filter"], shell=False, check=False, capture_output=True, text=True)
        if filt.returncode != 0:
            return {"status": "error", "error": "single_canary_filter_snapshot_failed"}
        fl = filt.stdout.splitlines()
        if sum(l.startswith(':MPFC_20001 ') for l in fl) != 1:
            return {"status": "blocked", "error": "single_canary_filter_chain_missing"}
        conn = [l for l in fl if l.startswith('-A MPFC_20001') and 'mpf:canary-btc-001:customer_connlimit_reject' in l and '--dport 20001' in l and '-j REJECT' in l]
        hsh = [l for l in fl if l.startswith('-A MPFC_20001') and 'mpf:canary-btc-001:customer_hashlimit_reject' in l and '--dport 20001' in l and '-j REJECT' in l]
        if len(conn) != 1:
            return {"status": "blocked", "error": "single_canary_connlimit_reject_source_missing"}
        if len(hsh) != 1:
            return {"status": "blocked", "error": "single_canary_hashlimit_reject_source_missing"}
        if any(l.startswith('-A MPFC_20001') and 'customer_connlimit_reject' in l and 'mpf:canary-btc-001:customer_connlimit_reject' not in l for l in fl):
            return {"status": "blocked", "error": "single_canary_wrong_customer_reject_source"}
        if any(l.startswith('-A MPFC_20001') and 'customer_hashlimit_reject' in l and 'mpf:canary-btc-001:customer_hashlimit_reject' not in l for l in fl):
            return {"status": "blocked", "error": "single_canary_wrong_customer_reject_source"}
        if any(l.startswith('-A MPFC_20001') and ('customer_connlimit_reject' in l or 'customer_hashlimit_reject' in l) and 'mpf:' not in l for l in fl):
            return {"status": "blocked", "error": "single_canary_broad_reject_source_forbidden"}
        if any("-A INPUT" in l and "--dport 60010" in l and "-s 127.0.0.1" not in l for l in fl):
            return {"status": "blocked", "error": "single_canary_backend_public_exposure_detected", "backend_public_exposure": True}

        return {
            "status": "ok",
            "nat_rule_verified": True,
            "duplicate_rule_detected": False,
            "backend_public_exposure": False,
            "filter_reject_counter_source_verified": True,
            "connlimit_reject_source_verified": True,
            "hashlimit_reject_source_verified": True,
            "resolved_target": {"target_host": thost, "target_port": 60010},
        }
