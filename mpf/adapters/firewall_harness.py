from __future__ import annotations

from mpf.domain.firewall import FirewallHarnessCall, FirewallHarnessFailure, FirewallHarnessResult


class FakeNoopFirewallHarnessAdapter:
    def __init__(self, fail_apply: bool = False, fail_verify: bool = False, fail_rollback: bool = False) -> None:
        self._fail_apply = fail_apply
        self._fail_verify = fail_verify
        self._fail_rollback = fail_rollback
        self._calls: list[FirewallHarnessCall] = []

    @property
    def calls(self) -> list[FirewallHarnessCall]:
        return list(self._calls)

    def _record(self, operation: str) -> FirewallHarnessResult:
        self._calls.append(FirewallHarnessCall(operation=operation, sequence=len(self._calls) + 1))
        return FirewallHarnessResult(ok=True, operation=operation, calls=self.calls)

    def plan(self) -> FirewallHarnessResult:
        return self._record("plan")

    def apply(self) -> FirewallHarnessResult:
        result = self._record("apply")
        if self._fail_apply:
            return FirewallHarnessResult(ok=False, operation="apply", calls=self.calls, failure=FirewallHarnessFailure(operation="apply", message="injected apply failure"))
        return result

    def verify(self) -> FirewallHarnessResult:
        result = self._record("verify")
        if self._fail_verify:
            return FirewallHarnessResult(ok=False, operation="verify", calls=self.calls, failure=FirewallHarnessFailure(operation="verify", message="injected verify failure"))
        return result

    def rollback(self) -> FirewallHarnessResult:
        result = self._record("rollback")
        if self._fail_rollback:
            return FirewallHarnessResult(ok=False, operation="rollback", calls=self.calls, failure=FirewallHarnessFailure(operation="rollback", message="injected rollback failure"))
        return result
