from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services import firewall_apply_gate_readiness_service, firewall_manual_canary_customer_proposal_service, firewall_no_customer_runtime_execution_evidence_service


def build_manual_canary_customer_acceptance_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    blockers: list[str] = []
    proposal = firewall_manual_canary_customer_proposal_service.build_manual_canary_customer_proposal_report(cfg, repo_root=root)
    controlled = firewall_no_customer_runtime_execution_evidence_service.build_no_customer_runtime_execution_evidence_report(cfg, repo_root=root)
    readiness = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg, repo_root=root, include_runtime_approval_summary=False, include_runtime_evidence_summary=False, include_manual_canary_summary=False)
    text = (root / "docs" / "PHASE_STATUS.md").read_text(encoding="utf-8") if (root / "docs" / "PHASE_STATUS.md").exists() else ""
    if not text:
        blockers.append("docs/PHASE_STATUS.md missing")
    if "## Current State" not in text:
        blockers.append("Current State missing or changed")
    if not ("farm5 synced to 0.1.95" in text and "mpf --version: 0.1.95" in text):
        blockers.append("farm5 0.1.95 sync evidence missing")
    if proposal.get("final_decision") != "BLOCKED" or proposal.get("execution_allowed") or proposal.get("customer_nat_authorized") or proposal.get("customer_firewall_rules_authorized"):
        blockers.append("manual canary proposal invalid")
    if controlled.get("final_decision") != "BLOCKED" or controlled.get("execution_allowed"):
        blockers.append("controlled no-customer runtime evidence invalid")
    if readiness.get("final_decision") != "BLOCKED":
        blockers.append("apply-gate-readiness missing/not BLOCKED")
    if cfg.firewall.apply_mode != "plan_only":
        blockers.append("firewall.apply_mode is not plan_only")
    if bool(cfg.proxy.runtime_activation_allowed):
        blockers.append("proxy.runtime_activation_allowed is true")

    return {
        "component": "firewall_manual_canary_customer_acceptance_readiness",
        "phase": "Phase 6 — Firewall Planner",
        "gate_type": "manual_canary_customer_nat_firewall_acceptance_readiness",
        "final_decision": "BLOCKED",
        "authorization_status": "MANUAL_CANARY_ACCEPTANCE_READY_BUT_NOT_GRANTED",
        "acceptance_status": "OPERATOR_ACCEPTANCE_REQUIRED",
        "inspection_only": True,
        "report_only": True,
        "preflight_only": True,
        "dry_run": True,
        "execution_allowed": False,
        "customer_nat_authorized": False,
        "customer_firewall_rules_authorized": False,
        "production_traffic_authorized": False,
        "operator_approval_required": True,
        "separate_canary_server_evidence_pr_required": True,
        "fresh_farm5_canary_evidence_required": True,
        "apply_decision": "BLOCKED",
        "verify_decision": "BLOCKED",
        "rollback_decision": "BLOCKED",
        "manual_canary_proposal_present": True,
        "manual_canary_proposal_blocked": True,
        "manual_canary_proposal_execution_disallowed": True,
        "apply_gate_readiness_blocked": readiness.get("final_decision") == "BLOCKED",
        "customer_nat_allowed": False,
        "customer_firewall_rules_allowed": False,
        "iptables_restore_allowed": False,
        "iptables_restore_executed": False,
        "subprocess_firewall_calls_executed": False,
        "real_adapter_allowed": False,
        "real_adapter_executed": False,
        "db_apply_record_write_allowed": False,
        "db_apply_record_written": False,
        "filesystem_write_executed": False,
        "restore_point_write_allowed": False,
        "lock_acquisition_allowed": False,
        "customer_nat_changed": False,
        "customer_firewall_rules_changed": False,
        "usage_automation_allowed": False,
        "ui_allowed_runtime": False,
        "telegram_allowed_runtime": False,
        "live_firewall_write_allowed": False,
        "live_firewall_apply_allowed": False,
        "live_firewall_verify_allowed": False,
        "live_firewall_rollback_allowed": False,
        "subprocess_firewall_calls_allowed": False,
        "db_mutation": False,
        "restore_point_written": False,
        "lock_acquired": False,
        "production_traffic_changed": False,
        "abuse_automation_allowed_runtime": False,
        "blockers": blockers,
        "errors": [],
    }
