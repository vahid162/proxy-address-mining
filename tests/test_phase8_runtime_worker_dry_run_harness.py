from __future__ import annotations
import json
from pathlib import Path
from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.abuse_worker_dry_run_harness import AbuseWorkerDryRunCycleInput, AbuseWorkerDryRunItem, build_worker_dry_run_cycle_id, evaluate_worker_dry_run_cycle
from mpf.interfaces.cli import app
from mpf.services.phase8_runtime_worker_dry_run_harness_service import build_phase8_runtime_worker_dry_run_harness_report


def cfg(): return load_config(Path('configs/mpf.example.yaml'))

def mk(**kw):
    base=dict(item_id='i1',customer_id=1,lane_id=1,customer_key='c',port=50001,current_state='normal',synthetic_evidence_status='ok',synthetic_decision_hint='normal')
    base.update(kw); return AbuseWorkerDryRunItem(**base)

def cycle(items, **kw):
    data=dict(cycle_id='c1',mode='report_only',now_iso='2026-05-16T00:00:00Z',items=items,global_kill_switch_enabled=False,worker_enabled=True,scheduler_enabled=False,max_batch_size=10,lock_name='l')
    data.update(kw)
    return evaluate_worker_dry_run_cycle(AbuseWorkerDryRunCycleInput(**data))

def test_domain_behaviors_and_determinism():
    assert build_worker_dry_run_cycle_id('a','t')==build_worker_dry_run_cycle_id('a','t')
    assert cycle([mk()],worker_enabled=False).item_results[0].skip_reason=='worker_disabled'
    assert 'scheduler_enabled_not_allowed_in_this_pr' in cycle([mk()],scheduler_enabled=True).blockers
    assert cycle([mk()],global_kill_switch_enabled=True).item_results[0].skip_reason=='global_kill_switch'
    assert cycle([]).no_work is True
    assert cycle([mk()]).item_results[0].would_transition is False
    assert cycle([mk(synthetic_decision_hint='miner_over')]).item_results[0].would_transition is True
    assert cycle([mk(synthetic_decision_hint='sustained_hard')]).item_results[0].would_harden is True
    assert 'farms_over_report_only' in cycle([mk(synthetic_decision_hint='farms_over_only')]).item_results[0].warnings
    assert 'worker_over_report_only' in cycle([mk(synthetic_decision_hint='worker_over_only')]).item_results[0].warnings
    assert cycle([mk(synthetic_evidence_status='missing')]).item_results[0].would_harden is False
    assert cycle([mk(synthetic_evidence_status='stale')]).item_results[0].would_harden is False
    assert cycle([mk(should_simulate_lock_contention=True)]).item_results[0].skip_reason=='lock_contention'
    assert cycle([mk(should_simulate_duplicate_idempotency=True)]).item_results[0].skip_reason=='duplicate_idempotency'
    assert cycle([mk(),mk(item_id='i2')],max_batch_size=1).item_results[0].skip_reason=='batch_limit'
    assert cycle([mk(should_simulate_db_failure=True)]).item_results[0].db_write_executed is False
    assert cycle([mk(should_simulate_firewall_failure=True)]).item_results[0].would_harden is False
    assert 'unknown_synthetic_decision_hint' in cycle([mk(synthetic_decision_hint='x')]).item_results[0].blockers


def test_service_cli_and_fail_closed(tmp_path: Path):
    r=build_phase8_runtime_worker_dry_run_harness_report(cfg())
    assert r['component']=='phase8_runtime_worker_dry_run_harness' and r['final_decision']=='BLOCKED'
    assert r['execution_allowed'] is False and r['phase8_acceptance_allowed'] is False
    assert r['latest_recorded_farm5_sync_evidence']=='0.1.115'
    assert r['no_farm5_0_1_116_sync_evidence_claimed'] is True and r['no_farm5_0_1_117_sync_evidence_claimed'] is True
    assert r['runtime_worker_readiness_present'] is True
    assert r['runtime_worker_readiness_fail_closed'] is False
    assert r['blockers'] == ['runtime_worker_readiness_fail_closed_missing_or_failed']
    assert r['synthetic_worker_cycles_passed'] is True
    out=CliRunner().invoke(app,['phase8','runtime-worker-dry-run-harness','--config','configs/mpf.example.yaml','--output','json'])
    assert out.exit_code==0
    data=json.loads(out.stdout)
    assert data['final_decision']=='BLOCKED' and data['execution_allowed'] is False and data['runtime_worker_authorized'] is False

