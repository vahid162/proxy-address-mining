from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryNatHookBootstrapService:
    expected_version: str = "0.1.173"

    def _run(self, argv: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(argv, shell=False, check=False, capture_output=True, **kwargs)

    def _analyze(self, nat_text: str) -> dict[str, object]:
        lines = nat_text.splitlines()
        chain_count = sum(line.startswith(":MPF_NAT_PRE ") for line in lines)
        hook_count = sum("-A PREROUTING" in line and "-j MPF_NAT_PRE" in line for line in lines)
        canary_lines = [line for line in lines if "canary-btc-001" in line or "--dport 20001" in line]
        canary_exact_count = sum(
            "-A MPF_NAT_PRE" in line
            and "canary-btc-001" in line
            and "--dport 20001" in line
            and "--to-destination 127.0.0.1:60010" in line
            for line in lines
        )
        docker_local_publish_seen = any("DOCKER" in line and "--dport 60010" in line for line in lines)
        unrelated_mpf_customer_nat = any(
            ("mpf:" in line or "canary-btc-001" in line or "--dport 20001" in line)
            and "-A MPF_NAT_PRE" not in line
            and "DOCKER" not in line
            for line in lines
        )
        return {
            "chain_count": chain_count,
            "chain_exists": chain_count == 1,
            "hook_count": hook_count,
            "hook_exists": hook_count == 1,
            "canary_rule_count": len(canary_lines),
            "canary_exact_count": canary_exact_count,
            "canary_rule_exists": canary_exact_count == 1,
            "docker_local_publish_seen": docker_local_publish_seen,
            "unrelated_mpf_customer_nat": unrelated_mpf_customer_nat,
        }

    def _render_bootstrap_payload(self, analysis: dict[str, object]) -> str:
        payload_lines = ["# mpf:phase11_single_canary_nat_hook_bootstrap", "*nat"]
        if analysis.get("chain_exists") is not True:
            payload_lines.append(":MPF_NAT_PRE - [0:0]")
        if analysis.get("hook_exists") is not True:
            payload_lines.append("-A PREROUTING -j MPF_NAT_PRE")
        payload_lines.append("COMMIT")
        return "\n".join(payload_lines) + "\n"

    def _validate_bootstrap_payload(self, payload: str) -> bool:
        forbidden = (
            "--dport 20001",
            "--to-destination",
            "DNAT",
            "DOCKER",
            "*filter",
            "*mangle",
            "*raw",
            "-F",
            "-X",
            "-D",
            "-I",
        )
        if any(token in payload for token in forbidden):
            return False
        if payload.count("*nat") != 1 or payload.count("COMMIT") != 1:
            return False
        return ":MPF_NAT_PRE " in payload or "-A PREROUTING -j MPF_NAT_PRE" in payload

    def _base_output(self, live_sha: str, analysis: dict[str, object]) -> dict[str, object]:
        return {
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

    def _preconditions_ok(self, report: dict[str, object], out: dict[str, object]) -> dict[str, object] | None:
        request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
        for flag in (
            "operator_confirmed",
            "understand_canary_customer",
            "understand_firewall_apply",
            "reviewed_rollback",
            "fresh_farm5_sync_confirmed",
        ):
            if request.get(flag) is not True:
                return {"status": "blocked", "error": f"missing_{flag}", **out}
        for gate in (
            "phase_gate",
            "mpf_doctor",
            "db_status",
            "proxy_doctor",
            "no_customer_nat_baseline",
            "no_customer_firewall_baseline",
            "local_only_runtime_baseline",
        ):
            if report.get("preflight_results", {}).get(gate) != "OK":
                return {"status": "blocked", "error": f"precondition_failed:{gate}", **out}
        if not report.get("restore_point") or report.get("restore_point", {}).get("status") == "placeholder":
            return {"status": "blocked", "error": "missing_non_placeholder_restore_point", **out}
        if not report.get("iptables_save_backup") or report.get("iptables_save_backup", {}).get("status") == "placeholder":
            return {"status": "blocked", "error": "missing_non_placeholder_iptables_save_backup", **out}
        if report.get("lock", {}).get("acquired") is not True:
            return {"status": "blocked", "error": "missing_lock", **out}
        return None

    def run(self, report: dict[str, object]) -> dict[str, object]:
        request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
        if request.get("requested_action") != "execute":
            return {"status": "blocked", "error": "single_canary_execute_only"}
        if request.get("expected_version") != self.expected_version:
            return {"status": "blocked", "error": "wrong_expected_version"}
        if request.get("customer_key") != "canary-btc-001" or request.get("lane") != "btc" or request.get("port") != 20001:
            return {"status": "blocked", "error": "single_canary_scope_mismatch"}
        if report.get("scope", {}).get("single_canary_only") is not True:
            return {"status": "blocked", "error": "non_single_canary_scope"}

        nat = self._run(["iptables-save", "-t", "nat"], text=True)
        if nat.returncode != 0:
            return {"status": "blocked", "error": "unsafe_live_nat_state"}
        live_sha = hashlib.sha256(nat.stdout.encode()).hexdigest()
        analysis = self._analyze(nat.stdout)
        out = self._base_output(live_sha, analysis)

        if analysis["chain_count"] > 1:
            return {"status": "blocked", "error": "duplicate_mpf_nat_pre_chain_detected", **out}
        if analysis["hook_count"] > 1:
            return {"status": "blocked", "error": "duplicate_nat_hook_detected", **out}
        if analysis["hook_exists"] and not analysis["chain_exists"]:
            return {"status": "blocked", "error": "unsafe_live_nat_state", **out}
        if analysis["unrelated_mpf_customer_nat"]:
            return {"status": "blocked", "error": "unrelated_mpf_customer_nat_detected", **out}
        if analysis["canary_rule_count"] and analysis["canary_exact_count"] != 1:
            return {"status": "blocked", "error": "single_canary_conflicting_rule_detected", **out}
        if analysis["chain_exists"] and analysis["hook_exists"]:
            report["live_nat_prerequisites"] = {"mpf_nat_pre_chain_exists": True, "prerouting_hook_to_mpf_nat_pre_count": 1}
            return {"status": "ok", "action": "already_ready", **out}

        payload = self._render_bootstrap_payload(analysis)
        if not self._validate_bootstrap_payload(payload):
            return {
                "status": "blocked",
                "error": "single_canary_nat_hook_bootstrap_not_apply_safe",
                "missing_primitive": "accepted_safe_single_canary_nat_hook_bootstrap",
                **out,
            }
        out["payload_sha256"] = hashlib.sha256(payload.encode()).hexdigest()

        if os.environ.get("MPF_PHASE11_SINGLE_CANARY_NAT_HOOK_BOOTSTRAP") != "allow":
            return {"status": "ok", "action": "needs_bootstrap", **out}
        if os.environ.get("CI"):
            return {"status": "blocked", "error": "single_canary_nat_hook_bootstrap_not_allowed_in_ci", **out}
        precondition_error = self._preconditions_ok(report, out)
        if precondition_error is not None:
            return precondition_error
        for env in (
            "MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP",
            "MPF_PHASE11_SINGLE_CANARY_HOST_APPLY",
            "MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE",
        ):
            if os.environ.get(env) != "allow":
                return {"status": "blocked", "error": "single_canary_host_apply_execution_not_confirmed", **out}

        test = self._run(["iptables-restore", "--test", "--noflush"], input=payload, text=True)
        if test.returncode != 0:
            return {
                "status": "blocked",
                "error": "single_canary_nat_hook_bootstrap_not_apply_safe",
                "missing_primitive": "accepted_safe_single_canary_nat_hook_bootstrap",
                **out,
            }
        apply = self._run(["iptables-restore", "--noflush"], input=payload, text=True)
        if apply.returncode != 0:
            return {
                "status": "blocked",
                "error": "single_canary_nat_hook_bootstrap_apply_failed",
                "mutation_performed": False,
                **out,
            }

        post = self._run(["iptables-save", "-t", "nat"], text=True)
        post_sha = hashlib.sha256(post.stdout.encode()).hexdigest() if post.returncode == 0 else None
        post_analysis = self._analyze(post.stdout) if post.returncode == 0 else {}
        mutation_evidence = {
            **out,
            "pre_bootstrap_nat_sha256": live_sha,
            "post_bootstrap_nat_sha256": post_sha,
            "pre_apply_nat_sha256": live_sha,
            "post_apply_nat_sha256": post_sha,
            "mutation_performed": True,
            "firewall_mutation_performed": True,
            "nat_mutation_performed": True,
            "production_traffic_enabled": False,
        }
        if post.returncode != 0 or post_analysis.get("chain_exists") is not True or post_analysis.get("hook_exists") is not True or post_analysis.get("hook_count") != 1:
            return {
                "status": "error",
                "error": "single_canary_nat_hook_bootstrap_verification_failed",
                "partial_mutation": True,
                "rollback_instructions": "restore the pre-bootstrap iptables-save backup using the accepted operator rollback path",
                **mutation_evidence,
            }
        if post_analysis.get("unrelated_mpf_customer_nat") or post_analysis.get("chain_count", 0) > 1:
            return {
                "status": "error",
                "error": "single_canary_nat_hook_bootstrap_post_state_unsafe",
                "partial_mutation": True,
                "rollback_instructions": "restore the pre-bootstrap iptables-save backup using the accepted operator rollback path",
                **mutation_evidence,
            }
        report["live_nat_prerequisites"] = {"mpf_nat_pre_chain_exists": True, "prerouting_hook_to_mpf_nat_pre_count": 1}
        return {"status": "ok", "action": "bootstrapped", **mutation_evidence}
