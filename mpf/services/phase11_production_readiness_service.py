from __future__ import annotations

from pathlib import Path

PHASE_STATUS_PATH = Path("docs/PHASE_STATUS.md")
AI_SAFE_RUNTIME_FIRST_PATH = Path("docs/AI_SAFE_RUNTIME_FIRST.md")
PRODUCTION_ACTIVATION_GATE_PATH = Path("docs/PRODUCTION_ACTIVATION_GATE.md")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_phase11_production_readiness_report() -> dict[str, object]:
    phase_status = _read(PHASE_STATUS_PATH)

    gate = {
        "accepted_phase": "Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5",
        "working_phase": "Phase 11 — Production / Customer Activation Gate planning/readiness",
        "production_traffic": "none",
        "firewall_apply_allowed": "no",
        "abuse_automation_allowed": "no",
        "customer_onboarding_allowed": "db_only",
        "proxy_data_plane_allowed": "limited_runtime_local_only",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "live_snapshot_read_allowed": "iptables_save_read_only",
        "restore_lock_record_execution_allowed": "controlled_boundary_only",
    }

    checks = {
        "phase10_accepted": gate["accepted_phase"] in phase_status,
        "phase11_working": gate["working_phase"] in phase_status,
        "phase11a_scope_defined": True,
        "ai_safe_runtime_first_present": AI_SAFE_RUNTIME_FIRST_PATH.exists(),
        "production_activation_gate_present": PRODUCTION_ACTIVATION_GATE_PATH.exists(),
        "cli_command_defined": True,
        "report_only": True,
        "fail_closed": True,
        "no_runtime_authorization": True,
    }

    blockers = [
        "farm5 sync/test evidence required after merge",
        "controlled CLI canary remains future Phase 11B/11C/11D gated",
        "firewall apply remains forbidden until explicit controlled gate",
        "customer onboarding remains db_only until canary gate evidence",
    ]

    return {
        "component": "phase11_production_readiness",
        "phase": "Phase 11A — Production readiness inventory",
        "final_decision": "READY_FOR_SERVER_SYNC_EVIDENCE" if checks["phase10_accepted"] and checks["phase11_working"] else "BLOCKED",
        "authorization_status": "REPORT_ONLY_NON_AUTHORIZING",
        "execution_allowed": False,
        "current_gate": gate,
        "required_evidence": {
            "github_main_version_known": True,
            "farm5_sync_test_required_after_merge": True,
            "pytest_required_on_farm5": True,
            "mpf_doctor_required": True,
            "phase_gate_required": True,
            "server_time_ntp_required": True,
            "restart_safety_required": True,
            "container_order_required": True,
            "proxy_doctor_required": True,
            "db_status_required": True,
        },
        "safety_flags": {
            "production_traffic_authorized": False,
            "controlled_cli_canary_authorized": False,
            "limited_customer_onboarding_authorized": False,
            "firewall_apply_authorized": False,
            "iptables_restore_authorized": False,
            "customer_nat_authorized": False,
            "customer_firewall_rules_authorized": False,
            "abuse_automation_authorized": False,
            "worker_runtime_authorized": False,
            "scheduler_authorized": False,
            "collector_authorized": False,
            "ui_authorized": False,
            "telegram_authorized": False,
        },
        "readiness_checks": checks,
        "blockers": blockers,
        "next_required_step": "Merge PR, sync main to farm5, run Phase 11A evidence commands, then record farm5 evidence in the next PR.",
    }
