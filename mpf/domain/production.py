from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_network

from mpf.domain.customer_lifecycle import DomainValidationError, validate_customer_key

ALLOWED_IPS_MODE = {"any", "whitelist"}


@dataclass(slots=True)
class CanaryPlanRequest:
    customer_key: str | None
    lane: str = "btc"
    port: int | None = None
    name: str | None = None
    miners: int = 1
    farms: int = 1
    maxconn: int = 1
    rate_per_min: int = 120
    burst: int = 240
    ips_mode: str = "any"
    ip_whitelist: list[str] = field(default_factory=list)
    operator: str | None = None
    reason: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        try:
            validate_customer_key(self.customer_key)
        except DomainValidationError as exc:
            errors.append(str(exc))

        if not self.lane.strip():
            errors.append("lane must be non-empty")
        if self.port is not None and not (1 <= self.port <= 65535):
            errors.append("port must be TCP 1..65535")

        for key in ("miners", "farms", "maxconn", "rate_per_min", "burst"):
            value = getattr(self, key)
            if value <= 0:
                errors.append(f"{key} must be positive")

        if self.maxconn < self.miners:
            errors.append("maxconn must be >= miners")

        if self.ips_mode not in ALLOWED_IPS_MODE:
            errors.append("ips_mode must be any or whitelist")
        if self.ips_mode == "any" and self.ip_whitelist:
            errors.append("ip_whitelist must be empty when ips_mode=any")
        for cidr in self.ip_whitelist:
            try:
                ip_network(cidr, strict=False)
            except ValueError:
                errors.append(f"invalid IP/CIDR: {cidr}")

        if self.name is not None and not self.name.strip():
            errors.append("name must be non-empty when provided")
        if self.operator is not None and not self.operator.strip():
            errors.append("operator must be non-empty when provided")
        if self.reason is not None and not self.reason.strip():
            errors.append("reason must be non-empty when provided")

        return errors


ALLOWED_CONTROLLED_HARNESS_ACTIONS = {"preflight", "package", "apply"}


@dataclass(slots=True)
class ControlledActivationHarnessRequest:
    customer_key: str | None = "canary-btc-001"
    lane: str = "btc"
    port: int | None = 20001
    name: str | None = "Phase 11 controlled canary"
    miners: int = 1
    farms: int = 1
    maxconn: int = 1
    rate_per_min: int = 120
    burst: int = 240
    ips_mode: str = "any"
    ip_whitelist: list[str] = field(default_factory=list)
    operator: str | None = None
    reason: str | None = None
    requested_action: str = "preflight"
    dry_run: bool = True
    require_operator_confirmation: bool = True

    def validate(self) -> list[str]:
        errors = CanaryPlanRequest(
            customer_key=self.customer_key,
            lane=self.lane,
            port=self.port,
            name=self.name,
            miners=self.miners,
            farms=self.farms,
            maxconn=self.maxconn,
            rate_per_min=self.rate_per_min,
            burst=self.burst,
            ips_mode=self.ips_mode,
            ip_whitelist=self.ip_whitelist,
            operator=self.operator,
            reason=self.reason,
        ).validate()

        if self.requested_action not in ALLOWED_CONTROLLED_HARNESS_ACTIONS:
            errors.append("requested_action must be preflight, package, or apply")
        if not self.require_operator_confirmation:
            errors.append("operator confirmation remains required before any controlled activation step")

        return errors


ALLOWED_MANUAL_CANARY_ACCEPTANCE_ACTIONS = {"package", "accept", "execute"}


