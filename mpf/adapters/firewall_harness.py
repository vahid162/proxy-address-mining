from __future__ import annotations

from mpf.domain.firewall import FirewallHarnessCall, FirewallHarnessFailure, FirewallHarnessResult


class FakeNoopFirewallHarnessAdapter:
    def __init__(
        self,
        fail_plan: bool = False,
        fail_apply: bool = False,
        fail_verify: bool = False,
        fail_rollback: bool = False,
    ) -> None:
        self._fail_plan = fail_plan
        self._fail_apply = fail_apply
        self._fail_verify = fail_verify
        self._fail_rollback = fail_rollback
        self._calls: list[FirewallHarnessCall] = []

    @property
    def calls(self) -> list[FirewallHarnessCall]:
        return list(self._calls)

    def reset(self) -> None:
        self._calls = []

    def _record(self, operation: str) -> FirewallHarnessResult:
        self._calls.append(FirewallHarnessCall(operation=operation, sequence=len(self._calls) + 1))
        return FirewallHarnessResult(ok=True, operation=operation, calls=self.calls)

    def _failure(self, operation: str, message: str) -> FirewallHarnessResult:
        return FirewallHarnessResult(ok=False, operation=operation, calls=self.calls, failure=FirewallHarnessFailure(operation=operation, message=message))

    def plan(self) -> FirewallHarnessResult:
        result = self._record("plan")
        if self._fail_plan:
            return self._failure("plan", "injected plan failure")
        return result

    def apply(self) -> FirewallHarnessResult:
        result = self._record("apply")
        if self._fail_apply:
            return self._failure("apply", "injected apply failure")
        return result

    def verify(self) -> FirewallHarnessResult:
        result = self._record("verify")
        if self._fail_verify:
            return self._failure("verify", "injected verify failure")
        return result

    def rollback(self) -> FirewallHarnessResult:
        result = self._record("rollback")
        if self._fail_rollback:
            return self._failure("rollback", "injected rollback failure")
        return result
