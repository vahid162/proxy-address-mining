from __future__ import annotations

from mpf.domain.firewall import (
    FirewallEvidenceBundleReport,
    FirewallGateReviewChecklistItem,
    FirewallGateReviewReport,
    FirewallGateReviewRiskItem,
    FirewallPlanResult,
)
from mpf.services.firewall_evidence_service import build_evidence_bundle_report


def _risk_rows() -> list[FirewallGateReviewRiskItem]:
    return [
        FirewallGateReviewRiskItem("R-001", "Backend direct external exposure", "CRITICAL", "BLOCKER", "external_backend_exposed must remain NO", "Block gate until external exposure checks are clean", "network"),
        FirewallGateReviewRiskItem("R-002", "Internal backend reachability failure", "CRITICAL", "BLOCKER", "internal_backend_reachable must remain OK", "Fix internal pathing before any future gate", "network"),
        FirewallGateReviewRiskItem("R-003", "Stale or missing restore artifact", "HIGH", "WARNING", "restore payload/rollback evidence may be stale", "Refresh explicit offline artifacts before review", "operator"),
        FirewallGateReviewRiskItem("R-004", "Rollback strategy not reviewed", "HIGH", "WARNING", "rollback readiness remains blocked_for_future_gate", "Run rollback review checklist in future gate", "operator"),
        FirewallGateReviewRiskItem("R-005", "Apply-readiness contract not reviewed", "HIGH", "WARNING", "apply readiness is contract-only and blocked", "Complete future gate review with operator sign-off", "operator+safety"),
        FirewallGateReviewRiskItem("R-006", "Evidence bundle missing or stale", "HIGH", "WARNING", "evidence bundle must exist and be current", "Rebuild evidence bundle from latest offline inputs", "operator"),
        FirewallGateReviewRiskItem("R-007", "Version/changelog/docs mismatch", "MEDIUM", "WARNING", "version/docs/changelog drift can mislead operators", "Align release metadata before acceptance", "release"),
        FirewallGateReviewRiskItem("R-008", "Server time synchronization unresolved", "MEDIUM", "WARNING", "time sync warning exists for production-dependent jobs", "Fix time sync before production-dependent automation", "platform"),
        FirewallGateReviewRiskItem("R-009", "Unreviewed customer NAT redirect", "CRITICAL", "BLOCKER", "customer NAT redirect is forbidden in current phase", "Keep NAT changes planned_only until apply gate", "safety"),
        FirewallGateReviewRiskItem("R-010", "Unreviewed customer firewall rule", "CRITICAL", "BLOCKER", "customer firewall rules are forbidden in current phase", "Keep firewall changes planned_only until apply gate", "safety"),
        FirewallGateReviewRiskItem("R-011", "Hidden fallback from DB-backed input to config-only", "HIGH", "WARNING", "planner source must stay explicit", "Use db-readonly by default; warn only when explicitly config-only", "service"),
        FirewallGateReviewRiskItem("R-012", "Final decision/verdict accidentally OK while apply is forbidden", "CRITICAL", "BLOCKER", "firewall_apply_allowed=no", "Force final_decision BLOCKED until dedicated apply gate", "safety"),
        FirewallGateReviewRiskItem("R-013", "applyable accidentally true while apply is forbidden", "CRITICAL", "BLOCKER", "applyable must remain false", "Keep applyable=false for offline review", "safety"),
        FirewallGateReviewRiskItem("R-014", "Abuse coverage weakened", "CRITICAL", "BLOCKER", "mandatory abuse flow must stay preserved", "Preserve normal->over_tracking->over_grace->hard and 3600s contract", "abuse"),
        FirewallGateReviewRiskItem("R-015", "Customer silently excluded from future abuse scan", "HIGH", "WARNING", "no-silent-skip policy is mandatory", "Require explicit exemption reason+expiry only", "abuse"),
        FirewallGateReviewRiskItem("R-016", "Public v2rayA UI exposure", "CRITICAL", "BLOCKER", "UI must remain local-only", "Maintain localhost-only binding and exposure checks", "network"),
        FirewallGateReviewRiskItem("R-017", "Public backend exposure", "CRITICAL", "BLOCKER", "backend must not be publicly reachable", "Keep external_backend_exposed=NO", "network"),
        FirewallGateReviewRiskItem("R-018", "Command syntax drift from implemented CLI", "MEDIUM", "WARNING", "stale docs/examples can cause unsafe operations", "Keep docs synced with current CLI syntax", "docs"),
    ]


