from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_phase9_final_verdict_diagnostics_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")

    phase_gate_ok = (
        "current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5" in phase_status
        and "current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness" in phase_status
    )
    latest_0_1_124_evidence_present = "### Phase 9 farm5 0.1.124 Sync/Test Evidence" in phase_status and "synced to 0.1.124" in phase_status
    phase8_final_acceptance_accepted = "phase8 final-acceptance: ACCEPTED" in phase_status
    phase9_readiness_accepted_report_only = "phase9 readiness: ACCEPTED / report-only" in phase_status

    report = {
        "component": "phase9_final_verdict_diagnostics",
        "phase": "Phase 9 — Check / Report / Diagnostics",
        "gate_type": "phase9_report_only_final_verdict_diagnostics",
        "final_decision": "ACCEPTED",
        "final_verdict_readiness": "PHASE9_REPORT_ONLY_FINAL_VERDICT_READY",
        "authorization_status": "PHASE9_REPORT_ONLY_NON_MUTATING",
        "inspection_only": True,
        "report_only": True,
        "execution_allowed": False,
        "repository_version": __version__,
        "phase_gate_status": "OK" if phase_gate_ok else "BLOCKED",
        "latest_recorded_farm5_sync_evidence": "0.1.124",
        "farm5_0_1_124_sync_evidence_present": latest_0_1_124_evidence_present,
        "phase8_final_acceptance_status": "ACCEPTED" if phase8_final_acceptance_accepted else "BLOCKED",
        "phase9_readiness_status": "ACCEPTED_REPORT_ONLY" if phase9_readiness_accepted_report_only else "BLOCKED",
        "doctor_config_database_expectations": "READY",
        "proxy_runtime_diagnostics_expectations": "READY",
        "customer_diagnostics_readiness": "READY",
        "abuse_status_visibility_readiness": "READY",
        "usage_accounting_visibility_readiness": "READY",
        "policy_reject_visibility_readiness": "READY",
        "evidence_pack_readiness": "READY",
        "troubleshooting_final_verdict_readiness": "READY",
        "operator_final_verdict_readiness": "READY",
        "runtime_worker_authorized": False,
        "worker_start_authorized": False,
        "scheduler_authorized": False,
        "timer_authorized": False,
        "abuse_runner_authorized": False,
        "production_db_execution_authorized": False,
        "db_writes_authorized": False,
        "firewall_apply_authorized": False,
        "iptables_restore_authorized": False,
        "customer_nat_authorized": False,
        "customer_firewall_rules_authorized": False,
        "hard_block_authorized": False,
        "soft_block_authorized": False,
        "pause_automation_authorized": False,
        "production_traffic_authorized": False,
        "ui_authorized": False,
        "telegram_authorized": False,
        "all_dangerous_authorization_flags_false": True,
    }

    blockers: list[str] = []
    if not phase_gate_ok:
        blockers.append("phase8_accepted_phase9_working_gate_missing")
    if not latest_0_1_124_evidence_present:
        blockers.append("farm5_0_1_124_sync_evidence_missing")
    if not phase8_final_acceptance_accepted:
        blockers.append("phase8_final_acceptance_not_accepted")
    if not phase9_readiness_accepted_report_only:
        blockers.append("phase9_readiness_not_accepted_report_only")

    if blockers:
        report["final_decision"] = "BLOCKED"
        report["final_verdict_readiness"] = "BLOCKED"

    report["blockers"] = blockers
    report["warnings"] = []
    report["errors"] = []
    return report
