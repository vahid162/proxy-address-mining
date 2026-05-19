from __future__ import annotations

from mpf.domain.production import CanaryPlanRequest


def build_phase11_canary_plan_report(request: CanaryPlanRequest) -> dict[str, object]:
    errors = request.validate()
    final_decision = "PLAN_READY_REPORT_ONLY" if not errors else "BLOCKED"

    return {
        "component": "phase11_canary_plan",
        "phase": "Phase 11B — CLI canary plan/report only",
        "final_decision": final_decision,
        "authorization_status": "REPORT_ONLY_NON_AUTHORIZING",
        "execution_allowed": False,
        "report_only": True,
        "mutation_performed": False,
        "canary_intent": {
            "customer_key": request.customer_key,
            "lane": request.lane,
            "port": request.port,
            "name": request.name,
            "policy": {
                "miners": request.miners,
                "farms": request.farms,
                "maxconn": request.maxconn,
                "rate_per_min": request.rate_per_min,
                "burst": request.burst,
                "ips_mode": request.ips_mode,
                "ip_whitelist": request.ip_whitelist,
            },
            "operator": request.operator,
            "reason": request.reason,
        },
        "gate": {
            "phase11a_readiness_required": True,
            "farm5_phase11a_evidence_required_before_acceptance": True,
            "controlled_apply_required_later": True,
            "manual_operator_acceptance_required_later": True,
        },
        "preview": {
            "would_create_customer": True,
            "would_create_policy": True,
            "would_generate_firewall_desired_model": True,
            "would_generate_customer_nat_preview": True,
            "would_generate_customer_firewall_rules_preview": True,
            "would_require_restore_point_before_apply": True,
            "would_require_iptables_save_backup_before_apply": True,
            "would_require_lock_before_apply": True,
            "would_require_verify_after_apply": True,
            "would_require_rollback_or_restore_plan": True,
        },
        "safety_flags": {
            "production_traffic_authorized": False,
            "controlled_cli_canary_execution_authorized": False,
            "limited_customer_onboarding_authorized": False,
            "firewall_apply_authorized": False,
            "iptables_restore_authorized": False,
            "customer_nat_apply_authorized": False,
            "customer_firewall_rules_apply_authorized": False,
            "abuse_automation_authorized": False,
            "conntrack_flush_authorized": False,
            "worker_enforcement_authorized": False,
            "scheduler_authorized": False,
            "collector_authorized": False,
            "ui_authorized": False,
            "telegram_authorized": False,
        },
        "operator_checklist": [
            "sync latest GitHub main to farm5",
            "run mpf production readiness --output json",
            "verify mpf doctor",
            "verify phase gate",
            "review canary plan",
            "do not apply until Phase 11C controlled harness is accepted",
            "do not connect a real miner until Phase 11D manual canary acceptance gate",
        ],
        "blockers": [
            "farm5 Phase 11A sync/test evidence required before accepting Phase 11B",
            "actual canary execution remains forbidden until Phase 11C/11D gates",
            "firewall apply remains forbidden until controlled apply harness",
            "customer NAT/customer firewall rules remain preview-only",
            "production traffic remains none",
        ],
        "validation_errors": errors,
        "next_required_step": "Merge PR, optionally batch with Phase 11A, sync to farm5, run readiness and canary-plan evidence commands, then record farm5 evidence before Phase 11C.",
    }
