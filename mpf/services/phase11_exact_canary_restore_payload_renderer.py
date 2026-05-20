from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11ExactCanaryRestorePayloadRenderer:
    expected_version: str = "0.1.160"

    def render(self, report: dict[str, object]) -> dict[str, object]:
        request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
        if request.get("requested_action") != "execute":
            return {"status": "blocked", "error": "single_canary_execute_only"}
        if request.get("expected_version") != self.expected_version:
            return {"status": "blocked", "error": "wrong_expected_version"}
        if request.get("customer_key") != "canary-btc-001":
            return {"status": "blocked", "error": "wrong_customer_key"}
        if request.get("lane") != "btc":
            return {"status": "blocked", "error": "wrong_lane"}
        if request.get("port") != 20001:
            return {"status": "blocked", "error": "wrong_customer_port"}
        if report.get("scope", {}).get("single_canary_only") is not True:
            return {"status": "blocked", "error": "non_single_canary_scope"}

        for flag in ("operator_confirmed", "understand_canary_customer", "understand_firewall_apply", "reviewed_rollback", "fresh_farm5_sync_confirmed"):
            if request.get(flag) is not True:
                return {"status": "blocked", "error": f"missing_{flag}"}
        for gate in ("phase_gate", "mpf_doctor", "db_status", "proxy_doctor", "no_customer_nat_baseline", "no_customer_firewall_baseline", "local_only_runtime_baseline"):
            if report.get("preflight_results", {}).get(gate) != "OK":
                return {"status": "blocked", "error": f"precondition_failed:{gate}"}

        restore = report.get("restore_point") or {}
        backup = report.get("iptables_save_backup") or {}
        if not restore:
            return {"status": "blocked", "error": "missing_restore_point"}
        if not backup:
            return {"status": "blocked", "error": "missing_iptables_save_backup"}
        if restore.get("status") == "placeholder":
            return {"status": "blocked", "error": "restore_point_placeholder_not_accepted_for_execute"}
        if backup.get("status") == "placeholder":
            return {"status": "blocked", "error": "iptables_save_backup_placeholder_not_accepted_for_execute"}
        if report.get("lock", {}).get("acquired") is not True:
            return {"status": "blocked", "error": "missing_lock"}

        plan = report.get("firewall_plan") or {}
        if plan.get("status") != "ok":
            return {"status": "blocked", "error": "missing_plan"}
        if plan.get("lane") != "btc" or plan.get("customer_port") != 20001 or plan.get("backend_port") != 60010:
            return {"status": "blocked", "error": "single_canary_plan_scope_mismatch"}

        diff = (report.get("firewall_diff") or {}).get("json_diff", {})
        if diff.get("customer_port") != 20001:
            return {"status": "blocked", "error": "wrong_diff_customer_port"}
        if diff.get("backend_port") != 60010:
            return {"status": "blocked", "error": "wrong_diff_backend_port"}

        payload = (
            "# mpf:phase11_exact_single_canary_restore canary-btc-001\n"
            "*nat\n"
            "-N MPF_NAT_PRE\n"
            "-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 127.0.0.1:60010\n"
            "COMMIT\n"
        )
        if payload.count("--dport 20001") != 1 or "--to-destination 127.0.0.1:60010" not in payload or "canary-btc-001" not in payload:
            return {"status": "error", "error": "single_canary_payload_validation_failed"}
        if "--dport " in payload.replace("--dport 20001", ""):
            return {"status": "blocked", "error": "single_canary_broad_payload_blocked"}
        if payload.count("COMMIT") != 1:
            return {"status": "blocked", "error": "single_canary_unrelated_tables_blocked"}

        sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return {
            "status": "ok",
            "restore_payload": payload,
            "payload_kind": "iptables_restore_single_canary_exact",
            "customer_key": "canary-btc-001",
            "lane": "btc",
            "customer_port": 20001,
            "backend_port": 60010,
            "renderer_scope": "single_canary_only",
            "payload_sha256": sha,
            "validation_summary": "exact_single_canary_payload_validated",
            "mutation_performed": False,
            "firewall_mutation_performed": False,
            "nat_mutation_performed": False,
            "production_traffic_enabled": False,
        }
