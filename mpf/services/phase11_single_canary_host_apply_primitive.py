from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class SingleCanaryHostApplyPrimitive:
    expected_version: str = "0.1.158"
    host_apply_executor: Callable[[dict[str, object], str], dict[str, object]] | None = None
    post_apply_verifier: Callable[[dict[str, object]], dict[str, object]] | None = None

    def execute(self, report: dict[str, object]) -> dict[str, object]:
        request = report.get("request", {}) if isinstance(report.get("request"), dict) else {}

        if request.get("requested_action") != "execute":
            return {"status": "blocked", "error": "single_canary_execute_only"}
        if request.get("customer_key") != "canary-btc-001":
            return {"status": "blocked", "error": "wrong_customer_key"}
        if request.get("lane") != "btc":
            return {"status": "blocked", "error": "wrong_lane"}
        if request.get("port") != 20001:
            return {"status": "blocked", "error": "wrong_customer_port"}
        if report.get("scope", {}).get("single_canary_only") is not True:
            return {"status": "blocked", "error": "non_single_canary_scope"}
        if request.get("expected_version") != self.expected_version:
            return {"status": "blocked", "error": "wrong_expected_version"}

        for flag in ("operator_confirmed", "understand_canary_customer", "understand_firewall_apply", "reviewed_rollback", "fresh_farm5_sync_confirmed"):
            if request.get(flag) is not True:
                return {"status": "blocked", "error": f"missing_{flag}"}

        if os.environ.get("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY") != "allow" or os.environ.get("CI"):
            return {"status": "blocked", "error": "single_canary_host_apply_context_not_confirmed"}

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

        diff = report.get("firewall_diff", {}).get("json_diff", {})
        if diff.get("customer_port") != 20001:
            return {"status": "blocked", "error": "wrong_diff_customer_port"}
        if diff.get("backend_port") != 60010:
            return {"status": "blocked", "error": "wrong_diff_backend_port"}

        payload = report.get("firewall_plan", {}).get("restore_payload")
        if not isinstance(payload, str):
            return {"status": "blocked", "error": "single_canary_restore_payload_renderer_missing", "missing_primitive": "accepted_exact_canary_restore_payload_renderer"}
        if "--dport 20001" not in payload or "--to-destination 127.0.0.1:60010" not in payload:
            return {"status": "blocked", "error": "single_canary_payload_scope_mismatch"}
        if "--dport " in payload.replace("--dport 20001", ""):
            return {"status": "blocked", "error": "single_canary_broad_payload_blocked"}

        if report.get("existing_canary_state") == "exact":
            return {"status": "ok", "applied": False, "existing_state_verified": True, "iptables_restore_used": False}
        if report.get("existing_canary_state") == "conflict":
            return {"status": "blocked", "error": "single_canary_conflicting_rule_detected", "conflict": report.get("existing_canary_conflict", "unknown")}

        if self.host_apply_executor is None:
            return {
                "status": "blocked",
                "error": "accepted_single_canary_host_apply_execution_missing",
                "missing_primitive": "accepted_single_canary_host_apply_execution",
            }

        try:
            apply_result = self.host_apply_executor(report, payload)
        except Exception as exc:
            return {"status": "error", "error": f"single_canary_host_apply_exception: {exc}"}
        if not isinstance(apply_result, dict):
            return {"status": "error", "error": "single_canary_host_apply_invalid_response"}
        if apply_result.get("status") != "ok" or apply_result.get("applied") is not True:
            return {"status": "blocked", "error": apply_result.get("error", "single_canary_host_apply_failed")}

        if self.post_apply_verifier is None:
            return {"status": "blocked", "error": "single_canary_post_apply_verification_missing"}
        try:
            verify_result = self.post_apply_verifier(report)
        except Exception as exc:
            return {"status": "error", "error": f"single_canary_post_apply_verification_exception: {exc}"}
        if not isinstance(verify_result, dict):
            return {"status": "error", "error": "single_canary_post_apply_verification_invalid_response"}
        if verify_result.get("status") != "ok" or verify_result.get("nat_rule_verified") is not True:
            return {"status": "blocked", "error": verify_result.get("error", "single_canary_post_apply_verification_missing")}

        return {"status": "ok", "applied": True, "existing_state_verified": False, "customer_port": 20001, "backend_port": 60010, "iptables_restore_used": bool(apply_result.get("iptables_restore_used") is True), "nat_rule_verified": True}
