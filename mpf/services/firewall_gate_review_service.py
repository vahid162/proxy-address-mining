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


def build_gate_review_report(plan: FirewallPlanResult | None = None, evidence: FirewallEvidenceBundleReport | None = None, *, apply_gate_readiness: dict[str, object] | None = None, live_snapshot_scaffold: dict[str, object] | None = None) -> FirewallGateReviewReport:
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

    return FirewallGateReviewReport(
        phase_gate_summary={"firewall_apply_allowed": "no", "production_traffic": "none", "abuse_automation_allowed": "no"},
        evidence_summary={"present": True, "evidence_version": evidence.evidence_version, "final_verdict": evidence.final_verdict, "planner_customer_source": evidence.planner_customer_source, "db_customer_input_loaded": evidence.db_customer_input_loaded},
        risk_summary=risk_summary,
        checklist_summary=checklist_summary,
        rollback_readiness_summary={"status": "blocked_for_future_gate"},
        canary_readiness_summary={"status": "blocked_for_future_gate"},
        apply_gate_readiness_summary=apply_gate_readiness_summary,
        live_snapshot_scaffold_summary=live_snapshot_scaffold_summary,
        abuse_requirement_summary={"state_flow": "normal -> over_tracking -> over_grace -> hard", "sustained_hardening_seconds": 3600, "preserved": True},
        safety_flags=safety_flags,
        risks=risks,
        checklist=checklist,
        blockers=blockers,
        warnings=list(evidence.warnings),
        errors=list(evidence.errors),
        final_decision="BLOCKED",
    )
