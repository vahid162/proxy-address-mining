from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.abuse_worker_pre_acceptance import AbuseWorkerPreAcceptanceInput, build_abuse_worker_pre_acceptance_contract, evaluate_abuse_worker_pre_acceptance
from mpf.interfaces.cli import app
from mpf.services.phase8_controlled_worker_pre_acceptance_service import build_phase8_controlled_worker_pre_acceptance_report


def cfg():
    return load_config(Path('configs/mpf.example.yaml'))


def test_domain_contract_and_eval():
    c = build_abuse_worker_pre_acceptance_contract()
    assert c.worker_execution_allowed_in_this_pr is False
    assert c.scheduler_allowed_in_this_pr is False
    assert c.timer_allowed_in_this_pr is False
    assert c.abuse_runner_allowed_in_this_pr is False
    assert c.real_customer_evaluation_allowed_in_this_pr is False
    assert c.production_db_execution_allowed_in_this_pr is False
    assert c.db_reads_allowed_in_this_pr is False and c.db_writes_allowed_in_this_pr is False
    assert c.firewall_mutation_allowed_in_this_pr is False and c.customer_mutation_allowed_in_this_pr is False
    assert c.hard_block_allowed_in_this_pr is False and c.soft_block_allowed_in_this_pr is False
    assert c.pause_automation_allowed_in_this_pr is False
    assert c.phase8_acceptance_allowed_in_this_pr is False

    res = evaluate_abuse_worker_pre_acceptance(AbuseWorkerPreAcceptanceInput('0.1.121', '0.1.118', True, True, True, True, True, True, True, True))
    assert res.final_decision == 'BLOCKED'
    assert res.controlled_worker_dry_run_allowed_now is False
    assert res.farm5_sync_required_before_worker_dry_run is False


def test_service_has_required_checks_and_scenarios():
    r = build_phase8_controlled_worker_pre_acceptance_report(cfg())
    assert r['component'] == 'phase8_controlled_worker_pre_acceptance'
    assert r['final_decision'] == 'BLOCKED'
    assert r['execution_allowed'] is False
    assert r['phase8_acceptance_allowed'] is False
    assert r['latest_recorded_farm5_sync_evidence'] == '0.1.121'
    assert r['repository_version'] == '0.1.122'
    assert r['no_farm5_0_1_116_sync_evidence_claimed'] is True
    assert r['no_farm5_0_1_117_sync_evidence_claimed'] is True
    assert r['farm5_0_1_119_historical_sync_evidence_present'] is True
    assert r['farm5_sync_required_before_worker_dry_run'] is True

    required_checks = [
        'apply_mode_plan_only', 'runtime_activation_disabled', 'production_traffic_none', 'firewall_apply_disallowed',
        'customer_nat_disallowed', 'customer_firewall_rules_disallowed', 'iptables_restore_disallowed',
        'abuse_automation_disallowed', 'abuse_runner_disallowed', 'runtime_worker_disallowed', 'scheduler_disallowed',
        'timer_disallowed', 'real_customer_evaluation_disallowed', 'production_db_execution_disallowed',
        'db_reads_disallowed', 'db_writes_disallowed', 'hard_block_disallowed', 'soft_block_disallowed',
        'pause_automation_disallowed', 'ui_disallowed', 'telegram_disallowed', 'abuse_invariant_preserved',
        'state_path_normal_over_tracking_over_grace_hard', 'sustained_abuse_window_3600_seconds',
        'missing_evidence_does_not_harden', 'stale_evidence_does_not_harden', 'db_failure_does_not_harden',
        'firewall_failure_does_not_harden', 'farms_over_alone_does_not_harden', 'worker_over_alone_does_not_harden',
        'explicit_skip_required', 'no_silent_skip_required',
    ]
    for key in required_checks:
        assert key in r
        assert r[key] is True

    assert r['runtime_worker_dry_run_harness_fail_closed'] is True
    assert r['runtime_worker_dry_run_harness_present'] is True
    assert 'repository_version_is_current_missing_or_failed' not in r['blockers']

    scenarios = r['synthetic_pre_acceptance_scenarios']
    assert len(scenarios) == 16
    assert sum(1 for s in scenarios if s['passed'] is True) >= 14


def test_cli_json_output():
    out = CliRunner().invoke(app, ['phase8', 'controlled-worker-pre-acceptance', '--config', 'configs/mpf.example.yaml', '--output', 'json'])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data['final_decision'] == 'BLOCKED'
    assert data['execution_allowed'] is False
    assert data['controlled_worker_dry_run_allowed_now'] is False
