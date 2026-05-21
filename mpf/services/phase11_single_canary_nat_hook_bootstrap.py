from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryNatHookBootstrapService:
    expected_version: str = "0.1.163"

    def _run(self, argv: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(argv, shell=False, check=False, capture_output=True, **kwargs)

    def _analyze(self, nat_text: str) -> dict[str, object]:
        lines = nat_text.splitlines()
        chain_count = sum(l.startswith(":MPF_NAT_PRE ") for l in lines)
        hook_count = sum("-A PREROUTING" in l and "-j MPF_NAT_PRE" in l for l in lines)
        canary_exact = sum("-A MPF_NAT_PRE" in l and "canary-btc-001" in l and "--dport 20001" in l and "--to-destination 127.0.0.1:60010" in l for l in lines)
        docker_local_publish_seen = any("127.0.0.1:60010" in l and "DOCKER" in l for l in lines)
        unrelated_mpf_customer_nat = any(("mpf:" in l or "canary-btc-001" in l or "--dport 20001" in l) and "-A MPF_NAT_PRE" not in l for l in lines)
        return {
            "chain_count": chain_count,
            "chain_exists": chain_count == 1,
            "hook_count": hook_count,
            "hook_exists": hook_count == 1,
            "canary_rule_exists": canary_exact == 1,
            "docker_local_publish_seen": docker_local_publish_seen,
            "unrelated_mpf_customer_nat": unrelated_mpf_customer_nat,
        }

    def _render_bootstrap_payload(self) -> str:
        return """# mpf:phase11_single_canary_nat_hook_bootstrap
*nat
:MPF_NAT_PRE - [0:0]
-A PREROUTING -j MPF_NAT_PRE
COMMIT
"""

    def run(self, report: dict[str, object]) -> dict[str, object]:
        request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
        if request.get("requested_action") != "execute":
            return {"status": "blocked", "error": "single_canary_execute_only"}
        if request.get("expected_version") != self.expected_version:
            return {"status": "blocked", "error": "wrong_expected_version"}
        if request.get("customer_key") != "canary-btc-001" or request.get("lane") != "btc" or request.get("port") != 20001:
            return {"status": "blocked", "error": "single_canary_scope_mismatch"}

        nat = self._run(["iptables-save", "-t", "nat"], text=True)
        if nat.returncode != 0:
            return {"status": "blocked", "error": "unsafe_live_nat_state"}
        live_sha = hashlib.sha256(nat.stdout.encode()).hexdigest()
        analysis = self._analyze(nat.stdout)
        out = {
            "live_nat_sha256": live_sha,
            "chain_exists": analysis["chain_exists"],
            "hook_exists": analysis["hook_exists"],
            "hook_count": analysis["hook_count"],
            "canary_rule_exists": analysis["canary_rule_exists"],
            "docker_local_publish_seen": analysis["docker_local_publish_seen"],
            "mutation_performed": False,
            "firewall_mutation_performed": False,
            "nat_mutation_performed": False,
            "production_traffic_enabled": False,
        }
        if analysis["chain_count"] > 1:
            return {"status": "blocked", "error": "duplicate_mpf_nat_pre_chain_detected", **out}
        if analysis["hook_count"] > 1:
            return {"status": "blocked", "error": "duplicate_nat_hook_detected", **out}
        if analysis["unrelated_mpf_customer_nat"]:
            return {"status": "blocked", "error": "unrelated_mpf_customer_nat_detected", **out}
        if analysis["chain_exists"] and analysis["hook_exists"]:
            return {"status": "ok", "action": "already_ready", **out}

        payload = self._render_bootstrap_payload()
        payload_sha = hashlib.sha256(payload.encode()).hexdigest()
        out["payload_sha256"] = payload_sha

        if os.environ.get("MPF_PHASE11_SINGLE_CANARY_NAT_HOOK_BOOTSTRAP") != "allow":
            return {"status": "ok", "action": "needs_bootstrap", **out}
        for env in ("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE"):
            if os.environ.get(env) != "allow":
                return {"status": "blocked", "error": "single_canary_host_apply_execution_not_confirmed", **out}

        test = self._run(["iptables-restore", "--test", "--noflush"], input=payload, text=True)
        if test.returncode != 0:
            return {"status": "blocked", "error": "single_canary_nat_hook_bootstrap_not_apply_safe", "missing_primitive": "accepted_safe_single_canary_nat_hook_bootstrap", **out}
        apply = self._run(["iptables-restore", "--noflush"], input=payload, text=True)
        if apply.returncode != 0:
            return {"status": "blocked", "error": "single_canary_nat_hook_bootstrap_not_apply_safe", "missing_primitive": "accepted_safe_single_canary_nat_hook_bootstrap", **out}

        post = self._run(["iptables-save", "-t", "nat"], text=True)
        post_sha = hashlib.sha256(post.stdout.encode()).hexdigest() if post.returncode == 0 else None
        out.update({"pre_bootstrap_nat_sha256": live_sha, "post_bootstrap_nat_sha256": post_sha, "mutation_performed": True, "firewall_mutation_performed": True, "nat_mutation_performed": True})
        report["live_nat_prerequisites"] = {"mpf_nat_pre_chain_exists": True, "prerouting_hook_to_mpf_nat_pre_count": 1}
        return {"status": "ok", "action": "bootstrapped", **out}
