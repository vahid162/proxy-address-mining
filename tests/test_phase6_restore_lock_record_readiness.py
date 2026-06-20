from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import firewall_apply_gate_readiness_service, firewall_restore_lock_record_gate_service, firewall_restore_lock_record_readiness_service
from mpf.services.firewall_gate_review_service import build_gate_review_report
from mpf.services.firewall_planner_service import build_plan

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def _cfg():
    return load_config(example_config_path())


def _good_phase_status() -> str:
    return """## Current State\n```text\ncurrent_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5\ncurrent_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness\nserver_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\nproxy_data_plane_allowed: limited_runtime_local_only\nui_allowed: no\ntelegram_allowed: no\nphase12_start_allowed: no\nlive_snapshot_read_allowed: iptables_save_read_only\n```\n\nPhase 6 Read-Only iptables-save Snapshot — Server Evidence\nPhase 6 Restore/Lock/DB Apply Record Readiness — Server Sync\nPhase 6 Restore/Lock/DB Apply Record Gate — Proposal Boundary\n"""


def test_service_returns_blocked_and_not_accepted() -> None:
    report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(_cfg())
    assert report["final_decision"] == "BLOCKED"
    assert report["authorization_status"] == "NOT_ACCEPTED"


def test_service_confirms_proposal_boundary_and_evidence() -> None:
    report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(_cfg())
    assert report["proposal_boundary_present"] is True
    assert report["read_only_snapshot_evidence_present"] is True
    assert report["restore_lock_record_readiness_evidence_present"] is True


def test_service_blocks_on_changed_current_state(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text("## Current State\n```text\nproduction_traffic: yes\n```", encoding="utf-8")
    report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(_cfg(), repo_root=tmp_path)
    assert "Current State does not match required gate" in report["blockers"]


def test_service_blocks_when_sections_missing(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text(_good_phase_status().replace("Phase 6 Restore/Lock/DB Apply Record Gate — Proposal Boundary", ""), encoding="utf-8")
    report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(_cfg(), repo_root=tmp_path)
    assert any("Proposal Boundary" in b for b in report["blockers"])


def test_service_blocks_when_snapshot_section_missing(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text(_good_phase_status().replace("Phase 6 Read-Only iptables-save Snapshot — Server Evidence", ""), encoding="utf-8")
    report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(_cfg(), repo_root=tmp_path)
    assert any("Read-Only iptables-save Snapshot" in b for b in report["blockers"])


def test_service_blocks_when_readiness_section_missing(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_STATUS.md").write_text(_good_phase_status().replace("Phase 6 Restore/Lock/DB Apply Record Readiness — Server Sync", ""), encoding="utf-8")
    report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(_cfg(), repo_root=tmp_path)
    assert any("Readiness" in b for b in report["blockers"])


def test_service_blocks_on_non_plan_mode_and_runtime_true() -> None:
    cfg = _cfg()
    cfg.firewall.apply_mode = "apply"
    cfg.proxy.runtime_activation_allowed = True
    report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(cfg)
    assert "firewall.apply_mode is not plan_only" in report["blockers"]
    assert "proxy.runtime_activation_allowed is true" in report["blockers"]


def test_cli_human_json_invalid_output() -> None:
    human = RUNNER.invoke(app, ["firewall", "restore-lock-record-gate", "--config", str(example_config_path())])
    assert human.exit_code == 0
    assert "final_decision: BLOCKED" in human.output
    assert "authorization_status: NOT_ACCEPTED" in human.output

    js = RUNNER.invoke(app, ["firewall", "restore-lock-record-gate", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    assert '"final_decision": "BLOCKED"' in js.output
    assert '"authorization_status": "NOT_ACCEPTED"' in js.output

    bad = RUNNER.invoke(app, ["firewall", "restore-lock-record-gate", "--config", str(example_config_path()), "--output", "yaml"])
    assert bad.exit_code != 0


def test_gate_review_and_apply_gate_integrations() -> None:
    cfg = _cfg()
    gate_report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(cfg)
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    review = build_gate_review_report(plan=plan, restore_lock_record_gate=gate_report)
    assert review.restore_lock_record_gate_summary["final_decision"] == "BLOCKED"
    assert review.final_decision == "BLOCKED"

    apply = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
    assert apply["restore_lock_record_gate_present"] is True
    assert apply["restore_lock_record_gate_authorization_status"] == "NOT_ACCEPTED"
    assert apply["restore_lock_record_gate_final_decision"] == "BLOCKED"
    assert apply["final_decision"] == "BLOCKED"


def test_static_safety_no_forbidden_tokens() -> None:
    text = Path("mpf/services/firewall_restore_lock_record_gate_service.py").read_text(encoding="utf-8").lower()
    forbidden = [
        "import subprocess",
        "subprocess.",
        "docker",
        "systemctl",
        "conntrack",
        "iptables-restore",
        "scheduler_locks",
        "firewall_applies",
        "open(",
        ".write_text(",
    ]
    for token in forbidden:
        assert token not in text


def test_readiness_command_still_not_authorized_for_writes() -> None:
    report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(_cfg())
    assert report["authorization_status"] == "NOT_AUTHORIZED_FOR_WRITES"
    res = RUNNER.invoke(app, ["firewall", "restore-lock-record-readiness", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"authorization_status": "NOT_AUTHORIZED_FOR_WRITES"' in res.output


def test_invalid_output_fails_for_both_commands() -> None:
    bad_ready = RUNNER.invoke(app, ["firewall", "restore-lock-record-readiness", "--config", str(example_config_path()), "--output", "yaml"])
    bad_gate = RUNNER.invoke(app, ["firewall", "restore-lock-record-gate", "--config", str(example_config_path()), "--output", "yaml"])
    assert bad_ready.exit_code != 0
    assert bad_gate.exit_code != 0


def test_gate_review_preserves_readiness_and_gate_summaries() -> None:
    cfg = _cfg()
    gate_report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(cfg)
    readiness_report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(cfg)
    plan = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[])
    review = build_gate_review_report(plan=plan, restore_lock_record_gate=gate_report, restore_lock_record_readiness=readiness_report)
    assert review.restore_lock_record_gate_summary["authorization_status"] == "NOT_ACCEPTED"
    assert review.restore_lock_record_readiness_summary["authorization_status"] == "NOT_AUTHORIZED_FOR_WRITES"
    assert review.final_decision == "BLOCKED"


def test_apply_gate_readiness_contains_gate_and_readiness_fields() -> None:
    apply = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(_cfg())
    assert apply["restore_lock_record_readiness_present"] is True
    assert apply["restore_lock_record_readiness_authorization_status"] == "NOT_AUTHORIZED_FOR_WRITES"
    assert apply["restore_lock_record_readiness_final_decision"] == "BLOCKED"
    assert apply["restore_lock_record_gate_present"] is True
    assert apply["restore_lock_record_gate_authorization_status"] == "NOT_ACCEPTED"
    assert apply["restore_lock_record_gate_final_decision"] == "BLOCKED"


def test_phase_status_docs_mentions_readiness_vs_gate_distinction() -> None:
    text = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8")
    assert "`restore-lock-record-readiness` remains report-only readiness" in text
    assert "`restore-lock-record-gate` is the proposal-boundary/preflight" in text


def test_no_new_docs_created() -> None:
    assert not Path("docs/PHASE_6_RESTORE_LOCK_RECORD_GATE.md").exists()
