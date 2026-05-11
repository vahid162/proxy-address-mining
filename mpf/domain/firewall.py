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
    raw_line: str | None = None
    match_json: dict[str, Any] = field(default_factory=dict)
    action_json: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FirewallLiveSnapshot:
    chains: list[tuple[str, str]] = field(default_factory=list)
    rules: list[FirewallLiveRuleSnapshot] = field(default_factory=list)
    source_snapshot_sha256: str | None = None


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


@dataclass(frozen=True)
class FirewallRestoreRule:
    table: str
    chain: str
    rule_key: str
    line: str
    planned_only: bool = False


@dataclass(frozen=True)
class FirewallRestoreChain:
    table: str
    chain: str
    policy: str = "-"


@dataclass
class FirewallRestoreTable:
    name: str
    chains: list[FirewallRestoreChain] = field(default_factory=list)
    rules: list[FirewallRestoreRule] = field(default_factory=list)


@dataclass(frozen=True)
class FirewallRestoreValidationResult:
    renderable: bool
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)


@dataclass
class FirewallRestorePayload:
    payload: str
    payload_sha256: str
    payload_line_count: int
    tables: list[FirewallRestoreTable] = field(default_factory=list)


@dataclass
class FirewallApplyContract:
    backend: str = "iptables"
    apply_mode: str = "plan_only"
    artifact_only: bool = True
    live_apply_allowed: bool = False
    iptables_restore_allowed: bool = False
    source_plan_version: str = "phase6-b1"
    renderable: bool = False
    applyable: bool = False
    required_tables: list[str] = field(default_factory=lambda: ["filter", "nat"])
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)
    safety_flags: dict[str, Any] = field(default_factory=lambda: {
        "live_firewall_read": False,
        "live_firewall_write": False,
        "iptables_save_executed": False,
        "iptables_restore_executed": False,
        "runtime_change": "no",
        "nat_change": "planned_only",
        "firewall_change": "planned_only",
    })
    restore_payload: FirewallRestorePayload | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FirewallRestorePointContract:
    artifact_only: bool = True
    required_before_apply: bool = True
    restore_point_required: bool = True
    live_snapshot_required_before_apply: bool = True
    desired_payload_hash: str | None = None
    source_plan_version: str = "phase6-b2"
    created_by_phase: str = "phase6-b2"
    storage_policy: str = "planned_only"
    filesystem_write_allowed: bool = False
    database_write_allowed: bool = False
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)


@dataclass
class FirewallLockContract:
    firewall_lock_path: str = "/run/mpf-firewall.lock"
    database_scheduler_lock_required: bool = True
    lock_required_for_apply: bool = True
    lock_required_for_rollback: bool = True
    lock_acquire_allowed_now: bool = False
    lock_release_allowed_now: bool = False
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)


@dataclass
class FirewallVerifyContract:
    verify_required_after_apply: bool = True
    verify_mode: str = "offline_contract_only"
    live_verify_allowed_now: bool = False
    compare_desired_to_live_required_later: bool = True
    backend_exposure_check_required: bool = True
    nat_target_check_required: bool = True
    accounting_coverage_check_required: bool = True
    rule_chain_consistency_check_required: bool = True
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)


@dataclass
class FirewallRollbackContract:
    rollback_required_for_apply: bool = True
    rollback_artifact_required: bool = True
    rollback_execution_allowed_now: bool = False
    rollback_must_use_stored_restore_artifact: bool = True
    rollback_must_not_guess_from_current_db: bool = True
    rollback_verify_required_later: bool = True
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)


@dataclass
class FirewallRollbackPayload:
    payload: str
    payload_sha256: str
    payload_line_count: int
    source_snapshot_sha256: str
    table_count: int
    chain_count: int
    rule_count: int


@dataclass(frozen=True)
class FirewallRollbackValidationResult:
    renderable: bool
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)


