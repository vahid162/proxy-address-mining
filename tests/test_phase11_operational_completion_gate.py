from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_operational_completion_gap_inventory_service import (
    build_phase11_operational_completion_gap_inventory_report,
)

RUNNER = CliRunner()


def test_docs_define_phase11_operational_completion_gate() -> None:
    paths = (
        "README.md",
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/AI_PHASE_11_OPERATIONAL_COMPLETION_TASK.md",
        "docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md",
    )
    for path in paths:
        assert "Phase 11 operational completion" in Path(path).read_text(encoding="utf-8")


def test_index_current_phase_contracts_match_full_cli_production_scope() -> None:
    text = Path("docs/INDEX.md").read_text(encoding="utf-8")
    current = text.split("## Current Phase Contracts", 1)[1].split("## Reading Order by Task", 1)[0]

    assert "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5" in current
    assert "current_working_phase: Phase 11 operational completion — Full CLI Production Operations" in current
    assert "Phase 12 Worker Policy Enforcement remains blocked until final Phase 11 operational completion acceptance" in current
    assert "UI, Telegram, worker enforcement, buyer panel, public API, and public backend exposure remain closed" in current
    assert "Full CLI Production Operations acceptance must prove the expanded matrix" in current
    assert "production_firewall plan/apply/verify/rollback" not in current
    assert "Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5" not in current
    assert "Phase 11 — Production / Customer Activation Gate planning/readiness" not in current


def test_phase_status_blocks_phase12_and_later_interfaces() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    current = text.split("## Current State", 1)[1].split("```text", 1)[1].split("```", 1)[0]
    for expected in (
        "current_working_phase: Phase 11 operational completion — Full CLI Production Operations",
        "phase12_start_allowed: no",
        "worker_enforcement_allowed: no",
        "ui_allowed: no",
        "telegram_allowed: no",
    ):
        assert expected in current


def test_runtime_forward_pr_rule_is_recorded() -> None:
    for path in ("AGENTS.md", "docs/AI_CODING_RULES.md"):
        text = Path(path).read_text(encoding="utf-8")
        assert "Runtime-forward PR rule" in text
        assert "No two consecutive PRs in the same active phase/subphase may be report-only" in text


def test_gap_inventory_service_is_fail_closed_and_read_only() -> None:
    report = build_phase11_operational_completion_gap_inventory_report()
    assert report["final_decision"] == "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED"
    assert report["phase12_start_allowed"] is False
    assert report["phase11_operational_completion_scope"] == "full_cli_production_operations"
    for key in (
        "restart_autostart_proof",
        "production_customer_lifecycle_execution",
        "production_firewall_apply_verify_rollback",
        "production_onboarding_flow",
        "production_usage_report_check_evidence",
        "production_abuse_runner",
        "production_controls_pause_block_expire",
        "backup_restore_drill",
        "full_cli_production_operations",
    ):
        assert report[key] == "missing_or_partial"
    assert report["accepted_final_state_required"] == {
        "production_traffic": "cli_production",
        "customer_onboarding_allowed": "cli_production",
    }
    assert report["next_required_step"] == "prepare_live_ready_controlled_artifact_reapply_package"
    assert report["restart_autostart_proof_final_decision"] == "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"
    for key in (
        "mutation_performed",
        "db_mutation_performed",
        "firewall_apply_performed",
        "conntrack_flush_performed",
        "docker_restart_performed",
        "systemd_restart_performed",
    ):
        assert report[key] is False


def test_gap_inventory_cli_returns_fail_closed_json() -> None:
    result = RUNNER.invoke(app, ["production", "phase11-operational-completion-gap-inventory", "--output", "json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["repository_version"] == "0.1.278"
    assert report["final_decision"] == "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED"
    assert report["phase12_start_allowed"] is False
    assert report["mutation_performed"] is False


def test_gap_inventory_keeps_restart_autostart_blocked_on_persistence_gap() -> None:
    report = build_phase11_operational_completion_gap_inventory_report()

    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["next_required_step"] == "prepare_live_ready_controlled_artifact_reapply_package"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False


def test_gap_inventory_with_packet_path_evidence_advances_only_next_step(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    monkeypatch.setattr(svc, "run_phase11_restart_autostart_persistence_fix_plan", lambda config_path: {"final_decision": "x", "safety_blockers": [], "live_ready_package_available": False})
    monkeypatch.setattr(svc, "run_phase11_controlled_artifact_reapply_readiness", lambda config_path, packet_path_evidence_dir=None: {"final_decision": svc.READINESS_READY, "live_ready_package_available": True, "package_id": "pkg", "package_sha256": "sha", "blockers": []})

    report = svc.run_phase11_operational_completion_gap_inventory_report(packet_path_evidence_dir=tmp_path)

    assert report["next_required_step"] == "sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"


def test_gap_inventory_cli_accepts_packet_path_evidence_dir(monkeypatch, tmp_path) -> None:
    import mpf.interfaces.cli as cli

    seen = {}

    def fake_run(config_path, *, evidence_dir=None, packet_path_evidence_dir=None, lifecycle_execution_evidence_json=None):
        seen["packet_path_evidence_dir"] = packet_path_evidence_dir
        return {"component": "phase11_operational_completion_gap_inventory", "repository_version": "0.1.278", "final_decision": "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED", "phase12_start_allowed": False, "mutation_performed": False, "next_required_step": "sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5"}

    monkeypatch.setattr(cli.phase11_operational_completion_gap_inventory_service, "run_phase11_operational_completion_gap_inventory_report", fake_run)
    result = RUNNER.invoke(app, ["production", "phase11-operational-completion-gap-inventory", "--packet-path-evidence-dir", str(tmp_path), "--output", "json"])

    assert result.exit_code == 0, result.output
    assert Path(seen["packet_path_evidence_dir"]) == tmp_path
    assert json.loads(result.output)["next_required_step"] == "sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5"


def test_gap_inventory_sees_ready_restart_only_from_ready_proof(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    monkeypatch.setattr(svc, "build_phase11_restart_autostart_proof_report", lambda evidence_dir=None: {"restart_autostart_proof": "ready", "final_decision": "RESTART_AUTOSTART_PROOF_READY"})
    report = svc.build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)
    assert report["restart_autostart_proof"] == "ready"
    assert report["next_required_step"] == "implement_production_customer_lifecycle_execution"
    assert report["production_customer_lifecycle_execution_readiness"]["final_decision"] == "BLOCKED_PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_NOT_READY"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"


def test_production_customer_lifecycle_readiness_cli_is_safe() -> None:
    result = RUNNER.invoke(app, ["production", "production-customer-lifecycle-execution-readiness", "--output", "json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["production_customer_lifecycle_execution"] == "missing_or_partial"
    assert report["phase11_operational_completion_accepted"] is False
    assert report["mutation_performed"] is False
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"
