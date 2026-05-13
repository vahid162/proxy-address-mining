from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import firewall_apply_gate_readiness_service, firewall_restore_lock_record_readiness_service
from mpf.services.firewall_gate_review_service import build_gate_review_report
from mpf.services.firewall_planner_service import build_plan

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def _cfg():
    return load_config(example_config_path())


def test_service_blocked_and_not_authorized() -> None:
    report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(_cfg())
    assert report["final_decision"] == "BLOCKED"
    assert report["authorization_status"] == "NOT_AUTHORIZED_FOR_WRITES"


def test_snapshot_gate_and_evidence_present() -> None:
    report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(_cfg())
    assert report["read_only_snapshot_gate_authorized"] is True
    assert report["read_only_snapshot_evidence_present"] is True


def test_service_blocks_on_changed_current_state(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text("## Current State\n```text\nproduction_traffic: yes\n```\n", encoding="utf-8")
    report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(_cfg(), repo_root=tmp_path)
    assert any("Current State" in b for b in report["blockers"])


def test_service_blocks_when_evidence_missing(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text("## Current State\n```text\ncurrent_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5\ncurrent_working_phase: Phase 6 — Firewall Planner\nserver_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\nproxy_data_plane_allowed: limited_runtime_local_only\nui_allowed: no\ntelegram_allowed: no\nlive_snapshot_read_allowed: iptables_save_read_only\n```\n", encoding="utf-8")
    report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(_cfg(), repo_root=tmp_path)
    assert any("evidence section" in b for b in report["blockers"])


def test_service_blocks_on_non_plan_mode_and_runtime_true() -> None:
    cfg = _cfg()
    cfg.firewall.apply_mode = "apply"
    cfg.proxy.runtime_activation_allowed = True
    report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(cfg)
    assert "firewall.apply_mode is not plan_only" in report["blockers"]
    assert "proxy.runtime_activation_allowed is true" in report["blockers"]


def test_cli_human_and_json_and_invalid_output() -> None:
    human = RUNNER.invoke(app, ["firewall", "restore-lock-record-readiness", "--config", str(example_config_path())])
    assert human.exit_code == 0
    assert "final_decision: BLOCKED" in human.output
    assert "authorization_status: NOT_AUTHORIZED_FOR_WRITES" in human.output

    js = RUNNER.invoke(app, ["firewall", "restore-lock-record-readiness", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    assert '"authorization_status": "NOT_AUTHORIZED_FOR_WRITES"' in js.output
    assert '"final_decision": "BLOCKED"' in js.output

    bad = RUNNER.invoke(app, ["firewall", "restore-lock-record-readiness", "--config", str(example_config_path()), "--output", "yaml"])
    assert bad.exit_code != 0


def test_gate_review_and_apply_gate_include_compact_readiness() -> None:
    cfg = _cfg()
    readiness = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(cfg)
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    report = build_gate_review_report(plan=plan, restore_lock_record_readiness=readiness)
    assert report.restore_lock_record_readiness_summary["authorization_status"] == "NOT_AUTHORIZED_FOR_WRITES"
    assert report.final_decision == "BLOCKED"

    apply = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
    assert apply["restore_lock_record_readiness_present"] is True
    assert apply["restore_lock_record_readiness_final_decision"] == "BLOCKED"


def test_static_safety_no_forbidden_calls_or_imports() -> None:
    text = Path("mpf/services/firewall_restore_lock_record_readiness_service.py").read_text(encoding="utf-8").lower()
    forbidden = [
        "import subprocess",
        "subprocess.",
        "docker",
        "systemctl",
        "conntrack",
        "iptables-restore",
        "scheduler_locks",
        "firewall_applies",
    ]
    for token in forbidden:
        assert token not in text