def _compact_no_customer_apply_scaffold_summary(report: dict[str, object] | None) -> dict[str, object]:
    if report is None:
        return {
            "no_customer_apply_scaffold_present": False,
            "no_customer_apply_scaffold_final_decision": "BLOCKED",
            "no_customer_apply_scaffold_authorization_status": "NOT_PROVIDED",
            "no_customer_apply_scaffold_execution_allowed": False,
            "no_customer_apply_scaffold_apply_decision": "BLOCKED",
            "no_customer_apply_scaffold_verify_decision": "BLOCKED",
            "no_customer_apply_scaffold_rollback_decision": "BLOCKED",
        }
    return {
        "no_customer_apply_scaffold_present": True,
        "no_customer_apply_scaffold_final_decision": report.get("final_decision", "BLOCKED"),
        "no_customer_apply_scaffold_authorization_status": report.get("authorization_status", "NOT_AUTHORIZED_FOR_APPLY"),
        "no_customer_apply_scaffold_execution_allowed": bool(report.get("execution_allowed", False)),
        "no_customer_apply_scaffold_apply_decision": report.get("apply_decision", "BLOCKED"),
        "no_customer_apply_scaffold_verify_decision": report.get("verify_decision", "BLOCKED"),
        "no_customer_apply_scaffold_rollback_decision": report.get("rollback_decision", "BLOCKED"),
    }

def _compact_no_customer_apply_acceptance_gate_summary(report: dict[str, object] | None) -> dict[str, object]:
    if report is None:
        return {
            "no_customer_apply_acceptance_gate_present": False,
            "no_customer_apply_acceptance_gate_final_decision": "BLOCKED",
            "no_customer_apply_acceptance_gate_authorization_status": "NOT_PROVIDED",
            "no_customer_apply_acceptance_gate_execution_allowed": False,
            "no_customer_apply_acceptance_gate_apply_decision": "BLOCKED",
            "no_customer_apply_acceptance_gate_verify_decision": "BLOCKED",
            "no_customer_apply_acceptance_gate_rollback_decision": "BLOCKED",
        }
    return {
        "no_customer_apply_acceptance_gate_present": True,
        "no_customer_apply_acceptance_gate_final_decision": report.get("final_decision", "BLOCKED"),
        "no_customer_apply_acceptance_gate_authorization_status": report.get("authorization_status", "UNKNOWN"),
        "no_customer_apply_acceptance_gate_execution_allowed": bool(report.get("execution_allowed", False)),
        "no_customer_apply_acceptance_gate_apply_decision": report.get("apply_decision", "BLOCKED"),
        "no_customer_apply_acceptance_gate_verify_decision": report.get("verify_decision", "BLOCKED"),
        "no_customer_apply_acceptance_gate_rollback_decision": report.get("rollback_decision", "BLOCKED"),
    }


def _compact_no_customer_apply_execution_gate_summary(report: dict[str, object] | None) -> dict[str, object]:
    if report is None:
        return {
            "no_customer_apply_execution_gate_present": False,
            "no_customer_apply_execution_gate_final_decision": "BLOCKED",
            "no_customer_apply_execution_gate_authorization_status": "NOT_PROVIDED",
            "no_customer_apply_execution_gate_execution_allowed": False,
        }
    return {
        "no_customer_apply_execution_gate_present": True,
        "no_customer_apply_execution_gate_final_decision": report.get("final_decision", "BLOCKED"),
        "no_customer_apply_execution_gate_authorization_status": report.get("authorization_status", "NOT_ACCEPTED_FOR_EXECUTION"),
        "no_customer_apply_execution_gate_execution_allowed": bool(report.get("execution_allowed", False)),
    }