@dataclass(slots=True)
class ManualCanaryAcceptanceRequest:
    customer_key: str | None = "canary-btc-001"
    lane: str = "btc"
    port: int | None = 20001
    name: str | None = "Phase 11 manual canary"
    miners: int = 1
    farms: int = 1
    maxconn: int = 1
    rate_per_min: int = 120
    burst: int = 240
    ips_mode: str = "any"
    ip_whitelist: list[str] = field(default_factory=list)
    operator: str | None = None
    reason: str | None = None
    requested_action: str = "package"
    require_operator_confirmation: bool = True
    require_farm5_phase11c_evidence: bool = True
    require_backup_reference: bool = True
    require_restore_plan_reference: bool = True
    require_rollback_plan: bool = True
    require_no_customer_nat_baseline: bool = True
    require_no_customer_firewall_baseline: bool = True
    require_local_only_runtime_baseline: bool = True

    def validate(self) -> list[str]:
        errors = CanaryPlanRequest(
            customer_key=self.customer_key,
            lane=self.lane,
            port=self.port,
            name=self.name,
            miners=self.miners,
            farms=self.farms,
            maxconn=self.maxconn,
            rate_per_min=self.rate_per_min,
            burst=self.burst,
            ips_mode=self.ips_mode,
            ip_whitelist=self.ip_whitelist,
            operator=self.operator,
            reason=self.reason,
        ).validate()

        if self.requested_action not in ALLOWED_MANUAL_CANARY_ACCEPTANCE_ACTIONS:
            errors.append("requested_action must be package, accept, or execute")
        if self.requested_action in {"accept", "execute"}:
            errors.append("requested_action accept/execute is blocked until a later explicit Phase 11D execution gate")
        if not self.require_operator_confirmation:
            errors.append("operator confirmation remains required before any future execution")

        required_fields = (
            "require_farm5_phase11c_evidence",
            "require_backup_reference",
            "require_restore_plan_reference",
            "require_rollback_plan",
            "require_no_customer_nat_baseline",
            "require_no_customer_firewall_baseline",
            "require_local_only_runtime_baseline",
        )
        for field_name in required_fields:
            if not getattr(self, field_name):
                errors.append(f"{field_name} must stay true in Phase 11D package")

        return errors

    def as_dict(self) -> dict[str, object]:
        return {
            "customer_key": self.customer_key,
            "lane": self.lane,
            "port": self.port,
            "name": self.name,
            "miners": self.miners,
            "farms": self.farms,
            "maxconn": self.maxconn,
            "rate_per_min": self.rate_per_min,
            "burst": self.burst,
            "ips_mode": self.ips_mode,
            "ip_whitelist": self.ip_whitelist,
            "operator": self.operator,
            "reason": self.reason,
            "requested_action": self.requested_action,
            "require_operator_confirmation": self.require_operator_confirmation,
            "require_farm5_phase11c_evidence": self.require_farm5_phase11c_evidence,
            "require_backup_reference": self.require_backup_reference,
            "require_restore_plan_reference": self.require_restore_plan_reference,
            "require_rollback_plan": self.require_rollback_plan,
            "require_no_customer_nat_baseline": self.require_no_customer_nat_baseline,
            "require_no_customer_firewall_baseline": self.require_no_customer_firewall_baseline,
            "require_local_only_runtime_baseline": self.require_local_only_runtime_baseline,
        }


ALLOWED_MANUAL_CANARY_EXECUTION_GATE_ACTIONS = {"gate", "execute"}


