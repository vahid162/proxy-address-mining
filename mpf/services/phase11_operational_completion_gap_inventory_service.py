"""Read-only, fail-closed Phase 11 full CLI production operations gap inventory."""

from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.services.phase11_restart_autostart_proof_service import (
    build_phase11_restart_autostart_proof_report,
)


_MISSING_OR_PARTIAL = "missing_or_partial"


def build_phase11_operational_completion_gap_inventory_report(evidence_dir: Path | str | None = None) -> dict[str, object]:
    """Return the expanded post-acceptance Phase 11 gap inventory without mutation."""

    restart_report = build_phase11_restart_autostart_proof_report(evidence_dir) if evidence_dir else None
    restart_status = restart_report["restart_autostart_proof"] if restart_report else _MISSING_OR_PARTIAL
    next_required_step = (
        "implement_production_customer_lifecycle_execution"
        if restart_status == "ready"
        else "run_restart_autostart_proof_on_farm5"
    )

    return {
        "component": "phase11_operational_completion_gap_inventory",
        "repository_version": __version__,
        "phase11_accepted": True,
        "phase11_operational_completion_required": True,
        "phase11_operational_completion_scope": "full_cli_production_operations",
        "phase12_start_allowed": False,
        "restart_autostart_proof": restart_status,
        "production_customer_lifecycle_execution": _MISSING_OR_PARTIAL,
        "production_firewall_apply_verify_rollback": _MISSING_OR_PARTIAL,
        "production_onboarding_flow": _MISSING_OR_PARTIAL,
        "production_usage_report_check_evidence": _MISSING_OR_PARTIAL,
        "production_abuse_runner": _MISSING_OR_PARTIAL,
        "production_controls_pause_block_expire": _MISSING_OR_PARTIAL,
        "backup_restore_drill": _MISSING_OR_PARTIAL,
        "full_cli_production_operations": _MISSING_OR_PARTIAL,
        "accepted_final_state_required": {
            "production_traffic": "cli_production",
            "customer_onboarding_allowed": "cli_production",
        },
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "final_decision": "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED",
        "next_required_step": next_required_step,
        "restart_autostart_proof_final_decision": restart_report["final_decision"] if restart_report else "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL",
    }
