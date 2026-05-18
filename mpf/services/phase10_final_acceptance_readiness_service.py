from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services.phase10_collector_dry_run_gate_service import build_collector_dry_run_gate_readiness_report
from mpf.services.phase10_collector_dry_run_plan_service import build_collector_dry_run_plan_report
from mpf.services.phase10_implementation_readiness_service import build_phase10_implementation_readiness_report
from mpf.services.phase10_readiness_service import build_phase10_readiness_report
from mpf.services.phase10_runtime_worker_dry_run_readiness_service import build_runtime_worker_dry_run_readiness_report
from mpf.services.phase10_scheduler_dry_run_readiness_service import build_scheduler_dry_run_readiness_report
from mpf.services.phase10_session_model_readiness_service import build_session_model_readiness_report
from mpf.services.phase10_share_timeline_model_readiness_service import build_share_timeline_model_readiness_report
from mpf.services.phase10_worker_cycle_dry_run_plan_service import build_worker_cycle_dry_run_plan_report
from mpf.services.phase10_worker_identity_readiness_service import build_worker_identity_readiness_report
from mpf.services.phase10_worker_policy_contract_readiness_service import build_worker_policy_contract_readiness_report


def build_phase10_final_acceptance_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]

    phase10 = build_phase10_readiness_report(cfg, repo_root=root)
    implementation = build_phase10_implementation_readiness_report(cfg, repo_root=root)
    session = build_session_model_readiness_report(cfg, repo_root=root)
    identity = build_worker_identity_readiness_report(cfg, repo_root=root)
    policy = build_worker_policy_contract_readiness_report(cfg, repo_root=root)
    share_timeline = build_share_timeline_model_readiness_report(cfg, repo_root=root)
    collector_gate = build_collector_dry_run_gate_readiness_report(cfg, repo_root=root)
    collector_plan = build_collector_dry_run_plan_report(cfg, repo_root=root)
    runtime_worker = build_runtime_worker_dry_run_readiness_report(cfg, repo_root=root)
    scheduler = build_scheduler_dry_run_readiness_report(cfg, repo_root=root)
    worker_cycle = build_worker_cycle_dry_run_plan_report(cfg, repo_root=root)

    evidence_present = (root / "docs/PHASE_10_FARM5_0_1_135_SYNC_TEST_EVIDENCE.md").exists()
    gate_ok = phase10.get("current_phase_gate_status") == "OK"

    dangerous_keys = [
        "phase10_final_acceptance_authorized",
        "phase11_production_activation_authorized",
        "execution_allowed",
        "production_traffic_authorized",
        "firewall_apply_authorized",
        "abuse_automation_authorized",
        "real_worker_runtime_authorized",
        "scheduler_authorized",
        "timer_authorized",
        "collector_authorized",
        "production_db_execution_authorized",
        "hard_block_authorized",
        "soft_block_authorized",
        "pause_automation_authorized",
        "customer_mutation_authorized",
        "ui_authorized",
        "telegram_authorized",
    ]
    dangerous_flags = {k: False for k in dangerous_keys}
    dangerous_enabled = any(bool(v) for v in dangerous_flags.values())

    checks = {
        "phase10_readiness": phase10.get("final_decision"),
        "phase10_implementation_readiness": implementation.get("final_decision"),
        "session_model_readiness": session.get("final_decision"),
        "worker_identity_readiness": identity.get("final_decision"),
        "worker_policy_contract_readiness": policy.get("final_decision"),
        "share_timeline_model_readiness": share_timeline.get("final_decision"),
        "collector_dry_run_gate_readiness": collector_gate.get("final_decision"),
        "collector_dry_run_plan": collector_plan.get("final_decision"),
        "runtime_worker_dry_run_readiness": runtime_worker.get("final_decision"),
        "scheduler_dry_run_readiness": scheduler.get("final_decision"),
        "worker_cycle_dry_run_plan": worker_cycle.get("final_decision"),
    }

    blockers: list[str] = []
    if not gate_ok:
        blockers.append("current_phase_gate_missing_or_invalid")
    if not evidence_present:
        blockers.append("farm5_0_1_135_sync_test_evidence_missing")
    for key, value in checks.items():
        if value != "ACCEPTED":
            blockers.append(f"{key}_not_accepted")
    if dangerous_enabled:
        blockers.append("dangerous_authorization_flag_enabled")

    accepted = not blockers

    report = {
        "component": "phase10_final_acceptance_readiness",
        "phase": "Phase 10 — Session / Worker / Policy / Share Timeline",
        "final_decision": "ACCEPTED" if accepted else "BLOCKED",
        "readiness_only": True,
        "current_phase_gate_status": phase10.get("current_phase_gate_status"),
        "farm5_0_1_135_sync_test_evidence_present": evidence_present,
        **checks,
        **dangerous_flags,
        "blockers": blockers,
        "warnings": [],
        "errors": [],
        "next_step": "Phase 10 final acceptance PR after farm5 0.1.136 sync/test evidence; not Phase 11 production activation.",
        "phase11_next_after_final_acceptance": "Production / Customer Activation Gate, controlled CLI canary first.",
    }
    return report