@dataclass(slots=True)
class ManualCanaryExecutionGateRequest:
    customer_key: str | None = "canary-btc-001"
    lane: str = "btc"
    port: int | None = 20001
    name: str | None = "Phase 11 manual canary execution"
    miners: int = 1
    farms: int = 1
    maxconn: int = 1
    rate_per_min: int = 120
    burst: int = 240
    ips_mode: str = "any"
    ip_whitelist: list[str] = field(default_factory=list)
    operator: str | None = None
    reason: str | None = None
    requested_action: str = "gate"
    require_operator_confirmation: bool = True
    require_farm5_0_1_147_evidence: bool = True
    require_phase11d_package_evidence: bool = True
    require_latest_main_sync_before_execution: bool = True
    require_backup_reference: bool = True
    require_restore_plan_reference: bool = True
    require_rollback_plan: bool = True
    require_no_customer_nat_baseline: bool = True
    require_no_customer_firewall_baseline: bool = True
    require_local_only_runtime_baseline: bool = True
    require_firewall_plan_review: bool = True
    require_abuse_coverage_check: bool = True
    require_usage_visibility_check: bool = True
    require_reject_visibility_check: bool = True
    require_session_worker_visibility_check: bool = True
    require_check_report_verdict: bool = True

    def validate(self) -> list[str]:
        errors = CanaryPlanRequest(customer_key=self.customer_key,lane=self.lane,port=self.port,name=self.name,miners=self.miners,farms=self.farms,maxconn=self.maxconn,rate_per_min=self.rate_per_min,burst=self.burst,ips_mode=self.ips_mode,ip_whitelist=self.ip_whitelist,operator=self.operator,reason=self.reason).validate()
        if self.requested_action not in ALLOWED_MANUAL_CANARY_EXECUTION_GATE_ACTIONS:
            errors.append("requested_action must be gate or execute")
        if self.requested_action == "execute":
            errors.append("requested_action execute is blocked in this PR")
        if not self.require_operator_confirmation:
            errors.append("require_operator_confirmation must stay true")
        if self.lane != "btc":
            errors.append("lane must be btc for Phase 11D explicit canary gate")
        if self.port is None or not (20000 <= self.port <= 20999):
            errors.append("port must be a safe canary port in range 20000..20999")
        if self.miners < 1 or self.farms < 1 or self.maxconn < 1:
            errors.append("miners/farms/maxconn must be >= 1")
        if self.maxconn > self.miners and not (self.reason and self.reason.strip()):
            errors.append("maxconn greater than miners requires a clear reason")
        if self.ips_mode not in ALLOWED_IPS_MODE:
            errors.append("ips_mode must be any or whitelist")
        if self.ips_mode == "whitelist" and not self.ip_whitelist:
            errors.append("ip_whitelist must be non-empty when ips_mode=whitelist")
        for name in ("require_farm5_0_1_147_evidence","require_phase11d_package_evidence","require_latest_main_sync_before_execution","require_backup_reference","require_restore_plan_reference","require_rollback_plan","require_no_customer_nat_baseline","require_no_customer_firewall_baseline","require_local_only_runtime_baseline","require_firewall_plan_review","require_abuse_coverage_check","require_usage_visibility_check","require_reject_visibility_check","require_session_worker_visibility_check","require_check_report_verdict"):
            if not getattr(self, name):
                errors.append(f"{name} must stay true")
        return errors

    def as_dict(self) -> dict[str, object]:
        return {k: getattr(self, k) for k in (
            "customer_key","lane","port","name","miners","farms","maxconn","rate_per_min","burst","ips_mode","ip_whitelist","operator","reason","requested_action","require_operator_confirmation","require_farm5_0_1_147_evidence","require_phase11d_package_evidence","require_latest_main_sync_before_execution","require_backup_reference","require_restore_plan_reference","require_rollback_plan","require_no_customer_nat_baseline","require_no_customer_firewall_baseline","require_local_only_runtime_baseline","require_firewall_plan_review","require_abuse_coverage_check","require_usage_visibility_check","require_reject_visibility_check","require_session_worker_visibility_check","require_check_report_verdict",
        )}


ALLOWED_MANUAL_CANARY_EXECUTION_RUN_PREPARATION_ACTIONS = {"prepare", "execute"}


