from __future__ import annotations

from mpf.domain.firewall import (
    FirewallEvidenceBundleReport,
    FirewallGateReviewChecklistItem,
    FirewallGateReviewReport,
    FirewallGateReviewRiskItem,
    FirewallPlanMessage,
    FirewallPlanResult,
)
from mpf.services.firewall_evidence_service import build_evidence_bundle_report


def build_gate_review_report(
    plan: FirewallPlanResult | None = None,
    evidence: FirewallEvidenceBundleReport | None = None,
) -> FirewallGateReviewReport:
    if evidence is None:
        if plan is None:
            raise ValueError("plan or evidence is required")
        evidence = build_evidence_bundle_report(plan)

    risks = [
        FirewallGateReviewRiskItem("R-001", "Live apply remains forbidden in current phase", "CRITICAL", "BLOCKER", "firewall_apply_allowed=no; apply_mode=plan_only", "Wait for dedicated apply gate acceptance", "operator+safety"),
        FirewallGateReviewRiskItem("R-002", "Backend exposure must remain blocked externally", "HIGH", "OK", "internal_backend_reachable=OK; external_backend_exposed=NO", "Keep doctor checks green before any future gate", "network"),
        FirewallGateReviewRiskItem("R-003", "Rollback/canary remain contract-only", "MEDIUM", "WARNING", "offline artifacts only; no live verify", "Future gate must require controlled live execution plan", "operator"),
    ]
    checklist = [
        FirewallGateReviewChecklistItem("phase_gate", "Phase gate forbids live apply", "BLOCKED", "firewall_apply_allowed=no", True),
        FirewallGateReviewChecklistItem("evidence_bundle", "Evidence bundle present", "PASS", f"evidence_version={evidence.evidence_version}", True),
        FirewallGateReviewChecklistItem("risk_matrix", "Phase 6-C1 risk matrix reflected", "PASS", "deterministic risk rows rendered", True),
        FirewallGateReviewChecklistItem("config_source_warning", "config-only source is explicit warning", "WARN", "config-only accepted only by explicit operator input", False),
    ]
    blockers = [r.risk_id for r in risks if r.status == "BLOCKER"]
    warnings = list(evidence.warnings)
    errors = list(evidence.errors)
    if errors:
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
    checklist_summary = {
        "total": len(checklist),
        "pass": len([c for c in checklist if c.status == "PASS"]),
        "warn": len([c for c in checklist if c.status == "WARN"]),
        "blocked": len([c for c in checklist if c.status == "BLOCKED"]),
    }
    safety_flags = dict(evidence.safety_flags)
    safety_flags.update({"restore_point_written": False, "rollback_written": False})

    return FirewallGateReviewReport(
        phase_gate_summary={"firewall_apply_allowed": "no", "production_traffic": "none", "abuse_automation_allowed": "no"},
        evidence_summary={"present": True, "evidence_version": evidence.evidence_version, "final_verdict": evidence.final_verdict},
        risk_summary=risk_summary,
        checklist_summary=checklist_summary,
        rollback_readiness_summary={"status": "blocked_for_future_gate"},
        canary_readiness_summary={"status": "blocked_for_future_gate"},
        abuse_requirement_summary={
            "state_flow": "normal -> over_tracking -> over_grace -> hard",
            "sustained_hardening_seconds": 3600,
            "preserved": True,
        },
        safety_flags=safety_flags,
        risks=risks,
        checklist=checklist,
        blockers=blockers,
        warnings=warnings,
        errors=errors,
        final_decision="BLOCKED",
    )