@dataclass
class FirewallRollbackArtifactContract:
    backend: str = "iptables"
    artifact_only: bool = True
    inspection_only: bool = True
    rollback_execution_allowed_now: bool = False
    live_apply_allowed: bool = False
    iptables_save_allowed_now: bool = False
    iptables_restore_allowed_now: bool = False
    source: str = "none"
    source_snapshot_hash: str | None = None
    rollback_payload_sha256: str | None = None
    rollback_payload_line_count: int = 0
    renderable: bool = False
    applyable: bool = False
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)
    safety_flags: dict[str, Any] = field(default_factory=lambda: {
        "live_firewall_read": False,
        "live_firewall_write": False,
        "iptables_save_executed": False,
        "iptables_restore_executed": False,
        "lock_acquired": False,
        "restore_point_written": False,
        "rollback_written": False,
        "database_write": False,
        "filesystem_write": False,
        "runtime_change": "no",
        "nat_change": "planned_only",
        "firewall_change": "planned_only",
    })
    rollback_payload: FirewallRollbackPayload | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FirewallApplyReadinessContract:
    backend: str = "iptables"
    apply_mode: str = "plan_only"
    artifact_only: bool = True
    live_apply_allowed: bool = False
    iptables_save_allowed_now: bool = False
    iptables_restore_allowed_now: bool = False
    restore_point_contract: FirewallRestorePointContract = field(default_factory=FirewallRestorePointContract)
    lock_contract: FirewallLockContract = field(default_factory=FirewallLockContract)
    verify_contract: FirewallVerifyContract = field(default_factory=FirewallVerifyContract)
    rollback_contract: FirewallRollbackContract = field(default_factory=FirewallRollbackContract)
    source_restore_payload_contract: FirewallApplyContract | None = None
    readiness: str = "blocked_for_live_apply"
    renderable: bool = False
    applyable: bool = False
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)
    safety_flags: dict[str, Any] = field(default_factory=lambda: {
        "live_firewall_read": False,
        "live_firewall_write": False,
        "iptables_save_executed": False,
        "iptables_restore_executed": False,
        "lock_acquired": False,
        "restore_point_written": False,
        "database_write": False,
        "filesystem_write": False,
        "runtime_change": "no",
        "nat_change": "planned_only",
        "firewall_change": "planned_only",
    })

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FirewallApplyPackageReport:
    backend: str = "iptables"
    apply_mode: str = "plan_only"
    package_version: str = "phase6-b3"
    artifact_only: bool = True
    inspection_only: bool = True
    live_apply_allowed: bool = False
    applyable: bool = False
    readiness: str = "blocked_for_live_apply"
    planner_customer_source: str = "unknown"
    db_customer_input_loaded: bool = False
    plan_summary: dict[str, Any] = field(default_factory=dict)
    restore_payload_summary: dict[str, Any] = field(default_factory=dict)
    apply_contract_summary: dict[str, Any] = field(default_factory=dict)
    payload_sha256: str | None = None
    payload_line_count: int = 0
    chain_count: int = 0
    rule_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)
    safety_flags: dict[str, Any] = field(default_factory=lambda: {
        "live_firewall_read": False,
        "live_firewall_write": False,
        "iptables_save_executed": False,
        "iptables_restore_executed": False,
        "lock_acquired": False,
        "restore_point_written": False,
        "database_write": False,
        "filesystem_write": False,
        "runtime_change": "no",
        "nat_change": "planned_only",
        "firewall_change": "planned_only",
    })
    source_plan: FirewallPlanResult | None = None
    restore_contract: FirewallApplyContract | None = None
    apply_readiness_contract: FirewallApplyReadinessContract | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirewallPreflightCheck:
    key: str
    status: str
    message: str
    blocking: bool = False
    evidence: str = ""
    remediation: str = ""


@dataclass
class FirewallPreflightReport:
    backend: str = "iptables"
    apply_mode: str = "plan_only"
    preflight_version: str = "phase6-b5"
    artifact_only: bool = True
    inspection_only: bool = True
    live_apply_allowed: bool = False
    applyable: bool = False
    readiness: str = "blocked_for_live_apply"
    final_verdict: str = "BLOCKED"
    planner_customer_source: str = "unknown"
    db_customer_input_loaded: bool = False
    restore_payload_present: bool = False
    restore_payload_renderable: bool = False
    apply_contract_present: bool = False
    apply_contract_readiness: str = "blocked_for_live_apply"
    package_present: bool = False
    rollback_artifact_present: bool = False
    rollback_artifact_renderable: bool = False
    rollback_snapshot_required_later: bool = True
    restore_point_required: bool = True
    lock_required_for_apply: bool = True
    verify_required_after_apply: bool = True
    rollback_artifact_required: bool = True
    check_count: int = 0
    ok_count: int = 0
    warn_count: int = 0
    blocked_count: int = 0
    checks: list[FirewallPreflightCheck] = field(default_factory=list)
    warnings: list[FirewallPlanMessage] = field(default_factory=list)
    errors: list[FirewallPlanMessage] = field(default_factory=list)
    safety_flags: dict[str, Any] = field(default_factory=lambda: {
        "live_firewall_read": False,
        "live_firewall_write": False,
        "iptables_save_executed": False,
        "iptables_restore_executed": False,
        "lock_acquired": False,
        "restore_point_written": False,
        "rollback_written": False,
        "database_write": False,
        "filesystem_write": False,
        "runtime_change": "no",
        "nat_change": "planned_only",
        "firewall_change": "planned_only",
    })

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
