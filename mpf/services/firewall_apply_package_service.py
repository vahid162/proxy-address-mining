from __future__ import annotations

from mpf.domain.firewall import (
    FirewallApplyContract,
    FirewallApplyPackageReport,
    FirewallApplyReadinessContract,
    FirewallPlanMessage,
    FirewallPlanResult,
)
from mpf.services.firewall_apply_contract_service import build_apply_readiness_contract
from mpf.services.firewall_restore_payload_renderer import render_restore_contract


def _dedupe_messages(messages: list[FirewallPlanMessage]) -> list[FirewallPlanMessage]:
    seen: set[tuple[str, str, str]] = set()
    result: list[FirewallPlanMessage] = []
    for msg in messages:
        key = (msg.severity, msg.code, msg.message)
        if key in seen:
            continue
        seen.add(key)
        result.append(msg)
    return result


def build_apply_package_report(
    plan: FirewallPlanResult,
    restore_contract: FirewallApplyContract | None = None,
    apply_readiness_contract: FirewallApplyReadinessContract | None = None,
) -> FirewallApplyPackageReport:
    restore = restore_contract or render_restore_contract(plan)
    readiness = apply_readiness_contract or build_apply_readiness_contract(plan, restore)

    warnings: list[FirewallPlanMessage] = []
    errors: list[FirewallPlanMessage] = []
    warnings.extend(plan.warnings)
    errors.extend(plan.errors)
    warnings.extend(restore.warnings)
    errors.extend(restore.errors)
    warnings.extend(readiness.warnings)
    errors.extend(readiness.errors)
    warnings = _dedupe_messages(warnings)
    errors = _dedupe_messages(errors)

    payload_sha256 = None
    payload_line_count = 0
    if restore.restore_payload is not None:
        payload_sha256 = restore.restore_payload.payload_sha256
        payload_line_count = restore.restore_payload.payload_line_count

    return FirewallApplyPackageReport(
        backend=plan.backend,
        apply_mode=plan.apply_mode,
        planner_customer_source=plan.planner_customer_source,
        db_customer_input_loaded=plan.db_customer_input_loaded,
        applyable=False,
        readiness="blocked_for_live_apply",
        plan_summary={
            "chain_count": len(plan.chains),
            "rule_count": len(plan.rules),
            "change_count": len(plan.changes),
            "planner_customer_source": plan.planner_customer_source,
            "db_customer_input_loaded": plan.db_customer_input_loaded,
        },
        restore_payload_summary={
            "renderable": restore.renderable,
            "applyable": restore.applyable,
            "artifact_only": restore.artifact_only,
            "live_apply_allowed": restore.live_apply_allowed,
        },
        apply_contract_summary={
            "readiness": readiness.readiness,
            "restore_point_required": readiness.restore_point_contract.restore_point_required,
            "lock_required_for_apply": readiness.lock_contract.lock_required_for_apply,
            "verify_required_after_apply": readiness.verify_contract.verify_required_after_apply,
            "rollback_artifact_required": readiness.rollback_contract.rollback_artifact_required,
            "applyable": readiness.applyable,
        },
        payload_sha256=payload_sha256,
        payload_line_count=payload_line_count,
        chain_count=len(plan.chains),
        rule_count=len(plan.rules),
        warning_count=len(warnings),
        error_count=len(errors),
        warnings=warnings,
        errors=errors,
        source_plan=plan,
        restore_contract=restore,
        apply_readiness_contract=readiness,
    )
