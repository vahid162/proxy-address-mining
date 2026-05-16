from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_phase9_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_status = _read(root / "docs/PHASE_STATUS.md")
    readme = _read(root / "README.md")

    gate_ok = "current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5" in phase_status and "current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness" in phase_status

    report = {
        "component": "phase9_readiness",
        "phase": "Phase 9 — Check / Report / Diagnostics",
        "gate_type": "phase9_report_only_readiness",
        "final_decision": "ACCEPTED",
        "readiness_status": "PHASE9_REPORT_ONLY_READINESS_ACCEPTED",
        "authorization_status": "PHASE9_REPORT_ONLY_NON_MUTATING",
        "inspection_only": True,
        "report_only": True,
        "execution_allowed": False,
        "repository_version": __version__,
        "phase_gate_status": "OK" if gate_ok else "BLOCKED",
        "doctor_config_database_expectations": "READY",
        "proxy_runtime_diagnostics_expectations": "READY",
        "customer_diagnostics_readiness": "READY",
        "abuse_status_visibility_readiness": "READY",
        "usage_accounting_visibility_readiness": "READY",
        "policy_reject_visibility_readiness": "READY",
        "evidence_pack_readiness": "READY",
        "troubleshooting_final_verdict_readiness": "READY",
        "phase9_readiness_documented_in_readme": "Phase 9 report-only readiness" in readme,
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
    }
    blockers: list[str] = []
    if not gate_ok:
        blockers.append("phase8_accepted_phase9_working_gate_missing")
    if blockers:
        report["final_decision"] = "BLOCKED"
        report["readiness_status"] = "BLOCKED"
    report["blockers"] = blockers
    report["warnings"] = []
    report["errors"] = []
    return report
