from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import firewall_apply_gate_readiness_service, firewall_restore_lock_record_execution_gate_service
from mpf.services.firewall_gate_review_service import build_gate_review_report
from mpf.services.firewall_planner_service import build_plan

RUNNER = CliRunner()


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def _base_text() -> str:
    return """## Current State\n```text\ncurrent_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5\ncurrent_working_phase: Phase 6 — Firewall Planner\nserver_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\nproxy_data_plane_allowed: limited_runtime_local_only\nui_allowed: no\ntelegram_allowed: no\nlive_snapshot_read_allowed: iptables_save_read_only\n```\nPhase 6 Read-Only iptables-save Snapshot — Server Evidence\nPhase 6 farm5 Time Synchronization — Server Evidence\nPhase 6 Restore/Lock/DB Apply Record Readiness — Server Sync\nPhase 6 Restore/Lock/DB Apply Record Gate — Proposal Boundary\nPhase 6 Restore/Lock/DB Apply Record Gate Report — Server Sync\nPhase 6 Restore/Lock/DB Apply Record Acceptance Gate — Server Sync\nSystem clock synchronized: yes\nNTPSynchronized=yes\n194.225.150.25\n"""


def test_service_blocked_and_not_authorized() -> None:
    r = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(_cfg())
    assert r["final_decision"] == "BLOCKED"
    assert r["authorization_status"] == "NOT_AUTHORIZED_FOR_EXECUTION"
    assert r["execution_allowed"] is False
    assert r["explicit_execution_authorization_present"] is False
    assert r["farm5_time_sync_resolved"] is True
    assert r["restore_lock_record_acceptance_gate_server_sync_evidence_present"] is True
    assert "explicit controlled restore point + lock + DB apply record execution authorization is not accepted" in r["blockers"]


def test_blocks_on_changed_current_state(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text(_base_text().replace("production_traffic: none", "production_traffic: yes"), encoding="utf-8")
    r = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(_cfg(), repo_root=tmp_path)
    assert "Current State does not match required gate" in r["blockers"]


def test_blocks_missing_time_sync_or_acceptance_sections(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    text = _base_text().replace("Phase 6 farm5 Time Synchronization — Server Evidence", "").replace("Phase 6 Restore/Lock/DB Apply Record Acceptance Gate — Server Sync", "")
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text(text, encoding="utf-8")
    r = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(_cfg(), repo_root=tmp_path)
    assert any("Time Synchronization" in b for b in r["blockers"])
    assert any("Acceptance Gate" in b for b in r["blockers"])


def test_blocks_on_non_plan_and_runtime_true() -> None:
    cfg = _cfg()
    cfg.firewall.apply_mode = "apply"
    cfg.proxy.runtime_activation_allowed = True
    r = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(cfg)
    assert "firewall.apply_mode is not plan_only" in r["blockers"]
    assert "proxy.runtime_activation_allowed is true" in r["blockers"]


def test_cli_human_json_invalid_output() -> None:
    human = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml"])
    assert human.exit_code == 0
    assert "final_decision: BLOCKED" in human.output
    assert "authorization_status: NOT_AUTHORIZED_FOR_EXECUTION" in human.output
    js = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--output", "json"])
    assert js.exit_code == 0
    assert '"component": "firewall_restore_lock_record_execution_gate"' in js.output
    bad = RUNNER.invoke(app, ["firewall", "restore-lock-record-execution-gate", "--config", "configs/mpf.example.yaml", "--output", "yaml"])
    assert bad.exit_code != 0


def test_integrations_remain_blocked() -> None:
    cfg = _cfg()
    eg = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(cfg)
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    review = build_gate_review_report(plan=plan, restore_lock_record_execution_gate=eg)
    assert review.restore_lock_record_execution_gate_summary["authorization_status"] == "NOT_AUTHORIZED_FOR_EXECUTION"
    assert review.final_decision == "BLOCKED"
    apply = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
    assert apply["restore_lock_record_execution_gate_present"] is True
    assert apply["restore_lock_record_execution_gate_authorization_status"] == "NOT_AUTHORIZED_FOR_EXECUTION"
    assert apply["restore_lock_record_execution_gate_final_decision"] == "BLOCKED"
    assert apply["restore_lock_record_execution_gate_execution_allowed"] is False
    assert apply["final_decision"] == "BLOCKED"


def test_static_safety_tokens() -> None:
    text = Path("mpf/services/firewall_restore_lock_record_execution_gate_service.py").read_text(encoding="utf-8").lower()
    forbidden = [
        "import subprocess", "subprocess.", "import os", "docker", "systemctl", "conntrack", "iptables-restore", "scheduler_locks", "firewall_applies", "open(", "write_text(", "mkdir(", "unlink(", "remove(", "rename(", "replace(", "insert ", "update ", "delete ",
    ]
    for token in forbidden:
        assert token not in text