@dataclass(slots=True)
class ManualCanaryExecutionRunPreparationRequest:
    customer_key: str | None = "canary-btc-001"
    lane: str = "btc"
    port: int | None = 20001
    name: str | None = "Phase 11 manual canary execution run"
    miners: int = 1
    farms: int = 1
    maxconn: int = 1
    rate_per_min: int = 120
    burst: int = 240
    ips_mode: str = "any"
    ip_whitelist: list[str] = field(default_factory=list)
    operator: str | None = None
    reason: str | None = None
    requested_action: str = "prepare"
    require_operator_confirmation: bool = True
    require_farm5_0_1_149_evidence: bool = True
    require_execution_gate_evidence: bool = True
    require_latest_main_sync_before_execution: bool = True
    require_phase_gate_pass: bool = True
    require_mpf_doctor_ok: bool = True
    require_db_status_ok: bool = True
    require_proxy_doctor_ok: bool = True
    require_no_customer_nat_baseline: bool = True
    require_no_customer_firewall_baseline: bool = True
    require_local_only_runtime_baseline: bool = True
    require_firewall_plan_review: bool = True
    require_firewall_diff_review: bool = True
    require_restore_point_before_apply: bool = True
    require_iptables_save_backup_before_apply: bool = True
    require_lock_before_apply: bool = True
    require_verify_after_apply: bool = True
    require_rollback_plan: bool = True
    require_usage_visibility_check: bool = True
    require_reject_visibility_check: bool = True
    require_session_worker_visibility_check: bool = True
    require_abuse_1h_coverage_check: bool = True
    require_conntrack_scope_review: bool = True
    require_post_execution_evidence_collection: bool = True

    def validate(self) -> list[str]:
        errors = CanaryPlanRequest(customer_key=self.customer_key,lane=self.lane,port=self.port,name=self.name,miners=self.miners,farms=self.farms,maxconn=self.maxconn,rate_per_min=self.rate_per_min,burst=self.burst,ips_mode=self.ips_mode,ip_whitelist=self.ip_whitelist,operator=self.operator,reason=self.reason).validate()
        if self.requested_action not in ALLOWED_MANUAL_CANARY_EXECUTION_RUN_PREPARATION_ACTIONS:
            errors.append("requested_action must be prepare or execute")
        if self.requested_action == "execute":
            errors.append("requested_action execute is blocked in this PR")
        if not self.require_operator_confirmation:
            errors.append("require_operator_confirmation must stay true")
        if self.lane != "btc":
            errors.append("lane must be btc for this manual canary preparation")
        if self.port is None or not (20000 <= self.port <= 20999):
            errors.append("port must be a safe canary port in range 20000..20999")
        if self.miners < 1 or self.farms < 1 or self.maxconn < 1:
            errors.append("miners/farms/maxconn must be >= 1")
        if self.maxconn > self.miners and not (self.reason and self.reason.strip()):
            errors.append("maxconn greater than miners requires a clear reason")
        if self.ips_mode not in ALLOWED_IPS_MODE:
            errors.append("ips_mode must be any or whitelist")
        if self.ips_mode == "whitelist" and not self.ip_whitelist:
            errors.append("ip_whitelist must be non-empty when ips_mode=whitelist")
        for name in ("require_farm5_0_1_149_evidence","require_execution_gate_evidence","require_latest_main_sync_before_execution","require_phase_gate_pass","require_mpf_doctor_ok","require_db_status_ok","require_proxy_doctor_ok","require_no_customer_nat_baseline","require_no_customer_firewall_baseline","require_local_only_runtime_baseline","require_firewall_plan_review","require_firewall_diff_review","require_restore_point_before_apply","require_iptables_save_backup_before_apply","require_lock_before_apply","require_verify_after_apply","require_rollback_plan","require_usage_visibility_check","require_reject_visibility_check","require_session_worker_visibility_check","require_abuse_1h_coverage_check","require_conntrack_scope_review","require_post_execution_evidence_collection"):
            if not getattr(self, name):
                errors.append(f"{name} must stay true")
        return errors

    def as_dict(self) -> dict[str, object]:
        return {k: getattr(self, k) for k in (
            "customer_key","lane","port","name","miners","farms","maxconn","rate_per_min","burst","ips_mode","ip_whitelist","operator","reason","requested_action","require_operator_confirmation","require_farm5_0_1_149_evidence","require_execution_gate_evidence","require_latest_main_sync_before_execution","require_phase_gate_pass","require_mpf_doctor_ok","require_db_status_ok","require_proxy_doctor_ok","require_no_customer_nat_baseline","require_no_customer_firewall_baseline","require_local_only_runtime_baseline","require_firewall_plan_review","require_firewall_diff_review","require_restore_point_before_apply","require_iptables_save_backup_before_apply","require_lock_before_apply","require_verify_after_apply","require_rollback_plan","require_usage_visibility_check","require_reject_visibility_check","require_session_worker_visibility_check","require_abuse_1h_coverage_check","require_conntrack_scope_review","require_post_execution_evidence_collection",
        )}


ALLOWED_MANUAL_CANARY_EXECUTION_RUN_ACTIONS = {"plan", "execute"}


