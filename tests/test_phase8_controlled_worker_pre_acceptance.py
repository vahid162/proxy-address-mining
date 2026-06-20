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
    assert not any('readme' in blocker.lower() or 'index' in blocker.lower() for blocker in r['blockers'])
    assert r['runtime_worker_dry_run_harness_present'] is True
    assert isinstance(r['blockers'], list)

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


def test_service_uses_named_runtime_first_template_and_keeps_all_authorizations_false(monkeypatch):
    import mpf.services.phase8_controlled_worker_pre_acceptance_service as svc

    read_paths: list[Path] = []
    original_read = svc._read

    def tracked_read(path: Path) -> str:
        read_paths.append(path)
        return original_read(path)

    monkeypatch.setattr(svc, "_read", tracked_read)
    r = svc.build_phase8_controlled_worker_pre_acceptance_report(cfg())

    assert r["pull_request_template_present"] is True
    assert "pull_request_template_present_missing_or_failed" not in r["blockers"]
    assert Path(".github/PULL_REQUEST_TEMPLATE/runtime-first.md") in [p.relative_to(Path.cwd()) for p in read_paths if p.is_relative_to(Path.cwd())]
    assert Path(".github/PULL_REQUEST_TEMPLATE.md") not in [p.relative_to(Path.cwd()) for p in read_paths if p.is_relative_to(Path.cwd())]
    assert r["final_decision"] == "BLOCKED"

    false_authorization_flags = [
        "execution_allowed",
        "phase8_acceptance_allowed",
        "runtime_worker_authorized",
        "scheduler_authorized",
        "timer_authorized",
        "abuse_runner_authorized",
        "production_db_execution_authorized",
        "db_writes_authorized",
        "firewall_apply_authorized",
        "production_traffic_authorized",
        "hard_block_authorized",
        "soft_block_authorized",
        "pause_automation_authorized",
        "ui_authorized",
        "telegram_authorized",
    ]
    for flag in false_authorization_flags:
        assert r[flag] is False


def test_remaining_plan_fallback_task_alignment_without_name_error(tmp_path, monkeypatch):
    import mpf.services.phase8_controlled_worker_pre_acceptance_service as svc

    def write(rel: str, content: str) -> None:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    write("docs/history/PHASE_STATUS_LEGACY_0.1.302.md", "current_accepted_phase: Phase 7\ncurrent_working_phase: Phase 8\nplanning/readiness\nsynced to 0.1.121\nsynced to 0.1.119\nproduction_traffic: none\nfirewall_apply_allowed: no\niptables-restore blocked\nabuse_automation_allowed: no\nui_allowed: no\ntelegram_allowed: no\n")
    write("docs/AI_CODING_RULES.md", "controlled worker dry-run gate stop condition\nAI agents use PR bodies as operational context\n")
    write("docs/AI_PHASE_8_TASK.md", "Phase 8 task text without the first alignment phrase.\n")
    write("docs/REMAINING_PHASE_PLAN.md", "Current target is Phase 8 controlled worker dry-run gate preparation package.\n")
    write(".github/PULL_REQUEST_TEMPLATE/runtime-first.md", "Why\nWhat\nHow to test\nVersion: X.Y.Z -> A.B.C\nRisk + Rollback\n")
    write("docs/ABUSE.md", "normal over_tracking over_grace hard 3600 firewall failure farms-over alone worker-over\n")
    write("VERSION", "0.1.122\n")

    blocked = {"component": "unused", "final_decision": "BLOCKED"}
    monkeypatch.setattr(svc, "build_phase8_abuse_state_machine_contract_report", lambda cfg, root: {**blocked, "component": "phase8_abuse_state_machine_contract"})
    monkeypatch.setattr(svc, "build_phase8_abuse_evidence_reporting_contract_report", lambda cfg, root: {**blocked, "component": "phase8_abuse_evidence_reporting_contract"})
    monkeypatch.setattr(svc, "build_phase8_abuse_dry_run_evaluator_report", lambda cfg, root: {**blocked, "component": "phase8_abuse_dry_run_evaluator"})
    monkeypatch.setattr(svc, "build_phase8_db_transition_readiness_report", lambda cfg, root: {**blocked, "component": "phase8_db_transition_readiness"})
    monkeypatch.setattr(svc, "build_phase8_db_transition_execution_report", lambda cfg, root: {**blocked, "component": "phase8_db_transition_execution"})
    monkeypatch.setattr(svc, "build_phase8_runtime_worker_integration_readiness_report", lambda cfg, root: {**blocked, "component": "phase8_runtime_worker_integration_readiness"})
    monkeypatch.setattr(svc, "build_phase8_runtime_worker_dry_run_harness_report", lambda cfg, root: {"component": "phase8_runtime_worker_dry_run_harness", "final_decision": "BLOCKED", "execution_allowed": False, "blockers": []})

    r = svc.build_phase8_controlled_worker_pre_acceptance_report(cfg(), repo_root=tmp_path)

    assert r["phase8_task_current_gate_aligned"] is True
    assert r["pull_request_template_present"] is True
    assert "pull_request_template_present_missing_or_failed" not in r["blockers"]
    assert r["final_decision"] == "BLOCKED"
