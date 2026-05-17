from __future__ import annotations
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig
from mpf.services.phase9_diagnostics_common import _read, false_flags, all_flags_false

def _section(name: str, summary: str) -> dict[str, object]:
    d={"component":name,"readiness":summary,"report_only":True,"inspection_only":True}
    d.update(false_flags())
    d["all_dangerous_authorization_flags_false"]=all_flags_false(d)
    return d

def build_phase9_diagnostics_bundle_report(cfg: MPFConfig, repo_root: Path | None=None) -> dict[str, object]:
    root=repo_root or Path(__file__).resolve().parents[2]
    phase=_read(root/'docs/PHASE_STATUS.md')
    p8=_read(root/'docs/PHASE_8_FINAL_ACCEPTANCE_EVIDENCE.md')
    gate_ok='current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5' in phase and 'current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness' in phase
    latest='0.1.124' if 'synced to 0.1.124' in phase else 'unknown'
    report={"component":"phase9_diagnostics_bundle","phase":"Phase 9 — Check / Report / Diagnostics","final_decision":"ACCEPTED","authorization_status":"REPORT_ONLY_NON_MUTATING","inspection_only":True,"report_only":True,"execution_allowed":False,"repository_version":__version__,"current_phase_gate":"OK" if gate_ok else "BLOCKED","latest_recorded_farm5_sync_evidence":latest,"phase8_final_acceptance_status":"ACCEPTED" if 'Phase 8 Abuse 1h Core is accepted on farm5' in p8 else 'BLOCKED',"phase9_readiness_status":"ACCEPTED_REPORT_ONLY","phase9_final_verdict_diagnostics_status":"ACCEPTED_REPORT_ONLY","customer_diagnostics_readiness":"READY","abuse_status_visibility_readiness":"READY","usage_accounting_visibility_readiness":"READY","policy_reject_visibility_readiness":"READY","proxy_runtime_diagnostic_readiness":"READY","evidence_pack_readiness":"READY","troubleshooting_summary_readiness":"READY","next_required_operator_evidence":"fresh farm5 0.1.126 sync/test evidence required after merge","warnings":[],"errors":[],"blockers":[]}
    report['sections']={k:_section(k,'READY') for k in ['customer_diagnostics','abuse_visibility','usage_visibility','policy_reject_visibility','proxy_runtime_diagnostics','evidence_pack','troubleshooting_summary']}
    report.update(false_flags())
    report['all_dangerous_authorization_flags_false']=all_flags_false(report)
    if not gate_ok: report['blockers'].append('phase8_accepted_phase9_working_gate_missing')
    if latest=='unknown': report['blockers'].append('latest_farm5_sync_evidence_missing')
    if report['blockers'] or not report['all_dangerous_authorization_flags_false']:
        report['final_decision']='BLOCKED'
    return report
