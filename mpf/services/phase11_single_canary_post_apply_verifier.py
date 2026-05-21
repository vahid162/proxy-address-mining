from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryPostApplyVerifier:
    def verify(self, report: dict[str, object]) -> dict[str, object]:
        save = subprocess.run(["iptables-save", "-t", "nat"], check=False, capture_output=True, text=True)
        if save.returncode != 0:
            return {"status": "error", "error": "single_canary_post_apply_iptables_save_failed"}
        text = save.stdout
        rule_lines = [ln for ln in text.splitlines() if "--dport 20001" in ln and "--to-destination 127.0.0.1:60010" in ln]
        canary_lines = [ln for ln in rule_lines if "canary-btc-001" in ln]
        if not canary_lines:
            return {"status": "blocked", "error": "single_canary_nat_rule_missing"}
        if len(canary_lines) > 1:
            return {"status": "blocked", "error": "single_canary_duplicate_rule_detected", "duplicate_rule_detected": True}
        if any("--dport" in ln and "--dport 20001" not in ln and "canary" in ln for ln in text.splitlines()):
            return {"status": "blocked", "error": "single_canary_unrelated_customer_rule_detected"}
        input_save = subprocess.run(["iptables-save", "-t", "filter"], check=False, capture_output=True, text=True)
        if input_save.returncode != 0:
            return {"status": "error", "error": "single_canary_filter_snapshot_failed"}
        exposure = any("--dport 60010" in ln and "-A INPUT" in ln and "-s 127.0.0.1" not in ln for ln in input_save.stdout.splitlines())
        if exposure:
            return {"status": "blocked", "error": "single_canary_backend_public_exposure_detected", "backend_public_exposure": True}
        return {
            "status": "ok",
            "nat_rule_verified": True,
            "customer_port": 20001,
            "backend_port": 60010,
            "duplicate_rule_detected": False,
            "backend_public_exposure": False,
        }
