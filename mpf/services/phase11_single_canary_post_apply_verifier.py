from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryPostApplyVerifier:
    def verify(self, report: dict[str, object]) -> dict[str, object]:
        nat = subprocess.run(["iptables-save", "-t", "nat"], shell=False, check=False, capture_output=True, text=True)
        if nat.returncode != 0:
            return {"status": "error", "error": "single_canary_post_apply_iptables_save_failed"}
        lines = nat.stdout.splitlines()
        if not any(l.startswith(":MPF_NAT_PRE ") for l in lines):
            return {"status": "blocked", "error": "single_canary_mpf_nat_pre_missing"}
        if not any("-A PREROUTING" in l and "-j MPF_NAT_PRE" in l for l in lines):
            return {"status": "blocked", "error": "single_canary_prerouting_hook_missing"}

        canary = [l for l in lines if "--dport 20001" in l and "--to-destination 127.0.0.1:60010" in l and "canary-btc-001" in l]
        if not canary:
            return {"status": "blocked", "error": "single_canary_nat_rule_missing"}
        if len(canary) > 1:
            return {"status": "blocked", "error": "single_canary_duplicate_rule_detected", "duplicate_rule_detected": True}
        if any("canary-btc-001" in l and "--dport 20001" not in l for l in lines):
            return {"status": "blocked", "error": "single_canary_unrelated_customer_rule_detected"}

        filt = subprocess.run(["iptables-save", "-t", "filter"], shell=False, check=False, capture_output=True, text=True)
        if filt.returncode != 0:
            return {"status": "error", "error": "single_canary_filter_snapshot_failed"}
        exposure = any("-A INPUT" in l and "--dport 60010" in l and "127.0.0.1" not in l for l in filt.stdout.splitlines())
        if exposure:
            return {"status": "blocked", "error": "single_canary_backend_public_exposure_detected", "backend_public_exposure": True}

        return {"status": "ok", "nat_rule_verified": True, "customer_port": 20001, "backend_port": 60010, "duplicate_rule_detected": False, "backend_public_exposure": False}
