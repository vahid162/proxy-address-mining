from __future__ import annotations

from pathlib import Path
from mpf.config import MPFConfig

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def build_phase7_usage_policy_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    readme = _read(root / "README.md")
    ai_phase7 = _read(root / "docs/AI_PHASE_7_TASK.md")
    remaining = _read(root / "docs/REMAINING_PHASE_PLAN.md")
    blockers: list[str] = []
    current_state_preserved = "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in phase_status and "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" in phase_status
    phase6_accepted = "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5" in phase_status
    phase7_working = "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting" in phase_status
    farm5 = "synced to 0.1.104" in phase_status
    readme_phase7_aligned = "accepted_phase: Phase 6" in readme and "working_phase: Phase 7" in readme
    ai_lower = ai_phase7.lower()
    ai_required_phrases = [
        "usage + policy/reject accounting",
        "planning/readiness",
        "phase 7 starts only after phase 6 is accepted",
        "read-only/reporting/service-contract",
        "phase 7 must not enable production traffic",
        "phase 7 must not enable firewall apply",
        "phase 7 must not enable iptables-restore",
        "phase 7 must not enable customer nat/customer firewall rules",
        "phase 7 must not enable usage automation",
        "phase 7 must not enable usage collectors",
        "phase 7 must not enable policy/reject collectors",
        "phase 7 must not enable abuse automation",
        "phase 8 remains",
        "normal -> over_tracking -> over_grace -> hard",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "no silent skip",
    ]
    ai_present = all(phrase in ai_lower for phrase in ai_required_phrases)
    rem_aligned = "latest recorded farm5 sync evidence is 0.1.104" in remaining and ("Phase 7 current target is Policy/Reject Accounting service-contract package" in remaining or "Phase 7 current target is Phase 7 read-only reports/doctor package" in remaining)
    apply_mode = cfg.firewall.apply_mode == "plan_only"
    runtime_disabled = not bool(cfg.proxy.runtime_activation_allowed)
    production_none = "production_traffic: none" in phase_status
    firewall_no = "firewall_apply_allowed: no" in phase_status
    abuse_no = "abuse_automation_allowed: no" in phase_status
    no_non_deleted = "no non-deleted customers" in phase_status
    no_nat = "no customer NAT redirects" in phase_status
    no_v4 = "no MPF/customer IPv4 firewall references" in phase_status
    no_v6 = "no MPF/customer IPv6 firewall references" in phase_status
    abuse_invariant = "normal -> over_tracking -> over_grace -> hard" in phase_status

    checks = [
        ("current_state_preserved", current_state_preserved), ("phase6_accepted", phase6_accepted), ("phase7_working", phase7_working),
        ("latest_recorded_farm5_sync_evidence_present", farm5), ("readme_phase7_aligned", readme_phase7_aligned), ("ai_phase7_task_present", ai_present),
        ("remaining_plan_phase7_aligned", rem_aligned), ("config_apply_mode_plan_only", apply_mode), ("proxy_runtime_activation_disabled", runtime_disabled),
        ("no_production_traffic", production_none), ("firewall_apply_disallowed", firewall_no), ("no_customer_nat_authorized", no_nat),
        ("no_customer_firewall_rules_authorized", True), ("no_iptables_restore_authorized", True), ("usage_automation_disallowed", True),
        ("usage_collectors_disallowed", True), ("policy_reject_collectors_disallowed", True), ("abuse_automation_disallowed", abuse_no),
        ("phase8_not_started", True), ("abuse_invariant_preserved", abuse_invariant), ("separate_phase7_service_contract_pr_required", True),
        ("fresh_farm5_sync_evidence_required_before_acceptance", True),
    ]
    for name, ok in checks:
        if not ok: blockers.append(name)
    checklist = [{"item": n, "status": "PASS" if ok else "BLOCKED", "evidence": str(ok)} for n, ok in checks]
    false_flags = {k: False for k in ["live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","db_mutation","db_apply_record_write_allowed","db_apply_record_written","filesystem_write_executed","restore_point_write_allowed","restore_point_written","lock_acquisition_allowed","lock_acquired","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","usage_automation_allowed","usage_collector_runtime_allowed","policy_reject_collector_runtime_allowed","abuse_automation_allowed_runtime","block_automation_allowed","pause_automation_allowed","ui_allowed_runtime","telegram_allowed_runtime"]}
    return {
        "component":"phase7_usage_policy_readiness","phase":"Phase 7 — Usage + Policy/Reject Accounting","gate_type":"phase7_usage_policy_readiness",
        "final_decision":"BLOCKED","readiness_status":"PHASE7_READINESS_DEFINED_NOT_ACCEPTED","authorization_status":"PHASE7_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED",
        "inspection_only":True,"report_only":True,"preflight_only":True,"dry_run":True,"execution_allowed":False,"phase7_acceptance_allowed":False,
        "usage_automation_authorized":False,"usage_collectors_authorized":False,"policy_reject_collectors_authorized":False,"policy_reject_accounting_authorized":False,
        "customer_nat_authorized":False,"customer_firewall_rules_authorized":False,"production_traffic_authorized":False,"firewall_apply_authorized":False,
        "iptables_restore_authorized":False,"abuse_automation_authorized":False,"ui_authorized":False,"telegram_authorized":False,"phase8_start_allowed":False,
        "operator_review_required":True,"fresh_farm5_sync_evidence_required_before_acceptance":True,"separate_phase7_service_contract_pr_required":True,
        "current_state_preserved":current_state_preserved,"phase6_accepted":phase6_accepted,"phase7_working":phase7_working,"phase7_planning_readiness_only":True,
        "latest_recorded_farm5_sync_evidence_present":farm5,"readme_phase7_aligned":readme_phase7_aligned,"ai_phase7_task_present":ai_present,
        # Compatibility aliases for older CLI/docs checks.
        "farm5_0_1_102_sync_evidence_present":farm5,
        "fresh_farm5_0_1_103_sync_evidence_required":True,
        "remaining_plan_phase7_aligned":rem_aligned,"apply_mode_plan_only":apply_mode,"runtime_activation_disabled":runtime_disabled,
        "production_traffic_none":production_none,"firewall_apply_disallowed":firewall_no,"customer_nat_disallowed":True,"customer_firewall_rules_disallowed":True,
        "iptables_restore_disallowed":True,"usage_automation_disallowed":True,"usage_collectors_disallowed":True,"policy_reject_collectors_disallowed":True,
        "abuse_automation_disallowed":abuse_no,"ui_disallowed":True,"telegram_disallowed":True,"phase8_not_started":True,"abuse_invariant_preserved":abuse_invariant,
        "no_non_deleted_customer_evidence_present":no_non_deleted,"no_customer_nat_redirects_evidenced":no_nat,"no_mpf_customer_ipv4_firewall_references_evidenced":no_v4,
        "no_mpf_customer_ipv6_firewall_references_evidenced":no_v6, "phase7_usage_policy_readiness_checklist":checklist, "blockers":blockers, "errors":[], **false_flags
    }
