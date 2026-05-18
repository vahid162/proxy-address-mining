from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services.phase9_diagnostics_common import DANGEROUS_AUTHORIZATION_FLAGS, all_flags_false, false_flags

LATEST_EVIDENCE_VERSION = "0.1.131"
NEXT_EVIDENCE = "fresh farm5 0.1.132 sync/test before Phase 10A/10B/10C readiness implementation is accepted"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_phase10_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase = _read(root / "docs/PHASE_STATUS.md")
    farm5_0_1_130 = _read(root / "docs/PHASE_10_FARM5_0_1_130_SYNC_TEST_EVIDENCE.md")
    farm5_0_1_131 = _read(root / "docs/PHASE_10_FARM5_0_1_131_SYNC_TEST_EVIDENCE.md")

    gate_ok = (
        "current_accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5" in phase
        and "current_working_phase: Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness" in phase
    )
    farm5_0_1_128_evidence = (
        "### Phase 10 farm5 0.1.128 Sync/Test Evidence" in phase
        and "server version after sync:\n  0.1.128" in phase
        and "pytest:\n  759 passed" in phase
    )
    farm5_0_1_130_evidence = (
        "# Phase 10 farm5 0.1.130 Sync/Test Evidence" in farm5_0_1_130
        and "server version: 0.1.130" in farm5_0_1_130
        and "pytest: 767 passed in 82.44s" in farm5_0_1_130
        and "all dangerous authorization flags: false" in farm5_0_1_130
    )
    farm5_0_1_131_sync_test_evidence_present = (
        "# Phase 10 farm5 0.1.131 Sync/Test Evidence" in farm5_0_1_131
        and "server version after sync:\n  0.1.131" in farm5_0_1_131
        and "768 passed" in farm5_0_1_131
        and "production_traffic:\n  none" in farm5_0_1_131
        and "firewall_apply_allowed:\n  no" in farm5_0_1_131
        and "abuse_automation_allowed:\n  no" in farm5_0_1_131
        and "no customer NAT redirects" in farm5_0_1_131
        and "production customer traffic is still disabled" in farm5_0_1_131
    )
    phase9_accepted = "phase9 final-acceptance:\n  ACCEPTED" in phase

    report = {
        "component": "phase10_readiness",
        "final_decision": "ACCEPTED",
        "readiness_status": "PHASE10_PLANNING_READINESS_ACCEPTED",
        "authorization_status": "PHASE10_REPORT_ONLY_NON_MUTATING",
        "report_only": True,
        "inspection_only": True,
        "execution_allowed": False,
        "repository_version": __version__,
        "current_phase_gate_status": "OK" if gate_ok else "BLOCKED",
        "latest_recorded_farm5_sync_evidence": LATEST_EVIDENCE_VERSION if farm5_0_1_131_sync_test_evidence_present else ("0.1.130" if farm5_0_1_130_evidence else ("0.1.128" if farm5_0_1_128_evidence else "unknown")),
        "farm5_0_1_128_sync_test_evidence_present": farm5_0_1_128_evidence,
        "farm5_0_1_130_sync_test_evidence_present": farm5_0_1_130_evidence,
        "farm5_0_1_131_sync_test_evidence_present": farm5_0_1_131_sync_test_evidence_present,
        "phase9_final_acceptance_status": "ACCEPTED" if phase9_accepted else "BLOCKED",
        "phase10_planning_readiness_status": "ACCEPTED",
        "session_readiness": "ACCEPTED_REPORT_ONLY",
        "worker_policy_readiness": "ACCEPTED_REPORT_ONLY",
        "share_timeline_readiness": "ACCEPTED_REPORT_ONLY",
        "enforcement_boundary_readiness": "ACCEPTED_REPORT_ONLY",
        "future_db_schema_readiness_expectation": "explicit additive planning/migration gate required",
        "future_runtime_worker_readiness_expectation": "explicit runtime gate + fresh farm5 evidence required",
        "future_scheduler_timer_readiness_expectation": "explicit scheduler/timer gate + evidence required",
        "future_collector_readiness_expectation": "explicit collector/retention gate + evidence required",
        "future_firewall_enforcement_readiness_expectation": "explicit apply/runtime/rollback gate + evidence required",
        "next_required_operator_evidence": NEXT_EVIDENCE,
    }
    report.update(false_flags())
    report.update(
        {
            "production_activation_allowed": False,
            "db_reads_authorized": False,
            "live_traffic_capture_authorized": False,
            "tcpdump_authorized": False,
            "conntrack_read_authorized": False,
            "conntrack_flush_authorized": False,
            "share_collector_authorized": False,
            "usage_collector_authorized": False,
            "policy_collector_authorized": False,
        }
    )
    report["all_dangerous_authorization_flags_false"] = all_flags_false(report)
    report["aggregate_dangerous_authorization_flag"] = any(report.get(k) is True for k in DANGEROUS_AUTHORIZATION_FLAGS)

    blockers: list[str] = []
    if not gate_ok:
        blockers.append("phase9_accepted_phase10_working_gate_missing")
    if not farm5_0_1_131_sync_test_evidence_present:
        blockers.append("farm5_0_1_131_sync_test_evidence_missing")
    if not phase9_accepted:
        blockers.append("phase9_final_acceptance_missing")
    if report["aggregate_dangerous_authorization_flag"] or not report["all_dangerous_authorization_flags_false"]:
        blockers.append("dangerous_authorization_flag_enabled")
    if blockers:
        report["final_decision"] = "BLOCKED"
        report["readiness_status"] = "BLOCKED"

    report["blockers"] = blockers
    report["warnings"] = []
    report["errors"] = []
    return report
