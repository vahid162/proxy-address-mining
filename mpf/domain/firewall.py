from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class FirewallChainIntent:
    id: str
    table: str
    chain: str
    owner: str
    purpose: str
    lane: str | None = None
    customer_key: str | None = None
    customer_port: int | None = None
    required: bool = True
    group: str = "default"
    order: int = 0


@dataclass(frozen=True)
class FirewallRuleIntent:
    id: str
    table: str
    chain: str
    rule_key: str
    rule_kind: str
    priority: int
    match_json: dict[str, Any] = field(default_factory=dict)
    action_json: dict[str, Any] = field(default_factory=dict)
    lane: str | None = None
    customer_key: str | None = None
    customer_id: int | None = None
    customer_port: int | None = None
    backend_port: int | None = None
    accounting_role: str | None = None
    safety_role: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class FirewallLiveRuleSnapshot:
    rule_key: str
    table: str
    chain: str
    rule_kind: str | None = None
    match_json: dict[str, Any] = field(default_factory=dict)
    action_json: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FirewallLiveSnapshot:
    chains: list[tuple[str, str]] = field(default_factory=list)
    rules: list[FirewallLiveRuleSnapshot] = field(default_factory=list)


@dataclass(frozen=True)
class FirewallPlanMessage:
    code: str
    message: str
    severity: str


@dataclass(frozen=True)
class FirewallPlanChange:
    kind: str
    object_type: str
    object_id: str
    detail: str


@dataclass
class FirewallPlanResult:
    backend: str = "iptables"
    apply_mode: str = "plan_only"
    tables: list[str] = field(default_factory=lambda: ["filter", "nat"])
    chains: list[FirewallChainIntent] = field(default_factory=list)
    rules: list[FirewallRuleIntent] = field(default_factory=list)
    lane_backend_coverage: list[str] = field(default_factory=list)
    customer_coverage: list[str] = field(default_factory=list)
    customer_policy_references: list[str] = field(default_factory=list)
    accounting_coverage: dict[str, bool] = field(default_factory=dict)
    backend_guard_intent: dict[str, Any] = field(default_factory=lambda: {
        "internal_backend_reachable": "OK",
        "external_backend_exposed": "NO",
        "preserve_loopback": True,
        "preserve_docker_internal_paths": True,
    })
    changes: list[FirewallPlanChange] = field(default_factory=list)
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)
    affected_customers: list[str] = field(default_factory=list)
    applyable: bool = True
    firewall_change: str = "planned_only"
    nat_change: str = "planned_only"
    runtime_change: str = "no"
    planner_customer_source: str = "unknown"
    db_customer_input_loaded: bool = False

    def finalize(self) -> None:
        self.applyable = len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["chains"] = [asdict(x) for x in self.chains]
        data["rules"] = [asdict(x) for x in self.rules]
        data["changes"] = [asdict(x) for x in self.changes]
        data["warnings"] = [asdict(x) for x in self.warnings]
        data["errors"] = [asdict(x) for x in self.errors]
        return data

    def to_human(self) -> str:
        lines = [
            "MPF firewall planner (dry-run)",
            f"backend: {self.backend}",
            f"apply_mode: {self.apply_mode}",
            f"applyable: {str(self.applyable).lower()}",
            f"firewall_change: {self.firewall_change}",
            f"nat_change: {self.nat_change}",
            f"runtime_change: {self.runtime_change}",
            f"planner_customer_source: {self.planner_customer_source}",
            f"db_customer_input_loaded: {str(self.db_customer_input_loaded).lower()}",
            f"chains: {len(self.chains)}",
            f"rules: {len(self.rules)}",
            f"changes: {len(self.changes)}",
            f"warnings: {len(self.warnings)}",
            f"errors: {len(self.errors)}",
        ]
        for warning in self.warnings:
            lines.append(f"WARNING [{warning.code}] {warning.message}")
        for error in self.errors:
            lines.append(f"ERROR [{error.code}] {error.message}")
        return "\n".join(lines)
