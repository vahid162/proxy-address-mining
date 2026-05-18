from __future__ import annotations

from pathlib import Path
from typing import Any

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


DANGEROUS_AUTHORIZATION_KEYS = (
    "phase10_final_acceptance_authorized",
    "phase11_production_activation_authorized",
    "execution_allowed",
    "runtime_authorized",
    "production_traffic_authorized",
    "firewall_apply_authorized",
    "firewall_mutation_authorized",
    "iptables_restore_authorized",
    "abuse_automation_authorized",
    "real_worker_runtime_authorized",
    "worker_daemon_authorized",
    "worker_runtime_authorized",
    "worker_enforcement_authorized",
    "policy_enforcement_authorized",
    "scheduler_authorized",
    "scheduler_enabled",
    "timer_authorized",
    "timer_enabled",
    "cron_enabled",
    "systemd_timer_enabled",
    "background_loop_authorized",
    "collector_authorized",
    "collector_daemon_authorized",
    "share_collector_authorized",
    "live_share_ingestion_authorized",
    "live_capture_authorized",
    "tcpdump_authorized",
    "conntrack_capture_authorized",
    "production_db_execution_authorized",
    "db_writes_authorized",
    "hard_block_authorized",
    "soft_block_authorized",
    "pause_automation_authorized",
    "customer_mutation_authorized",
    "customer_nat_authorized",
    "customer_firewall_rules_authorized",
    "customer_policy_mutation_authorized",
    "ui_authorized",
    "telegram_authorized",
)


def _dangerous_flags_enabled(*reports: dict[str, Any]) -> list[str]:
    enabled: list[str] = []
    for report in reports:
        component = str(report.get("component", "unknown"))
        for key in DANGEROUS_AUTHORIZATION_KEYS:
            if report.get(key) is True:
                enabled.append(f"{component}.{key}")
    return enabled


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

    output_dangerous_flags = {
        "phase10_final_acceptance_authorized": False,
        "phase11_production_activation_authorized": False,
        "execution_allowed": False,
        "production_traffic_authorized": False,
        "firewall_apply_authorized": False,
        "abuse_automation_authorized": False,
        "real_worker_runtime_authorized": False,
        "scheduler_authorized": False,
        "timer_authorized": False,
        "collector_authorized": False,
        "production_db_execution_authorized": False,
        "hard_block_authorized": False,
        "soft_block_authorized": False,
        "pause_automation_authorized": False,
        "customer_mutation_authorized": False,
        "ui_authorized": False,
        "telegram_authorized": False,
    }

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

    downstream_dangerous_flags = _dangerous_flags_enabled(
        phase10,
        implementation,
        session,
        identity,
        policy,
        share_timeline,
        collector_gate,
        collector_plan,
        runtime_worker,
        scheduler,
        worker_cycle,
    )

    blockers: list[str] = []
    if not gate_ok:
        blockers.append("current_phase_gate_missing_or_invalid")
    if not evidence_present:
        blockers.append("farm5_0_1_135_sync_test_evidence_missing")
    for key, value in checks.items():
        if value != "ACCEPTED":
            blockers.append(f"{key}_not_accepted")
    if downstream_dangerous_flags:
        blockers.append("dangerous_authorization_flag_enabled")

    accepted = not blockers

    return {
        "component": "phase10_final_acceptance_readiness",
        "phase": "Phase 10 — Session / Worker / Policy / Share Timeline",
        "final_decision": "ACCEPTED" if accepted else "BLOCKED",
        "readiness_only": True,
        "current_phase_gate_status": phase10.get("current_phase_gate_status"),
        "farm5_0_1_135_sync_test_evidence_present": evidence_present,
        **checks,
        **output_dangerous_flags,
        "downstream_dangerous_authorization_flags": downstream_dangerous_flags,
        "blockers": blockers,
        "warnings": [],
        "errors": [],
        "next_step": "Phase 10 final acceptance PR after farm5 0.1.136 sync/test evidence; not Phase 11 production activation.",
        "phase11_next_after_final_acceptance": "Production / Customer Activation Gate, controlled CLI canary first.",
    }