@dataclass(slots=True)
class ManualCanaryExecutionRunRequest:
    customer_key: str | None = "canary-btc-001"
    lane: str = "btc"
    port: int | None = 20001
    name: str | None = "Phase 11 manual canary execution"
    miners: int = 1
    farms: int = 1
    maxconn: int = 1
    rate_per_min: int = 120
    burst: int = 240
    ips_mode: str = "any"
    ip_whitelist: list[str] = field(default_factory=list)
    operator: str | None = None
    reason: str | None = None
    requested_action: str = "plan"
    expected_version: str | None = None
    operator_confirmed: bool = False
    understand_canary_customer: bool = False
    understand_firewall_apply: bool = False
    reviewed_rollback: bool = False
    fresh_farm5_sync_confirmed: bool = False
    require_farm5_0_1_151_evidence: bool = True
    require_run_preparation_evidence: bool = True
    require_latest_main_sync_before_execution: bool = True
    require_phase_gate_pass: bool = True
    require_mpf_doctor_ok: bool = True
    require_db_status_ok: bool = True
    require_proxy_doctor_ok: bool = True
    require_no_customer_nat_baseline: bool = True
    require_no_customer_firewall_baseline: bool = True
    require_local_only_runtime_baseline: bool = True
    require_firewall_plan_review: bool = True
    require_firewall_diff_review: bool = True
    require_restore_point_before_apply: bool = True
    require_iptables_save_backup_before_apply: bool = True
    require_lock_before_apply: bool = True
    require_verify_after_apply: bool = True
    require_rollback_plan: bool = True
    require_usage_visibility_check: bool = True
    require_reject_visibility_check: bool = True
    require_session_worker_visibility_check: bool = True
    require_abuse_1h_coverage_check: bool = True
    require_conntrack_scope_review: bool = True
    require_post_execution_evidence_collection: bool = True

    def validate(self, expected_repo_version: str | None = None) -> list[str]:
        errors = CanaryPlanRequest(customer_key=self.customer_key,lane=self.lane,port=self.port,name=self.name,miners=self.miners,farms=self.farms,maxconn=self.maxconn,rate_per_min=self.rate_per_min,burst=self.burst,ips_mode=self.ips_mode,ip_whitelist=self.ip_whitelist,operator=self.operator,reason=self.reason).validate()
        if self.requested_action not in ALLOWED_MANUAL_CANARY_EXECUTION_RUN_ACTIONS:
            errors.append("requested_action must be plan or execute")
        if self.lane != "btc":
            errors.append("lane must be btc for first real canary")
        if self.port != 20001:
            errors.append("port must be 20001 for first real canary")
        if self.customer_key != "canary-btc-001":
            errors.append("customer_key must be canary-btc-001 for first real canary")
        if self.miners < 1 or self.farms < 1 or self.maxconn < 1:
            errors.append("miners/farms/maxconn must be >= 1")
        if self.maxconn > self.miners and not (self.reason and self.reason.strip()):
            errors.append("maxconn greater than miners requires a clear reason")
        if self.ips_mode not in ALLOWED_IPS_MODE:
            errors.append("ips_mode must be any or whitelist")
        if self.ips_mode == "whitelist" and not self.ip_whitelist:
            errors.append("ip_whitelist must be non-empty when ips_mode=whitelist")
        reqs=("require_farm5_0_1_151_evidence","require_run_preparation_evidence","require_latest_main_sync_before_execution","require_phase_gate_pass","require_mpf_doctor_ok","require_db_status_ok","require_proxy_doctor_ok","require_no_customer_nat_baseline","require_no_customer_firewall_baseline","require_local_only_runtime_baseline","require_firewall_plan_review","require_firewall_diff_review","require_restore_point_before_apply","require_iptables_save_backup_before_apply","require_lock_before_apply","require_verify_after_apply","require_rollback_plan","require_usage_visibility_check","require_reject_visibility_check","require_session_worker_visibility_check","require_abuse_1h_coverage_check","require_conntrack_scope_review","require_post_execution_evidence_collection")
        for name in reqs:
            if not getattr(self,name):
                errors.append(f"{name} must stay true")
        if self.requested_action=="execute":
            if not self.operator_confirmed: errors.append("operator_confirmed must be true for execute")
            if not self.understand_canary_customer: errors.append("understand_canary_customer must be true for execute")
            if not self.understand_firewall_apply: errors.append("understand_firewall_apply must be true for execute")
            if not self.reviewed_rollback: errors.append("reviewed_rollback must be true for execute")
            if not self.fresh_farm5_sync_confirmed: errors.append("fresh_farm5_sync_confirmed must be true for execute")
            if not expected_repo_version:
                errors.append("expected_repo_version is required for execute validation")
            elif self.expected_version != expected_repo_version: errors.append(f"expected_version must be {expected_repo_version} for execute")
        return errors

    def as_dict(self) -> dict[str, object]:
        return {k: getattr(self, k) for k in (
            "customer_key","lane","port","name","miners","farms","maxconn","rate_per_min","burst","ips_mode","ip_whitelist","operator","reason","requested_action","expected_version","operator_confirmed","understand_canary_customer","understand_firewall_apply","reviewed_rollback","fresh_farm5_sync_confirmed","require_farm5_0_1_151_evidence","require_run_preparation_evidence","require_latest_main_sync_before_execution","require_phase_gate_pass","require_mpf_doctor_ok","require_db_status_ok","require_proxy_doctor_ok","require_no_customer_nat_baseline","require_no_customer_firewall_baseline","require_local_only_runtime_baseline","require_firewall_plan_review","require_firewall_diff_review","require_restore_point_before_apply","require_iptables_save_backup_before_apply","require_lock_before_apply","require_verify_after_apply","require_rollback_plan","require_usage_visibility_check","require_reject_visibility_check","require_session_worker_visibility_check","require_abuse_1h_coverage_check","require_conntrack_scope_review","require_post_execution_evidence_collection",
        )}
