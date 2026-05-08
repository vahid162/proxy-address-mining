from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class HealthStatus(StrEnum):
    OK = "OK"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class HealthCheck:
    """Stable health/doctor check shape for CLI, API, UI, and Telegram."""

    key: str
    status: HealthStatus
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    remediation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class HealthReport:
    """Stable health/doctor report shape shared by current and future doctors."""

    component: str
    final_verdict: HealthStatus
    checks: list[HealthCheck]

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "final_verdict": self.final_verdict.value,
            "checks": [check.to_dict() for check in self.checks],
        }


def worst_status(checks: list[HealthCheck]) -> HealthStatus:
    if any(check.status == HealthStatus.CRITICAL for check in checks):
        return HealthStatus.CRITICAL
    if any(check.status == HealthStatus.WARN for check in checks):
        return HealthStatus.WARN
    return HealthStatus.OK
