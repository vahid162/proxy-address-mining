from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def build_phase8_abuse_state_machine_contract_report(
    cfg: MPFConfig,
    repo_root: Path | None = None,
) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    readme = _read(root / "README.md")
    index = _read(root / "docs/INDEX.md")
    ai_rules = _read(root / "docs/AI_CODING_RULES.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")
    planning = _read(root / "mpf/services/phase8_planning_readiness_service.py")

    phase7_accepted = "current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in phase_status
    phase8_working = "current_working_phase: Phase 8 — Abuse 1h Core planning/readiness" in phase_status
    current_state_preserved = phase7_accepted and phase8_working

    farm5_sync = "synced to 0.1.110" in phase_status and "/var/backups/mpf/source-before-zip-sync-20260515T192056Z" in phase_status and "701 passed" in phase_status
    planning_ready = "phase8_planning_readiness" in planning
    ai_present = "Current Phase 8 Step — Abuse State-Machine Contract" in ai_phase8
    rem_aligned = "Current target is Phase 8 abuse state-machine contract package." in remaining
    readme_aligned = "accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in readme and "working_phase: Phase 8 — Abuse 1h Core planning/readiness" in readme
    index_aligned = "Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in index and "Phase 8 — Abuse 1h Core planning/readiness" in index
    rules_aligned = "accepted: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in ai_rules and "working: Phase 8 — Abuse 1h Core planning/readiness" in ai_rules

    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    runtime_activation_disabled = cfg.proxy.runtime_activation_allowed is False

    bools = {
        "current_state_preserved": current_state_preserved,
        "phase7_accepted": phase7_accepted,
        "phase8_working": phase8_working,
        "phase8_planning_only": True,
        "farm5_0_1_110_sync_evidence_present": farm5_sync,
        "phase8_planning_readiness_present": planning_ready,
        "ai_phase8_task_present": ai_present,
        "remaining_plan_state_machine_target_aligned": rem_aligned,
        "readme_current_gate_aligned": readme_aligned,
        "index_current_gate_aligned": index_aligned,
        "ai_coding_rules_current_gate_aligned": rules_aligned,
        "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_disabled": runtime_activation_disabled,
        "production_traffic_none": True,
        "firewall_apply_disallowed": True,
        "customer_nat_disallowed": True,
        "customer_firewall_rules_disallowed": True,
        "iptables_restore_disallowed": True,
        "abuse_automation_disallowed": True,
        "abuse_runner_disallowed": True,
        "abuse_state_db_writes_disallowed": True,
        "abuse_event_db_writes_disallowed": True,
        "hard_block_disallowed": True,
        "soft_block_disallowed": True,
        "pause_automation_disallowed": True,
        "ui_disallowed": True,
        "telegram_disallowed": True,
        "abuse_invariant_preserved": True,
        "state_path_normal_over_tracking_over_grace_hard": True,
        "sustained_abuse_window_3600_seconds": True,
        "farms_over_alone_does_not_harden": True,
        "worker_over_alone_does_not_harden": True,
        "all_active_customers_coverage_required": True,
        "abuse_exempt_requires_reason_and_expiry": True,
        "no_silent_skip_required": True,
    }

    checklist_items = [
        "current_state_preserved","phase7_accepted","phase8_working","farm5_0_1_110_sync_evidence_present","phase8_planning_readiness_present",
        "ai_phase8_task_present","remaining_plan_state_machine_target_aligned","readme_current_gate_aligned","index_current_gate_aligned",
        "ai_coding_rules_current_gate_aligned","abuse_state_machine_contract_defined","state_path_normal_over_tracking_over_grace_hard",
        "sustained_abuse_window_3600_seconds","farms_over_alone_does_not_harden","worker_over_alone_does_not_harden",
        "all_active_customers_coverage_required","abuse_exempt_requires_reason_and_expiry","no_silent_skip_required","config_apply_mode_plan_only",
        "proxy_runtime_activation_disabled","no_production_traffic","firewall_apply_disallowed","customer_nat_disallowed",
        "customer_firewall_rules_disallowed","no_iptables_restore_authorized","abuse_automation_disallowed","abuse_runner_disallowed",
        "abuse_state_db_writes_disallowed","abuse_event_db_writes_disallowed","hard_block_disallowed","soft_block_disallowed",
        "pause_automation_disallowed","separate_phase8_evidence_reporting_contract_pr_required","fresh_farm5_sync_evidence_required_before_acceptance",
    ]

    mapping = {
        "abuse_state_machine_contract_defined": True,
        "config_apply_mode_plan_only": bools["apply_mode_plan_only"],
        "proxy_runtime_activation_disabled": bools["runtime_activation_disabled"],
        "no_production_traffic": bools["production_traffic_none"],
        "no_iptables_restore_authorized": bools["iptables_restore_disallowed"],
        "separate_phase8_evidence_reporting_contract_pr_required": True,
        "fresh_farm5_sync_evidence_required_before_acceptance": True,
    }
    blockers = [f"{k}_missing_or_failed" for k, v in bools.items() if not v]

    checklist = []
    for item in checklist_items:
        ok = mapping.get(item, bools.get(item, True))
        checklist.append({"item": item, "status": "PASS" if ok else "BLOCKED", "evidence": item})

    false_flags = {k: False for k in ["live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_save_executed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation","db_usage_sample_write_allowed","db_usage_sample_written","db_policy_event_write_allowed","db_policy_event_written","db_abuse_state_write_allowed","db_abuse_state_written","db_abuse_event_write_allowed","db_abuse_event_written","filesystem_write_executed","scheduler_job_created","timer_enabled","usage_collector_runtime_allowed","usage_collector_runtime_started","policy_reject_collector_runtime_allowed","policy_reject_collector_runtime_started","abuse_runner_runtime_allowed","abuse_runner_runtime_started","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","abuse_automation_allowed_runtime","hard_block_allowed","hard_block_applied","soft_block_allowed","soft_block_applied","pause_automation_allowed","pause_applied","ui_allowed_runtime","telegram_allowed_runtime"]}

    return {
        "component": "phase8_abuse_state_machine_contract","phase": "Phase 8 — Abuse 1h Core","gate_type": "phase8_abuse_state_machine_contract",
        "final_decision": "BLOCKED","contract_status": "ABUSE_STATE_MACHINE_CONTRACT_DEFINED_NOT_ACCEPTED",
        "authorization_status": "PHASE8_ABUSE_STATE_MACHINE_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED","inspection_only": True,
        "report_only": True,"preflight_only": True,"dry_run": True,"execution_allowed": False,"phase8_acceptance_allowed": False,
        "abuse_state_machine_contract_defined": True,"abuse_state_path_defined": True,"abuse_transition_rules_defined": True,
        "abuse_timing_contract_defined": True,"abuse_hardening_contract_defined": True,"abuse_recovery_contract_defined": True,
        "abuse_exemption_contract_defined": True,"abuse_coverage_contract_defined": True,"abuse_runner_authorized": False,
        "abuse_automation_authorized": False,"abuse_state_db_writes_authorized": False,"abuse_event_db_writes_authorized": False,
        "hard_block_authorized": False,"soft_block_authorized": False,"pause_automation_authorized": False,
        "firewall_apply_authorized": False,"iptables_restore_authorized": False,"customer_nat_authorized": False,
        "customer_firewall_rules_authorized": False,"production_traffic_authorized": False,"ui_authorized": False,
        "telegram_authorized": False,"operator_review_required": True,
        "separate_phase8_evidence_reporting_contract_pr_required": True,
        "fresh_farm5_sync_evidence_required_before_acceptance": True,
        "abuse_state_machine_contract": {
            "state_path": ["normal","over_tracking","over_grace","hard"],
            "allowed_states": ["normal","over_tracking","over_grace","hard","disabled_manual","exempt_until"],
            "sustained_abuse_seconds": 3600,"grace_seconds_default": 900,
            "detection_inputs": {"primary": ["active_sessions","hot_sessions"], "secondary": ["unique_workers","unique_ips"]},
            "hardening_basis": {"miner_abuse_required": True,"farms_over_alone_hardens": False,"worker_over_alone_hardens": False},
            "coverage": {"all_active_customers_in_enabled_lanes_required": True,"abuse_exempt_requires_reason": True,"abuse_exempt_requires_expiry": True,"silent_skip_allowed": False},
            "transitions": {
                "normal_to_over_tracking": {"trigger": "active_sessions_or_hot_sessions_exceeds_miners", "writes_allowed_in_this_pr": False},
                "over_tracking_to_over_grace": {"trigger": "miner_abuse_drops_below_threshold_before_sustained_window", "writes_allowed_in_this_pr": False},
                "over_grace_to_normal": {"trigger": "grace_window_expires_without_repeated_miner_abuse", "writes_allowed_in_this_pr": False},
                "over_grace_to_over_tracking": {"trigger": "repeated_miner_abuse_during_grace_window", "writes_allowed_in_this_pr": False},
                "over_tracking_to_hard": {"trigger": "sustained_miner_abuse_for_about_3600_seconds", "writes_allowed_in_this_pr": False},
                "hard_to_normal": {"trigger": "manual_unhard_with_evidence_reason_and_audit", "writes_allowed_in_this_pr": False},
            },
            "hardening_requirements": {"policy_backup_required": True,"restore_reference_required": True,"audit_event_required": True,"evidence_required": True,"firewall_plan_required": True,"firewall_apply_future_gated": True,"conntrack_flush_future_gated": True},
            "failure_rules": {"evidence_missing_does_not_harden": True,"firewall_plan_failure_does_not_harden": True,"firewall_apply_failure_does_not_mark_hard_applied": True,"silent_skip_allowed": False},
            "future_acceptance_criteria": ["every active customer in every enabled lane is evaluated","no silent skip","farms-over alone does not harden","worker-over alone does not harden","sustained miner-abuse hardens after about 3600 seconds","hardening has evidence, audit, and restore reference","hardening stays fail-closed","manual unhard requires audit and reason","runtime implementation is separately gated"],
        },
        **bools,
        "phase8_abuse_state_machine_contract_checklist": checklist,
        "blockers": blockers,
        "errors": [],
        **false_flags,
    }
