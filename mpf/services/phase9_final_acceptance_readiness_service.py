from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services.phase9_diagnostics_common import all_flags_false, false_flags


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_phase9_final_acceptance_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg
    root = repo_root or Path(__file__).resolve().parents[2]
    phase = _read(root / "docs/PHASE_STATUS.md")

    phase9_current_gate_ok = (
        "current_accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5" in phase
        and "current_working_phase: Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness" in phase
    )
    later_phase_gate_ok = "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5" in phase
    gate_ok = phase9_current_gate_ok or later_phase_gate_ok
    farm5_0_1_127_present = "### Phase 9 farm5 0.1.127 Sync/Test Evidence" in phase and "server version after sync:\n  0.1.127" in phase
    phase8_final_accepted = "phase8 final-acceptance:\n  ACCEPTED" in phase
    phase9_readiness_accepted = "phase9 readiness:\n  ACCEPTED" in phase
    phase9_final_verdict_accepted = "phase9 final-verdict:\n  ACCEPTED" in phase
    phase9_diagnostics_accepted = "phase9 diagnostics:\n  ACCEPTED" in phase

    report = {
        "component": "phase9_final_acceptance_readiness",
        "final_decision": "ACCEPTED",
        "final_acceptance_readiness": "PHASE9_FINAL_ACCEPTANCE_READINESS_ACCEPTED",
        "authorization_status": "PHASE9_REPORT_ONLY_NON_MUTATING",
        "report_only": True,
        "inspection_only": True,
        "execution_allowed": False,
        "repository_version": __version__,
        "current_phase_gate_status": "OK" if gate_ok else "BLOCKED",
        "latest_recorded_farm5_sync_evidence": "0.1.127" if farm5_0_1_127_present else "unknown",
        "farm5_0_1_126_sync_test_evidence_present": farm5_0_1_127_present,
        "phase8_final_acceptance_status": "ACCEPTED" if phase8_final_accepted else "BLOCKED",
        "phase9_readiness_status": "ACCEPTED" if phase9_readiness_accepted else "BLOCKED",
        "phase9_final_verdict_diagnostics_status": "ACCEPTED" if phase9_final_verdict_accepted else "BLOCKED",
        "phase9_diagnostics_bundle_status": "ACCEPTED" if phase9_diagnostics_accepted else "BLOCKED",
        "customer_diagnostics_readiness": "READY",
        "abuse_visibility_readiness": "READY",
        "usage_accounting_visibility_readiness": "READY",
        "policy_reject_visibility_readiness": "READY",
        "proxy_runtime_diagnostics_readiness": "READY",
        "evidence_pack_readiness": "READY",
        "troubleshooting_summary_readiness": "READY",
        "next_required_operator_evidence": "historical: farm5 0.1.128 sync/test evidence required before Phase 10 implementation PRs",
    }
    report.update(false_flags())
    report["all_dangerous_authorization_flags_false"] = all_flags_false(report)

    blockers: list[str] = []
    if not gate_ok:
        blockers.append("phase9_accepted_phase10_working_or_later_gate_missing")
    if not farm5_0_1_127_present:
        blockers.append("farm5_0_1_127_sync_test_evidence_missing")
    if not phase8_final_accepted:
        blockers.append("phase8_final_acceptance_missing")
    if not phase9_readiness_accepted:
        blockers.append("phase9_readiness_missing")
    if not phase9_final_verdict_accepted:
        blockers.append("phase9_final_verdict_missing")
    if not phase9_diagnostics_accepted:
        blockers.append("phase9_diagnostics_bundle_missing")
    if not report["all_dangerous_authorization_flags_false"]:
        blockers.append("dangerous_authorization_flag_enabled")

    if blockers:
        report["final_decision"] = "BLOCKED"
        report["final_acceptance_readiness"] = "BLOCKED"

    report["blockers"] = blockers
    report["warnings"] = []
    report["errors"] = []
    return report
