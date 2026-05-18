from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services.phase9_diagnostics_common import DANGEROUS_AUTHORIZATION_FLAGS, all_flags_false, false_flags

LATEST_EVIDENCE_VERSION = "0.1.132"
NEXT_EVIDENCE = "fresh farm5 0.1.133 sync/test after merge before any runtime/scheduler/collector implementation PR"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_phase10_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg
    root = repo_root or Path(__file__).resolve().parents[2]
    phase = _read(root / "docs/PHASE_STATUS.md")
    farm5_0_1_130 = _read(root / "docs/PHASE_10_FARM5_0_1_130_SYNC_TEST_EVIDENCE.md")
    farm5_0_1_131 = _read(root / "docs/PHASE_10_FARM5_0_1_131_SYNC_TEST_EVIDENCE.md")
    farm5_0_1_132 = _read(root / "docs/PHASE_10_FARM5_0_1_132_SYNC_TEST_EVIDENCE.md")

    gate_ok = (
        "current_accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5" in phase
        and "current_working_phase: Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness" in phase
    )
    farm5_0_1_128_evidence = "### Phase 10 farm5 0.1.128 Sync/Test Evidence" in phase
    farm5_0_1_130_evidence = "# Phase 10 farm5 0.1.130 Sync/Test Evidence" in farm5_0_1_130
    farm5_0_1_131_sync_test_evidence_present = "# Phase 10 farm5 0.1.131 Sync/Test Evidence" in farm5_0_1_131
    farm5_0_1_132_sync_test_evidence_present = (
        "# Phase 10 farm5 0.1.132 Sync/Test Evidence" in farm5_0_1_132
        and "server version after sync:\n  0.1.132" in farm5_0_1_132
        and "768 passed in 149.45s" in farm5_0_1_132
        and "production_traffic: none" in farm5_0_1_132
        and "firewall_apply_allowed: no" in farm5_0_1_132
        and "abuse_automation_allowed: no" in farm5_0_1_132
        and "no customer NAT redirects" in farm5_0_1_132
        and "production customer traffic is still disabled" in farm5_0_1_132
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
        "latest_recorded_farm5_sync_evidence": LATEST_EVIDENCE_VERSION if farm5_0_1_132_sync_test_evidence_present else ("0.1.131" if farm5_0_1_131_sync_test_evidence_present else ("0.1.130" if farm5_0_1_130_evidence else ("0.1.128" if farm5_0_1_128_evidence else "unknown"))),
        "farm5_0_1_128_sync_test_evidence_present": farm5_0_1_128_evidence,
        "farm5_0_1_130_sync_test_evidence_present": farm5_0_1_130_evidence,
        "farm5_0_1_131_sync_test_evidence_present": farm5_0_1_131_sync_test_evidence_present,
        "farm5_0_1_132_sync_test_evidence_present": farm5_0_1_132_sync_test_evidence_present,
        "phase9_final_acceptance_status": "ACCEPTED" if phase9_accepted else "BLOCKED",
        "phase10_planning_readiness_status": "ACCEPTED",
        "session_readiness": "ACCEPTED_REPORT_ONLY",
        "worker_policy_readiness": "ACCEPTED_REPORT_ONLY",
        "share_timeline_readiness": "ACCEPTED_REPORT_ONLY",
        "enforcement_boundary_readiness": "ACCEPTED_REPORT_ONLY",
        "next_required_operator_evidence": NEXT_EVIDENCE,
    }
    report.update(false_flags())
    report["all_dangerous_authorization_flags_false"] = all_flags_false(report)
    report["aggregate_dangerous_authorization_flag"] = any(report.get(k) is True for k in DANGEROUS_AUTHORIZATION_FLAGS)

    blockers: list[str] = []
    if not gate_ok:
        blockers.append("phase9_accepted_phase10_working_gate_missing")
    if not farm5_0_1_132_sync_test_evidence_present:
        blockers.append("farm5_0_1_132_sync_test_evidence_missing")
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
