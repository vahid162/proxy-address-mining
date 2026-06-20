from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.abuse_db_transition_execution import AbuseDBExecutionRequest, validate_db_execution_request
from mpf.interfaces.cli import app
from mpf.repositories.abuse_transition_execution_repo import InMemoryAbuseTransitionExecutionRepo
from mpf.services.phase8_db_transition_execution_service import build_phase8_db_transition_execution_report, execute_db_transition_controlled


def req(**kw):
    data=dict(plan_id='p',idempotency_key='k',customer_id=1,lane_id=1,port=60010,current_state='normal',proposed_state='over_tracking',decision='tracking',evidence_status='complete',evidence_reference='e',restore_reference='r',policy_backup_reference='b',operator_id='o',operator_reason='why',operator_confirmation='I_UNDERSTAND_DB_ONLY_ABUSE_TRANSITION',request_source='explicit_manual_cli',dry_run=True)
    data.update(kw)
    return AbuseDBExecutionRequest(**data)


def test_validation_and_service_and_cli() -> None:
    v = validate_db_execution_request(req())
    assert v.db_writes_allowed is False
    assert validate_db_execution_request(req(dry_run=False, operator_confirmation=None)).execution_allowed is False
    assert validate_db_execution_request(req(dry_run=False, request_source='api')).execution_allowed is False
    assert validate_db_execution_request(req(dry_run=False, evidence_status='stale')).execution_allowed is False
    assert validate_db_execution_request(req(dry_run=False, idempotency_key='')).execution_allowed is False
    assert validate_db_execution_request(req(dry_run=False, customer_id=0)).execution_allowed is False
    assert validate_db_execution_request(req(dry_run=False, proposed_state='normal')).execution_allowed is False
    assert validate_db_execution_request(req(dry_run=False)).execution_allowed is True
    assert validate_db_execution_request(req(dry_run=False, proposed_state='hard', operator_id=None)).execution_allowed is False
    assert validate_db_execution_request(req(dry_run=False, decision='manual_unhard')).execution_allowed is False

    repo=InMemoryAbuseTransitionExecutionRepo()
    assert execute_db_transition_controlled(req(), repo, dry_run=True).db_writes_executed is False
    assert execute_db_transition_controlled(req(dry_run=False,idempotency_key='k1'), repo, dry_run=False).db_writes_executed is True
    assert execute_db_transition_controlled(req(dry_run=False,idempotency_key='k1'), repo, dry_run=False).db_writes_executed is False
    assert execute_db_transition_controlled(req(dry_run=False,idempotency_key='k2',proposed_state='hard'), repo, dry_run=False).db_writes_executed is True

    cfg=load_config(Path('configs/mpf.example.yaml'))
    r=build_phase8_db_transition_execution_report(cfg)
    assert r['component']=='phase8_db_transition_execution'
    assert r['final_decision']=='BLOCKED'
    assert r['execution_allowed'] is False
    assert r['phase8_acceptance_allowed'] is False
    assert r['farm5_0_1_114_sync_evidence_present'] is True
    assert r['farm5_0_1_114_phase8_reports_evidence_present'] is True
    assert r['no_farm5_0_1_115_sync_evidence_claimed'] is True
    assert r['db_transition_execution_contract_defined'] is True
    assert r['synthetic_execution_scenarios_passed'] is True
    assert r['db_execution_authorized'] is False
    assert r['db_writes_authorized'] is False
    assert r['runtime_automation_authorized'] is False
    assert r['abuse_runner_authorized'] is False
    assert r['firewall_apply_authorized'] is False
    assert r['production_traffic_authorized'] is False
    assert r['hard_block_authorized'] is False
    assert r['pause_automation_authorized'] is False
    assert r['blockers'] == []

    out = CliRunner().invoke(app,['phase8','db-transition-execution','--config','configs/mpf.example.yaml','--output','json'])
    assert out.exit_code==0
    j=json.loads(out.stdout)
    assert j['final_decision']=='BLOCKED' and j['execution_allowed'] is False and j['db_execution_authorized'] is False and j['db_writes_authorized'] is False and j['synthetic_execution_scenarios_passed'] is True and j['blockers']==[]



