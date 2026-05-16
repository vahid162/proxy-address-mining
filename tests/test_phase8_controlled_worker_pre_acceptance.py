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

    res = evaluate_abuse_worker_pre_acceptance(AbuseWorkerPreAcceptanceInput('0.1.115','0.1.118',True,True,True,True,True,True,True,True))
    assert res.final_decision == 'BLOCKED'
    assert res.controlled_worker_dry_run_allowed_now is False
    assert res.farm5_sync_required_before_worker_dry_run is True


def test_service_and_cli_json():
    r = build_phase8_controlled_worker_pre_acceptance_report(cfg())
    assert r['component'] == 'phase8_controlled_worker_pre_acceptance'
    assert r['final_decision'] == 'BLOCKED'
    assert r['execution_allowed'] is False
    assert r['phase8_acceptance_allowed'] is False
    assert r['latest_recorded_farm5_sync_evidence'] == '0.1.115'
    assert r['repository_version'] == '0.1.118'
    assert r['no_farm5_0_1_116_sync_evidence_claimed'] is True
    assert r['no_farm5_0_1_117_sync_evidence_claimed'] is True
    assert r['no_farm5_0_1_118_sync_evidence_claimed'] is True
    assert r['farm5_sync_required_before_worker_dry_run'] is True

    out = CliRunner().invoke(app,['phase8','controlled-worker-pre-acceptance','--config','configs/mpf.example.yaml','--output','json'])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data['final_decision'] == 'BLOCKED'
    assert data['execution_allowed'] is False
    assert data['controlled_worker_dry_run_allowed_now'] is False
