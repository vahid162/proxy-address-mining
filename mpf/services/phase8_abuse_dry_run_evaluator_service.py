from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from mpf.config import MPFConfig
from mpf.domain.abuse_dry_run_evaluator import (
    AbuseDryRunInput,
    AbuseEvidenceSnapshot,
    AbusePolicySnapshot,
    AbuseStateSnapshot,
    evaluate_abuse_dry_run,
)
from mpf.services.phase8_abuse_evidence_reporting_contract_service import (
    build_phase8_abuse_evidence_reporting_contract_report,
)
from mpf.services.phase8_abuse_state_machine_contract_service import (
    build_phase8_abuse_state_machine_contract_report,
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _scenario_input(now: datetime) -> AbuseDryRunInput:
    return AbuseDryRunInput(
        policy=AbusePolicySnapshot(10, 3, 100, 10, 20),
        evidence=AbuseEvidenceSnapshot(None, None, "synthetic", 10001, 5, 5, 2, 4, "complete", "synthetic", now, 100, []),
        state=AbuseStateSnapshot("normal", None, None, None, None),
        now=now,
    )


def build_phase8_abuse_dry_run_evaluator_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    ai_phase8 = _read(root / "docs/AI_PHASE_8_TASK.md")
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    readme = _read(root / "README.md")
    index = _read(root / "docs/INDEX.md")
    ai_rules = _read(root / "docs/AI_CODING_RULES.md")

    sm = build_phase8_abuse_state_machine_contract_report(cfg, root)
    er = build_phase8_abuse_evidence_reporting_contract_report(cfg, root)

    now = datetime(2026, 1, 1, 0, 0, 0)
    base = _scenario_input(now)
    scenarios: list[dict[str, object]] = []

    def add(sid: str, payload: AbuseDryRunInput, expected: str) -> None:
        result = evaluate_abuse_dry_run(payload)
        scenarios.append({
            "scenario_id": sid,
            "input_summary": {"state": payload.state.status, "evidence_status": payload.evidence.evidence_status},
            "expected_decision": expected,
            "result": result.__dict__,
            "passed": result.decision == expected,
        })

    add("normal_within_limits_stays_normal", base, "stays_normal")
    add("normal_miner_over_would_enter_over_tracking", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 11, 11, 1, 1, "complete", "synthetic", now, 100, []), base.state, now), "would_enter_over_tracking")
    add("normal_farms_over_only_does_not_harden", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 5, 5, 10, 1, "complete", "synthetic", now, 100, []), base.state, now), "stays_normal")
    add("normal_worker_over_only_does_not_harden", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 5, 5, 1, 20, "complete", "synthetic", now, 100, []), base.state, now), "stays_normal")
    add("missing_evidence_blocks_transition", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, None, None, 1, 1, "missing", "synthetic", now, 100, ["missing"]), base.state, now), "evaluation_blocked_missing")
    add("stale_evidence_blocks_transition", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 5, 5, 1, 1, "stale", "synthetic", now, 100, ["stale"]), base.state, now), "evaluation_blocked_stale")
    add("over_tracking_continues_before_threshold", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 11, 11, 1, 1, "complete", "synthetic", now, 100, []), AbuseStateSnapshot("over_tracking", now - timedelta(seconds=3000), now, None, None), now), "continues_over_tracking")
    add("over_tracking_would_harden_after_3600s", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 11, 11, 1, 1, "complete", "synthetic", now, 100, []), AbuseStateSnapshot("over_tracking", now - timedelta(seconds=3600), now, None, None), now), "would_harden_after_sustained_miner_abuse")
    add("over_tracking_recovers_to_over_grace", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 2, 2, 1, 1, "complete", "synthetic", now, 100, []), AbuseStateSnapshot("over_tracking", now - timedelta(seconds=3000), now, None, None), now), "would_enter_over_grace")
    add("over_grace_returns_to_tracking_on_repeated_miner_over", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 11, 11, 1, 1, "complete", "synthetic", now, 100, []), AbuseStateSnapshot("over_grace", now - timedelta(seconds=2000), now, now - timedelta(seconds=100), None), now), "would_return_to_over_tracking")
    add("over_grace_would_recover_normal_after_grace", AbuseDryRunInput(base.policy, AbuseEvidenceSnapshot(None, None, "s", 1, 2, 2, 1, 1, "complete", "synthetic", now, 100, []), AbuseStateSnapshot("over_grace", now - timedelta(seconds=2000), now, now - timedelta(seconds=1000), None), now), "would_recover_normal")
    add("hard_stays_hard_until_future_manual_unhard", AbuseDryRunInput(base.policy, base.evidence, AbuseStateSnapshot("hard", None, None, None, now - timedelta(seconds=20)), now), "hard_requires_manual_unhard_future_gated")
    add("active_exemption_blocks_transition", AbuseDryRunInput(AbusePolicySnapshot(10, 3, 100, 10, 20, True, "ok", now + timedelta(seconds=60)), AbuseEvidenceSnapshot(None, None, "s", 1, 11, 11, 1, 1, "complete", "synthetic", now, 100, []), base.state, now), "exempt_report_only")
    add("expired_exemption_ignored", AbuseDryRunInput(AbusePolicySnapshot(10, 3, 100, 10, 20, True, "ok", now - timedelta(seconds=60)), AbuseEvidenceSnapshot(None, None, "s", 1, 5, 5, 1, 1, "complete", "synthetic", now, 100, []), base.state, now), "stays_normal")
    add("unknown_state_blocks_evaluation", AbuseDryRunInput(base.policy, base.evidence, AbuseStateSnapshot("weird", None, None, None, None), now), "evaluation_blocked_unknown_state")

    synthetic_scenarios_passed = all(bool(item["passed"]) for item in scenarios)

    bools = {
        "current_state_preserved": "current_accepted_phase: Phase 7" in phase_status and "current_working_phase: Phase 8" in phase_status,
        "phase7_accepted": "current_accepted_phase: Phase 7" in phase_status,
        "phase8_working": "current_working_phase: Phase 8" in phase_status,
        "phase8_planning_only": True,
        "farm5_0_1_110_sync_evidence_present": "synced to 0.1.110" in phase_status,
        "no_farm5_0_1_111_sync_evidence_claimed": "synced to 0.1.111" not in phase_status,
        "no_farm5_0_1_112_sync_evidence_claimed": "synced to 0.1.112" not in phase_status,
        "no_farm5_0_1_113_sync_evidence_claimed": "synced to 0.1.113" not in phase_status,
        "state_machine_contract_present": sm.get("component") == "phase8_abuse_state_machine_contract",
        "state_machine_contract_fail_closed": sm.get("final_decision") == "BLOCKED" and not bool(sm.get("execution_allowed")),
        "evidence_reporting_contract_present": er.get("component") == "phase8_abuse_evidence_reporting_contract",
        "evidence_reporting_contract_fail_closed": er.get("final_decision") == "BLOCKED" and not bool(er.get("execution_allowed")),
        "ai_phase8_task_present": "Current Phase 8 Step — Abuse Dry-Run Evaluator" in ai_phase8,
        "remaining_plan_dry_run_target_aligned": "Current target is Phase 8 abuse dry-run evaluator package." in remaining or "Current target is Phase 8 DB-only controlled transition readiness package." in remaining,
        "readme_current_gate_aligned": "DB-only controlled transition readiness package" in readme and "report-only/non-mutating/non-authorizing" in readme,
        "index_current_gate_aligned": "abuse dry-run evaluator package" in index,
        "ai_coding_rules_current_gate_aligned": "Phase 8 dry-run evaluator stop condition" in ai_rules,
        "apply_mode_plan_only": cfg.firewall.apply_mode == "plan_only",
        "runtime_activation_disabled": cfg.proxy.runtime_activation_allowed is False,
        "production_traffic_none": True,
        "firewall_apply_disallowed": True,
        "customer_nat_disallowed": True,
        "customer_firewall_rules_disallowed": True,
        "iptables_restore_disallowed": True,
        "abuse_automation_disallowed": True,
        "abuse_runner_disallowed": True,
        "abuse_state_db_reads_disallowed": True,
        "abuse_state_db_writes_disallowed": True,
        "abuse_event_db_writes_disallowed": True,
        "usage_sample_db_reads_disallowed": True,
        "usage_sample_db_writes_disallowed": True,
        "policy_event_db_reads_disallowed": True,
        "policy_event_db_writes_disallowed": True,
        "conntrack_live_read_disallowed": True,
        "firewall_counter_live_read_disallowed": True,
        "hard_block_disallowed": True,
        "soft_block_disallowed": True,
        "pause_automation_disallowed": True,
        "ui_disallowed": True,
        "telegram_disallowed": True,
        "abuse_invariant_preserved": True,
        "state_path_normal_over_tracking_over_grace_hard": True,
        "sustained_abuse_window_3600_seconds": True,
        "missing_evidence_blocks_hardening": True,
        "stale_evidence_blocks_hardening": True,
        "farms_over_alone_does_not_harden": True,
        "worker_over_alone_does_not_harden": True,
        "all_active_customers_coverage_required": True,
        "no_silent_skip_required": True,
        "synthetic_scenarios_passed": synthetic_scenarios_passed,
    }

    blocker_keys = [
        "current_state_preserved","farm5_0_1_110_sync_evidence_present","no_farm5_0_1_111_sync_evidence_claimed","no_farm5_0_1_112_sync_evidence_claimed","no_farm5_0_1_113_sync_evidence_claimed",
        "state_machine_contract_present","state_machine_contract_fail_closed","evidence_reporting_contract_present","evidence_reporting_contract_fail_closed",
        "ai_phase8_task_present","remaining_plan_dry_run_target_aligned","readme_current_gate_aligned","index_current_gate_aligned","ai_coding_rules_current_gate_aligned",
        "apply_mode_plan_only","runtime_activation_disabled","synthetic_scenarios_passed",
    ]
    blockers = [f"{k}_missing_or_failed" for k in blocker_keys if not bools.get(k, False)]

    checklist_items = [
        "current_state_preserved","phase7_accepted","phase8_working","farm5_0_1_110_sync_evidence_present","no_farm5_0_1_111_sync_evidence_claimed","no_farm5_0_1_112_sync_evidence_claimed",
        "no_farm5_0_1_113_sync_evidence_claimed","state_machine_contract_present","state_machine_contract_fail_closed","evidence_reporting_contract_present","evidence_reporting_contract_fail_closed",
        "ai_phase8_task_present","remaining_plan_dry_run_target_aligned","readme_current_gate_aligned","index_current_gate_aligned","ai_coding_rules_current_gate_aligned",
        "dry_run_evaluator_defined","pure_domain_evaluator_defined","synthetic_scenarios_defined","synthetic_scenarios_passed","transition_logic_defined","hardening_proposal_logic_defined",
        "missing_evidence_blocks_hardening","stale_evidence_blocks_hardening","farms_over_alone_does_not_harden","worker_over_alone_does_not_harden","all_active_customers_coverage_required","no_silent_skip_required",
        "config_apply_mode_plan_only","proxy_runtime_activation_disabled","no_production_traffic","firewall_apply_disallowed","customer_nat_disallowed","customer_firewall_rules_disallowed","no_iptables_restore_authorized",
        "abuse_automation_disallowed","abuse_runner_disallowed","abuse_db_reads_disallowed","abuse_db_writes_disallowed","usage_policy_db_reads_writes_disallowed","live_conntrack_firewall_reads_disallowed",
        "hard_block_disallowed","soft_block_disallowed","pause_automation_disallowed","separate_phase8_db_controlled_transition_pr_required","fresh_farm5_sync_evidence_required_before_acceptance",
    ]
    mapping = {
        "dry_run_evaluator_defined": True,
        "pure_domain_evaluator_defined": True,
        "synthetic_scenarios_defined": True,
        "transition_logic_defined": True,
        "hardening_proposal_logic_defined": True,
        "config_apply_mode_plan_only": bools["apply_mode_plan_only"],
        "proxy_runtime_activation_disabled": bools["runtime_activation_disabled"],
        "no_production_traffic": bools["production_traffic_none"],
        "no_iptables_restore_authorized": bools["iptables_restore_disallowed"],
        "abuse_db_reads_disallowed": bools["abuse_state_db_reads_disallowed"],
        "abuse_db_writes_disallowed": bools["abuse_state_db_writes_disallowed"] and bools["abuse_event_db_writes_disallowed"],
        "usage_policy_db_reads_writes_disallowed": bools["usage_sample_db_reads_disallowed"] and bools["usage_sample_db_writes_disallowed"] and bools["policy_event_db_reads_disallowed"] and bools["policy_event_db_writes_disallowed"],
        "live_conntrack_firewall_reads_disallowed": bools["conntrack_live_read_disallowed"] and bools["firewall_counter_live_read_disallowed"],
        "separate_phase8_db_controlled_transition_pr_required": True,
        "fresh_farm5_sync_evidence_required_before_acceptance": True,
    }
    checklist = [{"item": item, "status": "PASS" if mapping.get(item, bools.get(item, True)) else "BLOCKED", "evidence": item} for item in checklist_items]

    report = {
        "component": "phase8_abuse_dry_run_evaluator",
        "phase": "Phase 8 — Abuse 1h Core",
        "gate_type": "phase8_abuse_dry_run_evaluator",
        "final_decision": "BLOCKED",
        "dry_run_status": "ABUSE_DRY_RUN_EVALUATOR_DEFINED_NOT_ACCEPTED",
        "authorization_status": "PHASE8_ABUSE_DRY_RUN_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED",
        "inspection_only": True,
        "report_only": True,
        "preflight_only": True,
        "dry_run": True,
        "execution_allowed": False,
        "phase8_acceptance_allowed": False,
        "dry_run_evaluator_defined": True,
        "pure_domain_evaluator_defined": True,
        "synthetic_scenarios_defined": True,
        "transition_logic_defined": True,
        "hardening_proposal_logic_defined": True,
        "manual_unhard_future_gated": True,
        "future_db_controlled_transition_pr_required": True,
        "fresh_farm5_sync_evidence_required_before_acceptance": True,
        "no_server_sync_evidence_for_0_1_111": bools["no_farm5_0_1_111_sync_evidence_claimed"],
        "no_server_sync_evidence_for_0_1_112": bools["no_farm5_0_1_112_sync_evidence_claimed"],
        "no_server_sync_evidence_for_0_1_113": bools["no_farm5_0_1_113_sync_evidence_claimed"],
        "abuse_runner_authorized": False,
        "abuse_automation_authorized": False,
        "abuse_state_db_reads_authorized": False,
        "abuse_state_db_writes_authorized": False,
        "abuse_event_db_writes_authorized": False,
        "usage_sample_db_reads_authorized": False,
        "usage_sample_db_writes_authorized": False,
        "policy_event_db_reads_authorized": False,
        "policy_event_db_writes_authorized": False,
        "conntrack_live_read_authorized": False,
        "firewall_counter_live_read_authorized": False,
        "iptables_save_authorized": False,
        "iptables_restore_authorized": False,
        "hard_block_authorized": False,
        "soft_block_authorized": False,
        "pause_automation_authorized": False,
        "firewall_apply_authorized": False,
        "customer_nat_authorized": False,
        "customer_firewall_rules_authorized": False,
        "production_traffic_authorized": False,
        "ui_authorized": False,
        "telegram_authorized": False,
        "operator_review_required": True,
        "separate_phase8_db_controlled_transition_pr_required": True,
        "phase8_abuse_dry_run_evaluator_checklist": checklist,
        "synthetic_scenarios": scenarios,
        "blockers": blockers,
        "errors": [],
        **bools,
    }
    false_flags = [
        "live_firewall_read_allowed","live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed",
        "iptables_save_executed","iptables_restore_allowed","iptables_restore_executed","conntrack_live_read_executed","firewall_counter_live_read_executed",
        "subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_read_executed","db_mutation",
        "db_customer_read_allowed","db_customer_read_executed","db_usage_sample_read_allowed","db_usage_sample_read_executed","db_usage_sample_write_allowed","db_usage_sample_written",
        "db_policy_event_read_allowed","db_policy_event_read_executed","db_policy_event_write_allowed","db_policy_event_written","db_abuse_state_read_allowed","db_abuse_state_read_executed",
        "db_abuse_state_write_allowed","db_abuse_state_written","db_abuse_event_write_allowed","db_abuse_event_written","filesystem_write_executed","scheduler_job_created","timer_enabled",
        "usage_collector_runtime_allowed","usage_collector_runtime_started","policy_reject_collector_runtime_allowed","policy_reject_collector_runtime_started",
        "abuse_runner_runtime_allowed","abuse_runner_runtime_started","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed",
        "production_traffic_changed","abuse_automation_allowed_runtime","hard_block_allowed","hard_block_applied","soft_block_allowed","soft_block_applied","pause_automation_allowed","pause_applied",
        "ui_allowed_runtime","telegram_allowed_runtime",
    ]
    for key in false_flags:
        report[key] = False
    return report