def build_gate_review_report(plan: FirewallPlanResult | None = None, evidence: FirewallEvidenceBundleReport | None = None, *, apply_gate_readiness: dict[str, object] | None = None, no_customer_runtime_execution_approval: dict[str, object] | None = None, no_customer_apply_scaffold: dict[str, object] | None = None, no_customer_apply_acceptance_gate: dict[str, object] | None = None, no_customer_apply_execution_gate: dict[str, object] | None = None, no_customer_apply_package: dict[str, object] | None = None, no_customer_apply_execution_acceptance: dict[str, object] | None = None, live_snapshot_scaffold: dict[str, object] | None = None, live_snapshot_read: dict[str, object] | None = None, restore_lock_record_gate: dict[str, object] | None = None, restore_lock_record_readiness: dict[str, object] | None = None, restore_lock_record_acceptance_gate: dict[str, object] | None = None, restore_lock_record_execution_gate: dict[str, object] | None = None) -> FirewallGateReviewReport:
    if evidence is None:
        if plan is None:
            raise ValueError("plan or evidence is required")
        evidence = build_evidence_bundle_report(plan)

    risks = _risk_rows()
    checklist = [
        FirewallGateReviewChecklistItem("phase_gate", "Phase gate forbids live apply", "BLOCKED", "firewall_apply_allowed=no", True),
        FirewallGateReviewChecklistItem("evidence_bundle", "Evidence bundle present", "PASS", f"evidence_version={evidence.evidence_version}", True),
        FirewallGateReviewChecklistItem("risk_matrix", "Phase 6-C1 risk matrix reflected", "PASS", "deterministic risk rows R-001..R-018 rendered", True),
    ]
    if evidence.planner_customer_source == "config_only":
        checklist.append(FirewallGateReviewChecklistItem("config_source_warning", "config-only source is explicit warning", "WARN", "config-only accepted only by explicit operator input", False))
    else:
        checklist.append(FirewallGateReviewChecklistItem("config_source_warning", "db-readonly source remains default", "PASS", "planner_customer_source=db_readonly", False))

    blockers = [r.risk_id for r in risks if r.status == "BLOCKER"]
    if evidence.errors:
        blockers.append("PLAN_OR_EVIDENCE_ERRORS")

    risk_summary = {
        "total": len(risks),
        "critical": len([r for r in risks if r.severity == "CRITICAL"]),
        "high": len([r for r in risks if r.severity == "HIGH"]),
        "medium": len([r for r in risks if r.severity == "MEDIUM"]),
        "low": len([r for r in risks if r.severity == "LOW"]),
        "blockers": len([r for r in risks if r.status == "BLOCKER"]),
        "warnings": len([r for r in risks if r.status == "WARNING"]),
    }
    checklist_summary = {"total": len(checklist), "pass": len([c for c in checklist if c.status == "PASS"]), "warn": len([c for c in checklist if c.status == "WARN"]), "blocked": len([c for c in checklist if c.status == "BLOCKED"])}
    safety_flags = dict(evidence.safety_flags)
    safety_flags.update({"restore_point_written": False, "rollback_written": False})

    live_snapshot_scaffold_summary = live_snapshot_scaffold or {
        "component": "firewall_live_snapshot_scaffold",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_AUTHORIZED",
        "live_firewall_read_executed": False,
        "iptables_save_executed": False,
        "subprocess_executed": False,
        "firewall_mutation": False,
        "db_mutation": False,
        "customer_nat_changed": False,
        "customer_firewall_rules_changed": False,
        "production_traffic_changed": False,
        "blockers": ["live_snapshot_scaffold_not_provided"],
    }


    live_snapshot_read_summary = live_snapshot_read or {
        "component": "firewall_live_snapshot_read",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_AUTHORIZED",
        "live_firewall_read_allowed": False,
        "live_firewall_read_executed": False,
        "iptables_save_allowed": False,
        "iptables_save_executed": False,
        "subprocess_allowed": False,
        "subprocess_executed": False,
        "filesystem_write_executed": False,
        "firewall_mutation": False,
        "db_mutation": False,
        "customer_nat_changed": False,
        "customer_firewall_rules_changed": False,
        "production_traffic_changed": False,
        "blockers": ["live_snapshot_read_not_provided"],
    }

    apply_gate_readiness_summary = apply_gate_readiness or {
        "final_decision": "BLOCKED",
        "documentation_boundary_present": False,
        "farm5_0_1_88_sync_evidence_present": False,
        "current_state_preserved": False,
        "apply_mode_plan_only": True,
        "runtime_activation_allowed": False,
        "blockers": ["apply_gate_readiness_not_provided"],
        "missing_requirements": [],
    }
    no_customer_apply_scaffold_summary = _compact_no_customer_apply_scaffold_summary(no_customer_apply_scaffold)
    apply_gate_readiness_summary["no_customer_apply_scaffold_summary"] = no_customer_apply_scaffold_summary
    apply_gate_readiness_summary["no_customer_apply_acceptance_gate_summary"] = _compact_no_customer_apply_acceptance_gate_summary(no_customer_apply_acceptance_gate)
    apply_gate_readiness_summary["no_customer_apply_execution_gate_summary"] = _compact_no_customer_apply_execution_gate_summary(no_customer_apply_execution_gate)

    apply_gate_readiness_summary["no_customer_apply_package_summary"] = {
        "no_customer_apply_package_present": bool(no_customer_apply_package) if no_customer_apply_package is not None else False,
        "no_customer_apply_package_final_decision": (no_customer_apply_package or {}).get("final_decision", "BLOCKED"),
        "no_customer_apply_package_authorization_status": (no_customer_apply_package or {}).get("authorization_status", "NOT_PROVIDED"),
        "no_customer_apply_package_execution_allowed": bool((no_customer_apply_package or {}).get("execution_allowed", False)),
        "no_customer_apply_package_customer_safe": not any((no_customer_apply_package or {}).get(k, False) for k in ("payload_contains_customer_nat","payload_contains_customer_firewall_rules","payload_contains_production_traffic","payload_contains_iptables_restore")),
    }
    apply_gate_readiness_summary["no_customer_apply_execution_acceptance_summary"] = {
        "no_customer_apply_execution_acceptance_present": bool(no_customer_apply_execution_acceptance) if no_customer_apply_execution_acceptance is not None else False,
        "no_customer_apply_execution_acceptance_final_decision": (no_customer_apply_execution_acceptance or {}).get("final_decision", "BLOCKED"),
        "no_customer_apply_execution_acceptance_authorization_status": (no_customer_apply_execution_acceptance or {}).get("authorization_status", "NOT_PROVIDED"),
        "no_customer_apply_execution_acceptance_execution_allowed": bool((no_customer_apply_execution_acceptance or {}).get("execution_allowed", False)),
    }


    apply_gate_readiness_summary["no_customer_runtime_execution_approval_summary"] = {
        "no_customer_runtime_execution_approval_present": bool(no_customer_runtime_execution_approval) if no_customer_runtime_execution_approval is not None else False,
        "no_customer_runtime_execution_approval_final_decision": (no_customer_runtime_execution_approval or {}).get("final_decision", "BLOCKED"),
        "no_customer_runtime_execution_approval_authorization_status": (no_customer_runtime_execution_approval or {}).get("authorization_status", "NOT_PROVIDED"),
        "no_customer_runtime_execution_approval_execution_allowed": bool((no_customer_runtime_execution_approval or {}).get("execution_allowed", False)),
        "no_customer_runtime_execution_approval_operator_approval_required": bool((no_customer_runtime_execution_approval or {}).get("operator_approval_required", True)),
        "no_customer_runtime_execution_approval_fresh_farm5_runtime_execution_evidence_required": bool((no_customer_runtime_execution_approval or {}).get("fresh_farm5_runtime_execution_evidence_required", True)),
        "no_customer_runtime_execution_approval_separate_runtime_execution_pr_required": bool((no_customer_runtime_execution_approval or {}).get("separate_runtime_execution_pr_required", True)),
    }

    restore_lock_record_readiness_summary = restore_lock_record_readiness or {
        "component": "firewall_restore_lock_record_readiness",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_AUTHORIZED_FOR_WRITES",
        "report_only": True,
        "apply_decision": "BLOCKED",
        "blockers": ["restore_lock_record_readiness_not_provided"],
    }

    restore_lock_record_gate_summary = restore_lock_record_gate or {
        "component": "firewall_restore_lock_record_gate",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_ACCEPTED",
        "report_only": True,
        "apply_decision": "BLOCKED",
        "blockers": ["restore_lock_record_gate_not_provided"],
    }
    restore_lock_record_acceptance_gate_summary = restore_lock_record_acceptance_gate or {
        "component": "firewall_restore_lock_record_acceptance_gate",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_ACCEPTED_FOR_EXECUTION",
        "report_only": True,
        "apply_decision": "BLOCKED",
        "blockers": ["restore_lock_record_acceptance_gate_not_provided"],
    }
    restore_lock_record_execution_gate_summary = restore_lock_record_execution_gate or {
        "component": "firewall_restore_lock_record_execution_gate",
        "final_decision": "BLOCKED",
        "authorization_status": "NOT_AUTHORIZED_FOR_EXECUTION",
        "report_only": True,
        "apply_decision": "BLOCKED",
        "blockers": ["restore_lock_record_execution_gate_not_provided"],
    }

    return FirewallGateReviewReport(
        phase_gate_summary={"firewall_apply_allowed": "no", "production_traffic": "none", "abuse_automation_allowed": "no"},
        evidence_summary={"present": True, "evidence_version": evidence.evidence_version, "final_verdict": evidence.final_verdict, "planner_customer_source": evidence.planner_customer_source, "db_customer_input_loaded": evidence.db_customer_input_loaded},
        risk_summary=risk_summary,
        checklist_summary=checklist_summary,
        rollback_readiness_summary={"status": "blocked_for_future_gate"},
        canary_readiness_summary={"status": "blocked_for_future_gate"},
        apply_gate_readiness_summary=apply_gate_readiness_summary,
        live_snapshot_scaffold_summary=live_snapshot_scaffold_summary,
        live_snapshot_read_summary=live_snapshot_read_summary,
        restore_lock_record_gate_summary=restore_lock_record_gate_summary,
        restore_lock_record_acceptance_gate_summary=restore_lock_record_acceptance_gate_summary,
        restore_lock_record_execution_gate_summary=restore_lock_record_execution_gate_summary,
        restore_lock_record_readiness_summary=restore_lock_record_readiness_summary,
        abuse_requirement_summary={"state_flow": "normal -> over_tracking -> over_grace -> hard", "sustained_hardening_seconds": 3600, "preserved": True},
        safety_flags=safety_flags,
        risks=risks,
        checklist=checklist,
        blockers=blockers,
        warnings=list(evidence.warnings),
        errors=list(evidence.errors),
        final_decision="BLOCKED",
    )
