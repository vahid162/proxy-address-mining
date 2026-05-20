from __future__ import annotations

from dataclasses import dataclass

from mpf.services.phase11_manual_canary_execution_run_service import CanaryExecutionAdapters
from mpf.services.phase11_single_canary_host_apply_primitive import SingleCanaryHostApplyPrimitive
from mpf.services.phase11_single_canary_restore_backup_adapter import SingleCanaryRestoreBackupAdapter


@dataclass(slots=True)
class _ReadinessAdapter:
    def check_readiness(self, report: dict[str, object]) -> dict[str, object]:
        return {"status": "ok", "preflight_results": report.get("preflight_results", {})}


@dataclass(slots=True)
class _RestoreAdapter:
    adapter: SingleCanaryRestoreBackupAdapter | None = None

    def _run_execute(self, report: dict[str, object]) -> dict[str, object]:
        if isinstance(report.get("_single_canary_restore_backup_result"), dict):
            return report["_single_canary_restore_backup_result"]
        adapter = self.adapter or SingleCanaryRestoreBackupAdapter()
        result = adapter.run(report)
        report["_single_canary_restore_backup_result"] = result
        return result

    def create_restore_point(self, report: dict[str, object]) -> dict[str, object]:
        if report.get("request", {}).get("requested_action") != "execute":
            return {"status": "ok", "restore_point": {"status": "placeholder", "mode": "service_layer_boundary"}}
        result = self._run_execute(report)
        if result.get("status") != "ok":
            return {"status": result.get("status", "error"), "error": result.get("error", "real_restore_backup_failed")}
        return {"status": "ok", "restore_point": result.get("restore_point")}

    def create_iptables_save_backup(self, report: dict[str, object]) -> dict[str, object]:
        if report.get("request", {}).get("requested_action") != "execute":
            return {"status": "ok", "iptables_save_backup": {"status": "placeholder", "mode": "service_layer_boundary"}}
        result = self._run_execute(report)
        if result.get("status") != "ok":
            return {"status": result.get("status", "error"), "error": result.get("error", "real_restore_backup_failed")}
        backup = result.get("iptables_save_backup")
        if isinstance(backup, dict):
            backup.setdefault("backup_path", result.get("backup_path"))
            backup.setdefault("backup_sha256", result.get("backup_sha256"))
        return {"status": "ok", "iptables_save_backup": backup}


@dataclass(slots=True)
class _LockAdapter:
    acquired: bool = False

    def acquire(self, report: dict[str, object]) -> dict[str, object]:
        self.acquired = True
        return {"acquired": True}

    def release(self, report: dict[str, object]) -> dict[str, object]:
        released = self.acquired
        self.acquired = False
        return {"released": released}


@dataclass(slots=True)
class _CustomerAdapter:
    def ensure_customer(self, report: dict[str, object]) -> dict[str, object]:
        request = report.get("request", {})
        return {
            "status": "ok",
            "idempotent": True,
            "customer_key": request.get("customer_key"),
            "lane": request.get("lane"),
            "port": request.get("port"),
        }


@dataclass(slots=True)
class _FirewallAdapter:
    host_apply_primitive: object | None = None

    def build_plan(self, report: dict[str, object]) -> dict[str, object]:
        request = report.get("request", {})
        if request.get("customer_key") != "canary-btc-001":
            return {"status": "blocked", "error": "wrong_customer_key"}
        if request.get("lane") != "btc":
            return {"status": "blocked", "error": "wrong_lane"}
        if request.get("port") != 20001:
            return {"status": "blocked", "error": "wrong_customer_port"}
        if report.get("scope", {}).get("single_canary_only") is not True:
            return {"status": "blocked", "error": "non_single_canary_scope"}
        return {
            "status": "ok",
            "lane": request.get("lane"),
            "customer_port": request.get("port"),
            "backend_port": 60010,
        }

    def render_diff(self, report: dict[str, object]) -> dict[str, object]:
        return {"status": "ok", "human_diff": "canary-btc-001:20001 -> btc:60010", "json_diff": {"customer_port": 20001, "backend_port": 60010}}

    def apply_plan(self, report: dict[str, object]) -> dict[str, object]:
        if report.get("lock", {}).get("acquired") is not True:
            return {"status": "blocked", "error": "missing_lock"}
        if report.get("restore_point") is None:
            return {"status": "blocked", "error": "missing_restore_point"}
        if report.get("iptables_save_backup") is None:
            return {"status": "blocked", "error": "missing_iptables_save_backup"}
        diff = report.get("firewall_diff") or {}
        json_diff = diff.get("json_diff", {}) if isinstance(diff, dict) else {}
        if json_diff.get("customer_port") != 20001 or json_diff.get("backend_port") != 60010:
            return {"status": "blocked", "error": "firewall_diff_not_reviewed"}
        payload = report.get("firewall_plan", {}).get("restore_payload")
        if not isinstance(payload, str):
            return {
                "status": "blocked",
                "error": "single_canary_restore_payload_renderer_missing",
                "missing_primitive": "accepted_exact_canary_restore_payload_renderer",
            }
        primitive = self.host_apply_primitive or SingleCanaryHostApplyPrimitive()
        return primitive.execute(report)


@dataclass(slots=True)
class _VerifyAdapter:
    def verify_post_apply(self, report: dict[str, object]) -> dict[str, object]: return {"status": "instruction_required", "note": "post-apply verify requires accepted real firewall apply adapter"}
    def verify_canary_connection(self, report: dict[str, object]) -> dict[str, object]: return {"status": "instruction_required"}
    def verify_nat_hit(self, report: dict[str, object]) -> dict[str, object]: return {"status": "instruction_required"}
    def verify_usage(self, report: dict[str, object]) -> dict[str, object]: return {"status": "instruction_required"}
    def verify_reject(self, report: dict[str, object]) -> dict[str, object]: return {"status": "instruction_required"}
    def verify_session_worker(self, report: dict[str, object]) -> dict[str, object]: return {"status": "instruction_required"}
    def verify_abuse_coverage(self, report: dict[str, object]) -> dict[str, object]: return {"status": "instruction_required"}
    def rollback_readiness(self, report: dict[str, object]) -> dict[str, object]: return {"status": "ok"}


@dataclass(slots=True)
class _EvidenceAdapter:
    def emit_evidence(self, report: dict[str, object]) -> dict[str, object]: return {"status": "ok", "mode": "service_layer_boundary", "saved": False}


def build_manual_canary_production_adapters() -> dict[str, object]:
    adapters = CanaryExecutionAdapters(
        readiness=_ReadinessAdapter(),
        restore=_RestoreAdapter(adapter=SingleCanaryRestoreBackupAdapter()),
        lock=_LockAdapter(),
        customer=_CustomerAdapter(),
        firewall=_FirewallAdapter(host_apply_primitive=SingleCanaryHostApplyPrimitive()),
        verify=_VerifyAdapter(),
        evidence=_EvidenceAdapter(),
    )
    return {
        "readiness": adapters.readiness,
        "restore": adapters.restore,
        "lock": adapters.lock,
        "customer": adapters.customer,
        "firewall": adapters.firewall,
        "verify": adapters.verify,
        "evidence": adapters.evidence,
    }
