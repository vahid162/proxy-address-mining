from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11ExactCanaryRestorePayloadRenderer:
    expected_version: str = "0.1.186"

    def render(self, report: dict[str, object]) -> dict[str, object]:
        request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
        if request.get("requested_action") != "execute":
            return {"status": "blocked", "error": "single_canary_execute_only"}
        if request.get("expected_version") != self.expected_version:
            return {"status": "blocked", "error": "wrong_expected_version"}
        if request.get("customer_key") != "canary-btc-001" or request.get("lane") != "btc" or request.get("port") != 20001:
            return {"status": "blocked", "error": "single_canary_scope_mismatch"}
        if report.get("scope", {}).get("single_canary_only") is not True:
            return {"status": "blocked", "error": "non_single_canary_scope"}

        nat_pre = report.get("live_nat_prerequisites", {}) if isinstance(report.get("live_nat_prerequisites"), dict) else {}
        if nat_pre.get("mpf_nat_pre_chain_exists") is not True or nat_pre.get("prerouting_hook_to_mpf_nat_pre_count") != 1:
            return {
                "status": "blocked",
                "error": "single_canary_restore_payload_not_apply_safe",
                "missing_primitive": "accepted_apply_safe_single_canary_payload",
            }

        backend_target = report.get("single_canary_backend_target", {}) if isinstance(report.get("single_canary_backend_target"), dict) else {}
        target_host = backend_target.get("target_host")
        target_port = backend_target.get("target_port")
        if not isinstance(target_host, str) or not target_host:
            return {"status": "blocked", "error": "single_canary_backend_target_missing"}
        if target_host.startswith("127."):
            return {"status": "blocked", "error": "single_canary_backend_target_loopback_forbidden"}
        if target_port != 60010 or backend_target.get("target_kind") != "docker_container_ipv4":
            return {"status": "blocked", "error": "single_canary_backend_target_invalid"}

        bootstrap = report.get("nat_hook_bootstrap", {}) if isinstance(report.get("nat_hook_bootstrap"), dict) else {}
        canary_rule_exists = (nat_pre.get("canary_rule_exists") is True) or (bootstrap.get("canary_rule_exists") is True)

        payload = "# mpf:phase11_exact_single_canary_restore canary-btc-001\n"
        if not canary_rule_exists:
            payload += (
                "*nat\n"
                f"-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination {target_host}:60010\n"
                "COMMIT\n"
            )
        payload += (
            "*filter\n"
            ":MPFC_20001 - [0:0]\n"
            "-A MPFC_20001 -p tcp --dport 20001 -m connlimit --connlimit-above 0 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n"
            "-A MPFC_20001 -p tcp --dport 20001 -m hashlimit --hashlimit-above 1/min --hashlimit-burst 1 --hashlimit-mode srcip --hashlimit-name mpf-canary-btc-001-20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\n"
            "COMMIT\n"
        )
        expected_dport_count = 2 if canary_rule_exists else 3
        expected_target_count = 0 if canary_rule_exists else 1
        if payload.count("--dport 20001") != expected_dport_count or payload.count(f"{target_host}:60010") != expected_target_count or "canary-btc-001" not in payload:
            return {"status": "error", "error": "single_canary_payload_validation_failed"}
        if canary_rule_exists and ("*nat" in payload or "customer_nat_redirect" in payload):
            return {"status": "error", "error": "single_canary_payload_validation_failed"}
        if any(k in payload for k in ("*mangle", "*raw", "-F", "-X", "-D", "-I", "-N MPF_NAT_PRE", "-A PREROUTING")):
            return {"status": "blocked", "error": "single_canary_restore_payload_not_apply_safe", "missing_primitive": "accepted_apply_safe_single_canary_payload"}

        return {
            "status": "ok",
            "restore_payload": payload,
            "payload_kind": "iptables_restore_single_canary_exact",
            "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "renderer_scope": "single_canary_only",
            "customer_key": "canary-btc-001",
            "lane": "btc",
            "customer_port": 20001,
            "backend_port": 60010,
            "mutation_performed": False,
            "firewall_mutation_performed": False,
            "nat_mutation_performed": False,
            "production_traffic_enabled": False,
        }
