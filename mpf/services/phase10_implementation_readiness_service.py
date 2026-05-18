from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services.phase10_readiness_service import build_phase10_readiness_report
from mpf.services.phase10_session_model_readiness_service import build_session_model_readiness_report
from mpf.services.phase10_worker_identity_readiness_service import build_worker_identity_readiness_report
from mpf.services.phase10_worker_policy_contract_readiness_service import build_worker_policy_contract_readiness_report
from mpf.services.phase10_share_timeline_model_readiness_service import build_share_timeline_model_readiness_report
from mpf.services.phase10_collector_dry_run_gate_service import build_collector_dry_run_gate_readiness_report
from mpf.services.phase10_runtime_worker_dry_run_readiness_service import build_runtime_worker_dry_run_readiness_report
from mpf.services.phase10_scheduler_dry_run_readiness_service import build_scheduler_dry_run_readiness_report


def build_phase10_implementation_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[2]
    phase10 = build_phase10_readiness_report(cfg, repo_root=root)
    session = build_session_model_readiness_report(cfg, repo_root=root)
    identity = build_worker_identity_readiness_report(cfg, repo_root=root)
    policy = build_worker_policy_contract_readiness_report(cfg, repo_root=root)
    share_timeline = build_share_timeline_model_readiness_report(cfg, repo_root=root)
    collector_gate = build_collector_dry_run_gate_readiness_report(cfg, repo_root=root)
    runtime_worker = build_runtime_worker_dry_run_readiness_report(cfg, repo_root=root)
    scheduler = build_scheduler_dry_run_readiness_report(cfg, repo_root=root)
    evidence_present = (root / 'docs/PHASE_10_FARM5_0_1_134_SYNC_TEST_EVIDENCE.md').exists()
    gate_ok = phase10.get('current_phase_gate_status') == 'OK'
    dangerous = any([
        phase10.get('production_traffic_authorized', False), phase10.get('firewall_apply_authorized', False),
        phase10.get('abuse_automation_authorized', False), phase10.get('scheduler_authorized', False),
        phase10.get('collector_authorized', False), phase10.get('ui_authorized', False), phase10.get('telegram_authorized', False),
    ])
    accepted = all([gate_ok, evidence_present, session['final_decision']=='ACCEPTED', identity['final_decision']=='ACCEPTED', policy['final_decision']=='ACCEPTED', share_timeline['final_decision']=='ACCEPTED', collector_gate['final_decision']=='ACCEPTED', runtime_worker['final_decision']=='ACCEPTED', scheduler['final_decision']=='ACCEPTED', not dangerous])
    blockers=[]
    if not gate_ok: blockers.append('current_phase_gate_missing_or_invalid')
    if not evidence_present: blockers.append('farm5_0_1_134_sync_test_evidence_missing')
    if dangerous: blockers.append('dangerous_authorization_flag_enabled')
    return {
        'component':'phase10_implementation_readiness',
        'phase':'Phase 10 — Session / Worker / Policy / Share Timeline',
        'final_decision':'ACCEPTED' if accepted else 'BLOCKED',
        'execution_allowed':False,
        'runtime_authorized':False,
        'production_traffic_authorized':False,
        'firewall_apply_authorized':False,
        'abuse_automation_authorized':False,
        'scheduler_authorized':False,
        'collector_authorized':False,
        'ui_authorized':False,
        'telegram_authorized':False,
        'next_step':'Phase 10 final-acceptance-readiness, then Phase 10 final acceptance; not production activation.',
        'farm5_0_1_134_sync_test_evidence_present': evidence_present,
        'session_model_readiness': session['final_decision'],
        'worker_identity_readiness': identity['final_decision'],
        'worker_policy_contract_readiness': policy['final_decision'],
        'share_timeline_model_readiness': share_timeline['final_decision'],
        'collector_dry_run_gate_readiness': collector_gate['final_decision'],
        'runtime_worker_dry_run_readiness': runtime_worker['final_decision'],
        'scheduler_dry_run_readiness': scheduler['final_decision'],
        'current_phase_gate_status': phase10.get('current_phase_gate_status'),
        'blockers':blockers,
        'warnings':[],
        'errors':[],
    }
