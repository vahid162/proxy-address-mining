from __future__ import annotations

from dataclasses import dataclass

from mpf.services.phase11_manual_canary_execution_run_service import CanaryExecutionAdapters


@dataclass(slots=True)
class _ReadinessAdapter:
    def check_readiness(self, report: dict[str, object]) -> dict[str, object]:
        return {"status": "ok", "preflight_results": report.get("preflight_results", {})}


@dataclass(slots=True)
class _RestoreAdapter:
    def create_restore_point(self, report: dict[str, object]) -> dict[str, object]:
        return {"status": "ok", "restore_point": {"status": "placeholder", "mode": "service_layer_boundary"}}

    def create_iptables_save_backup(self, report: dict[str, object]) -> dict[str, object]:
        return {"status": "ok", "iptables_save_backup": {"status": "placeholder", "mode": "service_layer_boundary"}}


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
    def build_plan(self, report: dict[str, object]) -> dict[str, object]:
        request = report.get("request", {})
        return {
            "status": "ok",
            "lane": request.get("lane"),
            "customer_port": request.get("port"),
            "backend_port": 60010,
        }

    def render_diff(self, report: dict[str, object]) -> dict[str, object]:
        return {"status": "ok", "human_diff": "canary-btc-001:20001 -> btc:60010", "json_diff": {"customer_port": 20001, "backend_port": 60010}}

    def apply_plan(self, report: dict[str, object]) -> dict[str, object]:
        return {"status": "blocked", "error": "missing_real_firewall_apply_adapter"}


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
        restore=_RestoreAdapter(),
        lock=_LockAdapter(),
        customer=_CustomerAdapter(),
        firewall=_FirewallAdapter(),
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
