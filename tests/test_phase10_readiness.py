import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase10_readiness_service import build_phase10_readiness_report
from mpf.services.phase10_session_model_readiness_service import build_session_model_readiness_report
from mpf.services.phase10_worker_identity_readiness_service import build_worker_identity_readiness_report
from mpf.services.phase10_worker_policy_contract_readiness_service import build_worker_policy_contract_readiness_report
from mpf.services.phase10_implementation_readiness_service import build_phase10_implementation_readiness_report
from mpf.services.phase10_share_timeline_model_readiness_service import build_share_timeline_model_readiness_report
from mpf.services.phase10_collector_dry_run_gate_service import build_collector_dry_run_gate_readiness_report
from mpf.services.phase10_collector_dry_run_plan_service import build_collector_dry_run_plan_report
from mpf.services.phase10_runtime_worker_dry_run_readiness_service import build_runtime_worker_dry_run_readiness_report
from mpf.services.phase10_scheduler_dry_run_readiness_service import build_scheduler_dry_run_readiness_report
from mpf.services.phase10_worker_cycle_dry_run_plan_service import build_worker_cycle_dry_run_plan_report


def cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def test_phase10_readiness_accepted():
    r = build_phase10_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["latest_recorded_farm5_sync_evidence"] == "0.1.133"


def test_phase10_session_model_readiness_accepted():
    r = build_session_model_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["execution_allowed"] is False
    assert r["conntrack_capture_authorized"] is False
    assert r["tcpdump_authorized"] is False
    assert r["scheduler_authorized"] is False
    assert r["production_db_execution_authorized"] is False


def test_phase10_worker_identity_readiness_accepted():
    r = build_worker_identity_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["worker_enforcement_authorized"] is False
    assert r["worker_over_alone_must_not_harden"] is True
    assert r["farms_over_alone_must_not_harden"] is True
    assert r["miner_abuse_1h_invariant_preserved"] is True


def test_phase10_worker_policy_contract_readiness_accepted():
    r = build_worker_policy_contract_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["enforcement_enabled"] is False
    assert r["policy_enforcement_authorized"] is False
    assert r["firewall_mutation_authorized"] is False
    assert r["pause_automation_authorized"] is False
    assert r["hard_block_authorized"] is False


def test_phase10_implementation_readiness_accepted():
    r = build_phase10_implementation_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["execution_allowed"] is False
    assert r["share_timeline_model_readiness"] == "ACCEPTED"
    assert r["collector_dry_run_gate_readiness"] == "ACCEPTED"
    assert r["farm5_0_1_134_sync_test_evidence_present"] is True
    assert r["production_traffic_authorized"] is False
    assert r["firewall_apply_authorized"] is False
    assert r["abuse_automation_authorized"] is False
    assert r["scheduler_authorized"] is False
    assert r["collector_authorized"] is False
    assert r["ui_authorized"] is False
    assert r["telegram_authorized"] is False


def test_phase10_implementation_fail_closed_missing_evidence(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/PHASE_STATUS.md").write_text(Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8"), encoding="utf-8")
    r = build_phase10_implementation_readiness_report(cfg(), repo_root=tmp_path)
    assert r["final_decision"] == "BLOCKED"
    assert "farm5_0_1_134_sync_test_evidence_missing" in r["blockers"]


