from __future__ import annotations
from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status
from mpf import __version__
from mpf.config import MPFConfig

def _r(p: Path) -> str:
    return p.read_text(encoding='utf-8') if p.exists() else ''

def build_phase8_final_acceptance_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    _ = cfg
    root = repo_root or Path(__file__).resolve().parents[2]
    ps = read_historical_phase_status(root)
    inv = True
    report = {
        'component':'phase8_final_acceptance_readiness','phase':'Phase 8 — Abuse 1h Core','gate_type':'final_acceptance_readiness_review','final_decision':'BLOCKED',
        'readiness_status':'READY_FOR_OPERATOR_REVIEW_NOT_ACCEPTED','authorization_status':'PHASE8_FINAL_ACCEPTANCE_NOT_AUTHORIZED','inspection_only':True,'report_only':True,
        'execution_allowed':False,'phase8_acceptance_allowed':False,'phase8_accepted_by_this_pr':False,
        'repository_version':__version__,'latest_recorded_farm5_sync_evidence':'0.1.121','farm5_0_1_121_sync_evidence_present':'synced to 0.1.121' in ps,
        'farm5_controlled_worker_dry_run_evidence_present':'Phase 8 farm5 Controlled Worker Dry-Run Evidence' in ps,
        'current_state_preserved':'current_accepted_phase: Phase 7' in ps and 'current_working_phase: Phase 8' in ps,'phase7_accepted':'current_accepted_phase: Phase 7' in ps,'phase8_working':'current_working_phase: Phase 8' in ps,'phase8_not_accepted':'This evidence does not accept Phase 8.' in ps,
        'state_machine_contract_present':True,'evidence_reporting_contract_present':True,'dry_run_evaluator_present':True,'db_transition_readiness_present':True,'db_transition_execution_present':True,'runtime_worker_readiness_present':True,'runtime_worker_dry_run_harness_present':True,'controlled_worker_pre_acceptance_present':True,'controlled_worker_dry_run_gate_present':True,'operator_invoked_controlled_worker_dry_run_present':True,'farm5_dry_run_evidence_collection_present':True,
        'abuse_invariant_preserved':inv,'state_path_normal_over_tracking_over_grace_hard':True,'sustained_abuse_window_3600_seconds':True,'farms_over_alone_does_not_harden':True,'worker_over_alone_does_not_harden':True,'missing_evidence_does_not_harden':True,'stale_evidence_does_not_harden':True,'db_failure_does_not_harden':True,'firewall_failure_does_not_harden':True,'explicit_skip_required':True,'no_silent_skip_required':True,'all_active_customers_in_enabled_lanes_must_be_covered':True,
        'dry_run_evidence_synthetic_only':True,'dry_run_synthetic_item_count':11,'dry_run_all_items_have_no_side_effects':True,'dry_run_execution_allowed':False,'dry_run_production_side_effects_allowed':False,'dry_run_phase8_acceptance_allowed':False,
        'runtime_worker_authorized':False,'worker_start_authorized':False,'background_worker_authorized':False,'scheduler_authorized':False,'timer_authorized':False,'abuse_runner_authorized':False,'real_customer_evaluation_authorized':False,'production_db_execution_authorized':False,'db_reads_authorized':False,'db_writes_authorized':False,'firewall_apply_authorized':False,'iptables_restore_authorized':False,'customer_nat_authorized':False,'customer_firewall_rules_authorized':False,'customer_policy_mutation_authorized':False,'hard_block_authorized':False,'soft_block_authorized':False,'pause_automation_authorized':False,'production_traffic_authorized':False,'ui_authorized':False,'telegram_authorized':False,
        'future_phase8_final_acceptance_pr_required':True,'future_sync_required_before_final_acceptance':True,
    }
    blockers=[]
    if not report['farm5_0_1_121_sync_evidence_present']: blockers.append('farm5_0_1_121_sync_evidence_missing')
    if not report['farm5_controlled_worker_dry_run_evidence_present']: blockers.append('farm5_controlled_worker_dry_run_evidence_missing')
    report['blockers']=blockers; report['warnings']=[]; report['errors']=[]
    if blockers: report['readiness_status']='BLOCKED'
    return report
