from __future__ import annotations

from mpf.domain.firewall import (
    FirewallApplyContract,
    FirewallApplyPackageReport,
    FirewallApplyReadinessContract,
    FirewallPlanMessage,
    FirewallPlanResult,
    FirewallPreflightCheck,
    FirewallPreflightReport,
    FirewallRollbackArtifactContract,
)
from mpf.services.firewall_apply_contract_service import build_apply_readiness_contract
from mpf.services.firewall_apply_package_service import build_apply_package_report
from mpf.services.firewall_restore_payload_renderer import render_restore_contract


def _add(checks: list[FirewallPreflightCheck], key: str, status: str, message: str, blocking: bool = False, evidence: str = "", remediation: str = "") -> None:
    checks.append(FirewallPreflightCheck(key=key, status=status, message=message, blocking=blocking, evidence=evidence, remediation=remediation))


def _dedupe_messages(messages: list[FirewallPlanMessage]) -> list[FirewallPlanMessage]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[FirewallPlanMessage] = []
    for msg in messages:
        key = (msg.severity, msg.code, msg.message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(msg)
    return deduped


def build_preflight_report(
    plan: FirewallPlanResult,
    restore_contract: FirewallApplyContract | None = None,
    apply_readiness_contract: FirewallApplyReadinessContract | None = None,
    package_report: FirewallApplyPackageReport | None = None,
    rollback_artifact: FirewallRollbackArtifactContract | None = None,
) -> FirewallPreflightReport:
    restore = restore_contract or render_restore_contract(plan)
    readiness = apply_readiness_contract or build_apply_readiness_contract(plan, restore)
    package = package_report or build_apply_package_report(plan, restore, readiness)

    warnings: list[FirewallPlanMessage] = []
    errors: list[FirewallPlanMessage] = []
    warnings.extend(plan.warnings)
    warnings.extend(restore.warnings)
    warnings.extend(readiness.warnings)
    warnings.extend(package.warnings)
    errors.extend(plan.errors)
    errors.extend(restore.errors)
    errors.extend(readiness.errors)
    errors.extend(package.errors)

    warnings = _dedupe_messages(warnings)
    errors = _dedupe_messages(errors)

    checks: list[FirewallPreflightCheck] = []
    _add(checks, "phase_gate_plan_only", "OK" if plan.apply_mode == "plan_only" else "BLOCKED", f"apply_mode={plan.apply_mode}", blocking=plan.apply_mode != "plan_only")
    _add(checks, "live_apply_forbidden_current_phase", "BLOCKED", "live apply remains forbidden in current phase", blocking=True)
    _add(checks, "planner_result_loaded", "OK", "planner result loaded", evidence=f"chains={len(plan.chains)} rules={len(plan.rules)}")
    _add(checks, "planner_source_explicit", "OK" if plan.planner_customer_source == "db_readonly" else "WARN", f"planner_customer_source={plan.planner_customer_source}")
    _add(checks, "restore_payload_renderable", "OK" if restore.renderable else "BLOCKED", f"renderable={restore.renderable}", blocking=not restore.renderable)
    _add(checks, "apply_contract_present", "OK", "apply contract present")
    _add(checks, "apply_contract_applyable_false", "OK" if not readiness.applyable else "BLOCKED", f"applyable={readiness.applyable}", blocking=readiness.applyable)
    _add(checks, "package_present", "OK", "apply package present")
    _add(checks, "package_applyable_false", "OK" if not package.applyable else "BLOCKED", f"applyable={package.applyable}", blocking=package.applyable)
    if rollback_artifact is None:
        _add(checks, "rollback_artifact_present_if_snapshot_given", "WARN", "rollback artifact not provided (no explicit snapshot input)")
    else:
        _add(checks, "rollback_artifact_present_if_snapshot_given", "OK", "rollback artifact provided from explicit snapshot")
        _add(checks, "rollback_artifact_renderable_if_snapshot_given", "OK" if rollback_artifact.renderable else "BLOCKED", f"renderable={rollback_artifact.renderable}", blocking=not rollback_artifact.renderable)

    for key in ["live_firewall_read", "live_firewall_write", "iptables_save_executed", "iptables_restore_executed", "lock_acquired", "database_write", "filesystem_write"]:
        _add(checks, f"no_{key}", "OK", f"{key}=false")

    ok_count = len([c for c in checks if c.status == "OK"])
    warn_count = len([c for c in checks if c.status == "WARN"])
    blocked_count = len([c for c in checks if c.status == "BLOCKED"])
    return FirewallPreflightReport(
        backend=plan.backend,
        apply_mode=plan.apply_mode,
        planner_customer_source=plan.planner_customer_source,
        db_customer_input_loaded=plan.db_customer_input_loaded,
        restore_payload_present=restore.restore_payload is not None,
        restore_payload_renderable=restore.renderable,
        apply_contract_present=True,
        apply_contract_readiness=readiness.readiness,
        package_present=True,
        rollback_artifact_present=rollback_artifact is not None,
        rollback_artifact_renderable=bool(rollback_artifact.renderable) if rollback_artifact else False,
        checks=checks,
        check_count=len(checks),
        ok_count=ok_count,
        warn_count=warn_count,
        blocked_count=blocked_count,
        warnings=warnings,
        errors=errors,
    )
