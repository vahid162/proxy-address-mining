from __future__ import annotations

from mpf.domain.firewall import (
    FirewallApplyContract,
    FirewallApplyPackageReport,
    FirewallApplyReadinessContract,
    FirewallEvidenceBundleReport,
    FirewallEvidenceSection,
    FirewallPlanMessage,
    FirewallPlanResult,
    FirewallPreflightReport,
    FirewallRollbackArtifactContract,
)
from mpf.services.firewall_apply_contract_service import build_apply_readiness_contract
from mpf.services.firewall_apply_package_service import build_apply_package_report
from mpf.services.firewall_preflight_service import build_preflight_report
from mpf.services.firewall_restore_payload_renderer import render_restore_contract


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


def _section(key: str, status: str, summary: str, evidence: dict, warnings: list[FirewallPlanMessage] | None = None, errors: list[FirewallPlanMessage] | None = None) -> FirewallEvidenceSection:
    return FirewallEvidenceSection(key=key, status=status, summary=summary, evidence=evidence, warnings=warnings or [], errors=errors or [])


def build_evidence_bundle_report(
    plan: FirewallPlanResult,
    restore_contract: FirewallApplyContract | None = None,
    apply_readiness_contract: FirewallApplyReadinessContract | None = None,
    package_report: FirewallApplyPackageReport | None = None,
    rollback_artifact: FirewallRollbackArtifactContract | None = None,
    preflight_report: FirewallPreflightReport | None = None,
) -> FirewallEvidenceBundleReport:
    restore = restore_contract or render_restore_contract(plan)
    readiness = apply_readiness_contract or build_apply_readiness_contract(plan, restore)
    package = package_report or build_apply_package_report(plan, restore, readiness)
    preflight = preflight_report or build_preflight_report(plan, restore, readiness, package, rollback_artifact)

    warnings = _dedupe_messages(plan.warnings + restore.warnings + readiness.warnings + package.warnings + preflight.warnings)
    errors = _dedupe_messages(plan.errors + restore.errors + readiness.errors + package.errors + preflight.errors)

    sections = [
        _section("phase_gate", "BLOCKED", "Current phase blocks live apply/rollback.", {"final_verdict": "BLOCKED", "readiness": "blocked_for_live_apply"}),
        _section("planner", "OK" if len(plan.errors) == 0 else "BLOCKED", "Planner result loaded for offline evidence.", {"chains": len(plan.chains), "rules": len(plan.rules), "changes": len(plan.changes), "planner_customer_source": plan.planner_customer_source, "db_customer_input_loaded": plan.db_customer_input_loaded}, plan.warnings, plan.errors),
        _section("diff_contract", "OK", "Diff contract remains inspection-only.", {"snapshot_input": "none", "live_read_performed": False}),
        _section("doctor_contract", "OK" if plan.planner_customer_source == "db_readonly" else "WARN", "Doctor contract remains offline/planning-only.", {"planner_customer_source": plan.planner_customer_source}),
        _section("restore_payload", "OK" if restore.renderable else "BLOCKED", "Restore payload artifact contract.", {"renderable": restore.renderable, "applyable": restore.applyable}, restore.warnings, restore.errors),
        _section("apply_contract", "OK" if readiness.readiness == "blocked_for_live_apply" else "BLOCKED", "Apply-readiness contract (inspection-only).", {"readiness": readiness.readiness, "applyable": readiness.applyable}, readiness.warnings, readiness.errors),
        _section("apply_package", "OK", "Offline apply package report present.", {"present": True, "readiness": package.readiness, "applyable": package.applyable}, package.warnings, package.errors),
        _section("rollback_artifact", "WARN" if rollback_artifact is None else ("OK" if rollback_artifact.renderable else "BLOCKED"), "Rollback artifact requires explicit offline snapshot input.", {"present": rollback_artifact is not None, "renderable": bool(rollback_artifact.renderable) if rollback_artifact is not None else False}),
        _section("preflight", preflight.final_verdict, "Offline preflight result.", {"final_verdict": preflight.final_verdict, "readiness": preflight.readiness, "applyable": preflight.applyable}, preflight.warnings, preflight.errors),
        _section("safety_flags", "OK", "No live read/write/apply/rollback/writes occurred.", dict(preflight.safety_flags)),
        _section("abuse_future_requirement", "WARN", "Abuse automation not implemented now; mandatory future path remains intact.", {"state_machine": "normal -> over_tracking -> over_grace -> hard", "sustained_hardening_seconds": 3600}),
    ]
    ok_count = len([s for s in sections if s.status == "OK"])
    warn_count = len([s for s in sections if s.status == "WARN"])
    blocked_count = len([s for s in sections if s.status == "BLOCKED"])
    return FirewallEvidenceBundleReport(
        backend=plan.backend,
        apply_mode=plan.apply_mode,
        planner_customer_source=plan.planner_customer_source,
        db_customer_input_loaded=plan.db_customer_input_loaded,
        plan_summary=package.plan_summary,
        diff_summary={"inspection_only": True, "live_snapshot_auto_read": False},
        doctor_summary={"inspection_only": True, "planner_customer_source": plan.planner_customer_source},
        restore_summary=package.restore_payload_summary,
        apply_contract_summary=package.apply_contract_summary,
        package_summary={"present": True, "readiness": package.readiness, "applyable": package.applyable},
        rollback_summary={"present": rollback_artifact is not None, "renderable": bool(rollback_artifact.renderable) if rollback_artifact is not None else False},
        preflight_summary={"final_verdict": preflight.final_verdict, "readiness": preflight.readiness, "applyable": preflight.applyable},
        phase_gate_summary={"current_step": "Phase 6-B", "live_apply_allowed": False, "final_verdict": "BLOCKED"},
        section_count=len(sections),
        ok_count=ok_count,
        warn_count=warn_count,
        blocked_count=blocked_count,
        sections=sections,
        warnings=warnings,
        errors=errors,
        safety_flags=dict(preflight.safety_flags),
    )
