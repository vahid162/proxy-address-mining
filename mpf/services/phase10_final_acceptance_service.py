from __future__ import annotations

from pathlib import Path
from typing import Any

from mpf.config import MPFConfig
from mpf.services.phase10_final_acceptance_readiness_service import build_phase10_final_acceptance_readiness_report


DANGEROUS_KEYS = (
    "phase11_production_activation_authorized",
    "controlled_cli_canary_authorized",
    "execution_allowed",
    "production_traffic_authorized",
    "firewall_apply_authorized",
    "abuse_automation_authorized",
    "real_worker_runtime_authorized",
    "scheduler_authorized",
    "timer_authorized",
    "collector_authorized",
    "production_db_execution_authorized",
    "hard_block_authorized",
    "soft_block_authorized",
    "pause_automation_authorized",
    "customer_mutation_authorized",
    "ui_authorized",
    "telegram_authorized",
)


def _dangerous_flags_enabled(report: dict[str, Any]) -> list[str]:
    enabled = list(report.get("downstream_dangerous_authorization_flags", []))
    component = str(report.get("component", "phase10_final_acceptance_readiness"))
    for key in DANGEROUS_KEYS:
        if report.get(key) is True:
            enabled.append(f"{component}.{key}")
    return enabled


def build_phase10_final_acceptance_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase_path = root / "docs/PHASE_STATUS.md"
    phase = phase_path.read_text(encoding="utf-8") if phase_path.exists() else ""

    readiness = build_phase10_final_acceptance_readiness_report(cfg, repo_root=root)
    evidence_present = (root / "docs/PHASE_10_FARM5_0_1_136_SYNC_TEST_EVIDENCE.md").exists()
    pre_acceptance_gate_ok = (
        "current_accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5" in phase
        and "current_working_phase: Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness" in phase
    )
    post_acceptance_gate_ok = (
        "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5" in phase
        and "current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness" in phase
    )
    gate_ok = pre_acceptance_gate_ok or post_acceptance_gate_ok
    readiness_ok = readiness.get("final_decision") == "ACCEPTED"
    dangerous_flags = _dangerous_flags_enabled(readiness)

    blockers: list[str] = []
    if not evidence_present:
        blockers.append("farm5_0_1_136_sync_test_evidence_missing")
    if not readiness_ok:
        blockers.append("phase10_final_acceptance_readiness_not_accepted")
    if not gate_ok:
        blockers.append("current_phase_gate_missing_or_invalid")
    if dangerous_flags:
        blockers.append("dangerous_authorization_flag_enabled")

    accepted = not blockers
    return {
        "component": "phase10_final_acceptance",
        "phase": "Phase 10 — Session / Worker / Policy / Share Timeline",
        "final_decision": "ACCEPTED" if accepted else "BLOCKED",
        "acceptance_status": "PHASE10_ACCEPTED" if accepted else "BLOCKED",
        "report_only": True,
        "inspection_only": True,
        "execution_allowed": False,
        "phase10_acceptance_authorized": accepted,
        "phase11_production_activation_authorized": False,
        "controlled_cli_canary_authorized": False,
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
        "farm5_0_1_136_sync_test_evidence_present": evidence_present,
        "phase10_final_acceptance_readiness": "ACCEPTED" if readiness_ok else "BLOCKED",
        "current_phase_gate_status": "OK" if gate_ok else "BLOCKED",
        "downstream_dangerous_authorization_flags": dangerous_flags,
        "blockers": blockers,
        "warnings": [],
        "errors": [],
        "next_phase": "Phase 11 — Production / Customer Activation Gate planning/readiness",
        "post_merge_required_operator_evidence": "fresh farm5 0.1.137 sync/test evidence before any Phase 11 production/canary implementation PRs",
    }