def test_phase10_implementation_fail_closed_missing_gate(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/PHASE_STATUS.md").write_text("invalid", encoding="utf-8")
    (tmp_path / "docs/PHASE_10_FARM5_0_1_134_SYNC_TEST_EVIDENCE.md").write_text("x", encoding="utf-8")
    r = build_phase10_implementation_readiness_report(cfg(), repo_root=tmp_path)
    assert r["final_decision"] == "BLOCKED"
    assert "current_phase_gate_missing_or_invalid" in r["blockers"]


def test_phase10_implementation_fail_closed_dangerous_flag_true(monkeypatch):
    from mpf.services import phase10_implementation_readiness_service as svc

    def fake(*args, **kwargs):
        return {"current_phase_gate_status": "OK", "production_traffic_authorized": True, "firewall_apply_authorized": False, "abuse_automation_authorized": False, "scheduler_authorized": False, "collector_authorized": False, "ui_authorized": False, "telegram_authorized": False}

    monkeypatch.setattr(svc, "build_phase10_readiness_report", fake)
    r = svc.build_phase10_implementation_readiness_report(cfg())
    assert r["final_decision"] == "BLOCKED"
    assert "dangerous_authorization_flag_enabled" in r["blockers"]


def test_phase10_new_cli_commands_json():
    runner = CliRunner()
    cmds = [
        ["phase10", "session-model-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "worker-identity-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "worker-policy-contract-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "implementation-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "share-timeline-model-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "collector-dry-run-gate-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "collector-dry-run-plan", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "runtime-worker-dry-run-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "scheduler-dry-run-readiness", "--config", "configs/mpf.example.yaml", "--output", "json"],
        ["phase10", "worker-cycle-dry-run-plan", "--config", "configs/mpf.example.yaml", "--output", "json"],
    ]
    for cmd in cmds:
        out = runner.invoke(app, cmd)
        assert out.exit_code == 0
        assert json.loads(out.stdout)["execution_allowed"] is False


def test_phase10_share_timeline_model_readiness_accepted():
    r = build_share_timeline_model_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["execution_allowed"] is False
    assert r["share_collector_authorized"] is False
    assert r["live_share_ingestion_authorized"] is False
    assert r["tcpdump_authorized"] is False
    assert r["conntrack_capture_authorized"] is False
    assert r["scheduler_authorized"] is False
    assert r["production_db_execution_authorized"] is False
    assert r["accepted_rejected_visibility_defined"] is True
    assert r["retention_policy_defined"] is True
    assert r["high_volume_guard_defined"] is True


def test_phase10_collector_dry_run_gate_readiness_accepted():
    r = build_collector_dry_run_gate_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["dry_run_only"] is True
    assert r["execution_allowed"] is False
    assert r["collector_daemon_authorized"] is False
    assert r["scheduler_authorized"] is False
    assert r["timer_authorized"] is False
    assert r["background_loop_authorized"] is False
    assert r["live_capture_authorized"] is False
    assert r["live_share_ingestion_authorized"] is False
    assert r["production_db_execution_authorized"] is False
    assert r["db_writes_authorized"] is False
    assert r["firewall_apply_authorized"] is False
    assert r["abuse_automation_authorized"] is False
    assert r["customer_mutation_authorized"] is False
    assert r["job_runs_logging_contract_defined"] is True
    assert r["scheduler_lock_contract_defined"] is True
    assert r["no_silent_skip_contract_defined"] is True


def test_phase10_collector_dry_run_plan_accepted():
    r = build_collector_dry_run_plan_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["plan_only"] is True
    assert r["execution_allowed"] is False
    assert r["would_write_tables"] == []
    assert r["would_create_job_run"] is False
    assert r["would_start_daemon"] is False
    assert r["would_schedule_timer"] is False
    assert r["would_touch_firewall"] is False
    assert r["would_mutate_customers"] is False
    assert len(r["sample_synthetic_events"]) >= 2


def test_phase10_runtime_worker_dry_run_readiness_accepted():
    r = build_runtime_worker_dry_run_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["dry_run_only"] is True
    assert r["execution_allowed"] is False
    assert r["worker_daemon_authorized"] is False
    assert r["worker_runtime_authorized"] is False
    assert r["scheduler_authorized"] is False
    assert r["timer_authorized"] is False
    assert r["background_loop_authorized"] is False


def test_phase10_scheduler_dry_run_readiness_accepted():
    r = build_scheduler_dry_run_readiness_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["dry_run_only"] is True
    assert r["execution_allowed"] is False
    assert r["scheduler_enabled"] is False
    assert r["timer_enabled"] is False


def test_phase10_worker_cycle_dry_run_plan_accepted():
    r = build_worker_cycle_dry_run_plan_report(cfg())
    assert r["final_decision"] == "ACCEPTED"
    assert r["plan_only"] is True
    assert r["dry_run_only"] is True
    assert r["execution_allowed"] is False
    assert r["would_write_tables"] == []
    assert r["would_create_job_run"] is False
    assert r["would_acquire_scheduler_lock"] is False
    assert r["would_start_daemon"] is False
    assert r["would_schedule_timer"] is False
    assert r["would_touch_firewall"] is False
    assert r["would_mutate_customers"] is False
    assert r["would_harden_abuse_state"] is False
    assert len(r["synthetic_cycle_steps"]) >= 5
    assert r["sample_cycle_result"]["hardening_actions"] == 0
    assert r["sample_cycle_result"]["firewall_actions"] == 0
    assert r["sample_cycle_result"]["customer_mutations"] == 0
