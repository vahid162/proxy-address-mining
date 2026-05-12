from __future__ import annotations

from dataclasses import dataclass, field

from mpf.adapters.firewall_harness import FakeNoopFirewallHarnessAdapter
from mpf.domain.firewall import FirewallHarnessResult


@dataclass
class FirewallHarnessWorkflowReport:
    mode: str
    ok: bool
    calls: list[str] = field(default_factory=list)
    apply: FirewallHarnessResult | None = None
    verify: FirewallHarnessResult | None = None
    rollback: FirewallHarnessResult | None = None
    report_only: bool = True
    database_write: bool = False
    lock_acquired: bool = False
    restore_point_written: bool = False


def run_apply_verify_harness(adapter: FakeNoopFirewallHarnessAdapter) -> FirewallHarnessWorkflowReport:
    adapter.plan()
    apply_result = adapter.apply()
    if not apply_result.ok:
        return FirewallHarnessWorkflowReport(mode="apply_verify", ok=False, calls=[c.operation for c in adapter.calls], apply=apply_result)

    verify_result = adapter.verify()
    return FirewallHarnessWorkflowReport(mode="apply_verify", ok=verify_result.ok, calls=[c.operation for c in adapter.calls], apply=apply_result, verify=verify_result)


def run_verify_failure_with_rollback_guidance(adapter: FakeNoopFirewallHarnessAdapter) -> FirewallHarnessWorkflowReport:
    adapter.plan()
    apply_result = adapter.apply()
    verify_result = adapter.verify() if apply_result.ok else None
    rollback_result = adapter.rollback() if (verify_result is not None and not verify_result.ok) else None
    ok = bool(apply_result.ok and verify_result is not None and verify_result.ok)
    return FirewallHarnessWorkflowReport(
        mode="verify_failure_rollback_guidance",
        ok=ok,
        calls=[c.operation for c in adapter.calls],
        apply=apply_result,
        verify=verify_result,
        rollback=rollback_result,
    )
