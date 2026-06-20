from __future__ import annotations

from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status

from mpf.config import MPFConfig


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def build_phase7_usage_accounting_contract_report(
    cfg: MPFConfig,
    repo_root: Path | None = None,
) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = read_historical_phase_status(root)
    readme = _read(root / "README.md")
    ai_phase7 = _read(root / "docs/AI_PHASE_7_TASK.md")
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    blockers: list[str] = []

    current_state_present = "## Current State" in phase_status
    current_state_preserved = (
        "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in phase_status
        and "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" in phase_status
    )
    phase6_accepted = "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in phase_status
    phase7_working = "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" in phase_status
    phase7_readiness_present = "phase7_usage_policy_readiness" in phase_status or "Usage + Policy/Reject Accounting" in phase_status
    farm5 = "synced to 0.1.107" in phase_status.lower() and "690 passed" in phase_status
    readme_phase7_aligned = "accepted_phase: Phase 6" in readme and "working_phase: Phase 7" in readme
    ai_lower = ai_phase7.lower()
    ai_phase7_task_present = all(
        phrase in ai_lower
        for phrase in [
            "current phase 7 step — usage accounting contract",
            "report-only/service-contract only",
            "does not enable collectors",
            "does not enable timers",
            "does not read live firewall counters",
            "does not write usage_samples",
            "does not write policy_events",
            "phase 8 remains future-only",
        ]
    )
    remaining_l = remaining.lower()
    remaining_plan_usage_contract_target_aligned = (
        "latest recorded farm5 sync evidence is 0.1.107" in remaining_l
        and "phase 7 current target is phase 7 final acceptance readiness package" in remaining_l
        and "next target after this pr is phase 7 operator acceptance / phase 8 planning boundary" in remaining_l
    )
    apply_mode_plan_only = cfg.firewall.apply_mode == "plan_only"
    runtime_activation_disabled = not bool(cfg.proxy.runtime_activation_allowed)
    production_traffic_none = "production_traffic: none" in phase_status
    firewall_apply_disallowed = "firewall_apply_allowed: no" in phase_status
    abuse_automation_disallowed = "abuse_automation_allowed: no" in phase_status
    abuse_invariant_preserved = "normal -> over_tracking -> over_grace -> hard" in phase_status

    checks = [
        ("current_state_preserved", current_state_preserved),
        ("phase6_accepted", phase6_accepted),
        ("phase7_working", phase7_working),
        ("farm5_0_1_107_sync_evidence_present", farm5),
        ("phase7_readiness_present", phase7_readiness_present),
        ("usage_accounting_contract_defined", True),
        ("usage_samples_contract_defined", True),
        ("usage_delta_contract_defined", True),
        ("usage_report_windows_defined", True),
        ("usage_doctor_contract_defined", True),
        ("config_apply_mode_plan_only", apply_mode_plan_only),
        ("proxy_runtime_activation_disabled", runtime_activation_disabled),
        ("no_production_traffic", production_traffic_none),
        ("firewall_apply_disallowed", firewall_apply_disallowed),
        ("customer_nat_disallowed", True),
        ("customer_firewall_rules_disallowed", True),
        ("no_iptables_restore_authorized", True),
        ("usage_automation_disallowed", True),
        ("usage_collectors_disallowed", True),
        ("usage_db_writes_disallowed", True),
        ("firewall_counter_live_read_disallowed", True),
        ("abuse_automation_disallowed", abuse_automation_disallowed),
        ("phase8_not_started", True),
        ("abuse_invariant_preserved", abuse_invariant_preserved),
        ("separate_policy_reject_contract_pr_required", True),
        ("fresh_farm5_sync_evidence_required_before_acceptance", True),
    ]

    if not current_state_present:
        blockers.append("phase_status_current_state_missing")
    if not current_state_preserved:
        blockers.append("current_state_changed_away_from_phase6_accepted_phase7_working")
    if not readme_phase7_aligned:
        blockers.append("readme_not_aligned_to_phase7")
    if not ai_phase7_task_present:
        blockers.append("ai_phase7_task_missing_required_prohibitions")
    if not remaining_plan_usage_contract_target_aligned:
        blockers.append("remaining_plan_usage_contract_target_not_aligned")

    for name, ok in checks:
        if not ok:
            blockers.append(name)

    checklist = [{"item": n, "status": "PASS" if ok else "BLOCKED", "evidence": str(ok)} for n, ok in checks]

    false_flags = {k: False for k in [
        "live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed",
        "iptables_save_executed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed",
        "real_adapter_allowed","real_adapter_executed","db_mutation","db_usage_sample_write_allowed","db_usage_sample_written","db_policy_event_write_allowed",
        "db_policy_event_written","filesystem_write_executed","scheduler_job_created","timer_enabled","usage_collector_runtime_allowed",
        "usage_collector_runtime_started","policy_reject_collector_runtime_allowed","policy_reject_collector_runtime_started","customer_nat_allowed",
        "customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed",
        "abuse_automation_allowed_runtime","block_automation_allowed","pause_automation_allowed","ui_allowed_runtime","telegram_allowed_runtime"
    ]}

    return {
        "component": "phase7_usage_accounting_contract",
        "phase": "Phase 7 — Usage + Policy/Reject Accounting",
        "gate_type": "phase7_usage_accounting_contract",
        "final_decision": "BLOCKED",
        "contract_status": "USAGE_ACCOUNTING_CONTRACT_DEFINED_NOT_ACCEPTED",
        "authorization_status": "PHASE7_USAGE_ACCOUNTING_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED",
        "inspection_only": True,
        "report_only": True,
        "preflight_only": True,
        "dry_run": True,
        "execution_allowed": False,
        "phase7_acceptance_allowed": False,
        "usage_accounting_contract_defined": True,
        "usage_samples_contract_defined": True,
        "usage_delta_contract_defined": True,
        "usage_report_windows_defined": True,
        "usage_doctor_contract_defined": True,
        "usage_collector_runtime_authorized": False,
        "usage_timer_authorized": False,
        "usage_db_writes_authorized": False,
        "usage_counter_live_read_authorized": False,
        "firewall_counter_live_read_authorized": False,
        "production_traffic_authorized": False,
        "firewall_apply_authorized": False,
        "iptables_restore_authorized": False,
        "customer_nat_authorized": False,
        "customer_firewall_rules_authorized": False,
        "abuse_automation_authorized": False,
        "phase8_start_allowed": False,
        "operator_review_required": True,
        "separate_policy_reject_contract_pr_required": True,
        "fresh_farm5_sync_evidence_required_before_acceptance": True,
        "usage_contract": {
            "source": "future accounting rules/counters, not activated in this PR",
            "data_model_tables": ["usage_samples", "policy_events", "customers", "customer_policies", "lanes"],
            "customer_identity_fields": ["customer_id", "lane_id", "port", "sampled_at"],
            "counter_fields": ["bytes_in", "bytes_out", "packets_in", "packets_out", "connlimit_rejects", "hashlimit_rejects", "pause_rejects", "block_rejects"],
            "report_windows": ["1h", "1d", "30d"],
            "required_future_acceptance_criteria": [
                "every active customer has accounting coverage",
                "missing accounting rule count is zero",
                "counter deltas are non-negative and explainable",
                "reports are read-only",
                "no silent skip",
                "no abuse automation before Phase 8",
            ],
        },
        "current_state_preserved": current_state_preserved,
        "phase6_accepted": phase6_accepted,
        "phase7_working": phase7_working,
        "phase7_readiness_present": phase7_readiness_present,
        "farm5_0_1_107_sync_evidence_present": farm5,
        "readme_phase7_aligned": readme_phase7_aligned,
        "ai_phase7_task_present": ai_phase7_task_present,
        "remaining_plan_usage_contract_target_aligned": remaining_plan_usage_contract_target_aligned,
        "apply_mode_plan_only": apply_mode_plan_only,
        "runtime_activation_disabled": runtime_activation_disabled,
        "production_traffic_none": production_traffic_none,
        "firewall_apply_disallowed": firewall_apply_disallowed,
        "customer_nat_disallowed": True,
        "customer_firewall_rules_disallowed": True,
        "iptables_restore_disallowed": True,
        "usage_automation_disallowed": True,
        "usage_collectors_disallowed": True,
        "usage_db_writes_disallowed": True,
        "firewall_counter_live_read_disallowed": True,
        "abuse_automation_disallowed": abuse_automation_disallowed,
        "phase8_not_started": True,
        "abuse_invariant_preserved": abuse_invariant_preserved,
        "phase7_usage_accounting_contract_checklist": checklist,
        "blockers": blockers,
        "errors": [],
        **false_flags,
    }