def test_execution_checklist_uses_named_items() -> None:
    cfg=load_config(Path('configs/mpf.example.yaml'))
    r=build_phase8_db_transition_execution_report(cfg)
    items=[x['item'] for x in r['phase8_db_transition_execution_checklist']]
    assert "current_state_preserved" in items
    assert "future_runtime_worker_integration_pr_required" in items
    assert not any(i.isdigit() for i in items)


def _mk_repo(tmp_path: Path, phase_status: str, readme: str = "DB-only controlled transition execution package", index: str = "DB-only controlled transition execution", rules: str = "Phase 8 DB-only execution stop condition", remaining: str = "Current target is Phase 8 DB-only controlled transition execution package.", ai: str = "DB-Only Controlled Transition Execution") -> Path:
    repo = tmp_path / "repo"
    (repo / "docs/history").mkdir(parents=True)
    (repo / "README.md").write_text(readme, encoding="utf-8")
    (repo / "docs/history/PHASE_STATUS_LEGACY_0.1.302.md").write_text(phase_status, encoding="utf-8")
    (repo / "docs/INDEX.md").write_text(index, encoding="utf-8")
    (repo / "docs/AI_CODING_RULES.md").write_text(rules, encoding="utf-8")
    (repo / "docs/REMAINING_PHASE_PLAN.md").write_text(remaining, encoding="utf-8")
    (repo / "docs/AI_PHASE_8_TASK.md").write_text(ai, encoding="utf-8")
    return repo


def test_blockers_and_checklist_fail_closed_on_missing_prerequisites(tmp_path: Path) -> None:
    cfg = load_config(Path('configs/mpf.example.yaml'))
    repo = _mk_repo(tmp_path, phase_status='current_accepted_phase: Phase 7\ncurrent_working_phase: Phase 8\n')
    r = build_phase8_db_transition_execution_report(cfg, repo_root=repo)
    assert 'farm5_0_1_114_sync_evidence_present_missing_or_failed' in r['blockers']
    assert 'farm5_0_1_114_phase8_reports_evidence_present_missing_or_failed' in r['blockers']
    c = {i['item']: i['status'] for i in r['phase8_db_transition_execution_checklist']}
    assert c['farm5_0_1_114_sync_evidence_present'] == 'BLOCKED'


def test_blockers_on_fabricated_0_1_115_and_stale_docs(tmp_path: Path) -> None:
    cfg = load_config(Path('configs/mpf.example.yaml'))
    phase_status = 'current_accepted_phase: Phase 7\ncurrent_working_phase: Phase 8\nsynced to 0.1.114\ndb-transition-readiness\nsynced to 0.1.115\n'
    repo = _mk_repo(tmp_path, phase_status=phase_status, readme='stale', index='stale', rules='stale', remaining='stale', ai='stale')
    r = build_phase8_db_transition_execution_report(cfg, repo_root=repo)
    assert 'readme_current_gate_aligned_missing_or_failed' not in r['blockers']
    assert 'index_current_gate_aligned_missing_or_failed' not in r['blockers']
    assert 'ai_coding_rules_current_gate_aligned_missing_or_failed' in r['blockers']
    assert 'remaining_plan_db_execution_target_aligned_missing_or_failed' in r['blockers']


def test_blocker_when_previous_phase8_report_fails(tmp_path: Path) -> None:
    cfg = load_config(Path('configs/mpf.example.yaml'))
    phase_status = 'current_accepted_phase: Phase 6\ncurrent_working_phase: Phase 8\nsynced to 0.1.114\ndb-transition-readiness\n'
    repo = _mk_repo(tmp_path, phase_status=phase_status)
    r = build_phase8_db_transition_execution_report(cfg, repo_root=repo)
    assert 'current_state_preserved_missing_or_failed' in r['blockers']
