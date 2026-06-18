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
        "production_generic_real_customer_activation",
        "full_cli_production_operations",
    ):
        assert report[key] == "missing_or_partial"
    assert report["accepted_final_state_required"] == {
        "production_traffic": "cli_production",
        "customer_onboarding_allowed": "cli_production",
    }
    assert report["next_required_step"] == "controlled_artifact_reapply_readiness_snapshot_required"
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
    assert report["repository_version"] == "0.1.293"
    assert report["final_decision"] == "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED"
    assert report["phase12_start_allowed"] is False
    assert report["mutation_performed"] is False


def test_gap_inventory_keeps_restart_autostart_blocked_on_persistence_gap() -> None:
    report = build_phase11_operational_completion_gap_inventory_report()

    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["next_required_step"] == "controlled_artifact_reapply_readiness_snapshot_required"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False


def test_gap_inventory_with_packet_path_evidence_advances_only_next_step(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    monkeypatch.setattr(svc, "run_phase11_restart_autostart_persistence_fix_plan", lambda config_path: {"final_decision": "x", "safety_blockers": [], "live_ready_package_available": False})
    monkeypatch.setattr(svc, "run_phase11_controlled_artifact_reapply_readiness", lambda config_path, **kwargs: {"final_decision": svc.READINESS_READY, "live_ready_package_available": True, "package_id": "pkg", "package_sha256": "sha", "blockers": []})

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

    def fake_run(config_path, **kwargs):
        packet_path_evidence_dir = kwargs.get("packet_path_evidence_dir")
        seen["packet_path_evidence_dir"] = packet_path_evidence_dir
        return {"component": "phase11_operational_completion_gap_inventory", "repository_version": "0.1.293", "final_decision": "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED", "phase12_start_allowed": False, "mutation_performed": False, "next_required_step": "sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5"}

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


def test_firewall_completion_contract_fails_closed_on_partial_evidence(tmp_path) -> None:
    from mpf.services.phase11_production_firewall_apply_verify_rollback_readiness_service import build_production_firewall_apply_verify_rollback_readiness_report

    (tmp_path / "current-controlled-artifact-gate-with-target.json").write_text(json.dumps({
        "unknown_mpf_artifacts": [],
        "duplicate_nat_redirect_count": 0,
        "forbidden_public_runtime_exposure": False,
    }), encoding="utf-8")
    report = build_production_firewall_apply_verify_rollback_readiness_report(tmp_path)
    assert report["production_firewall_apply_verify_rollback"] == "missing_or_partial"
    for blocker in ("firewall_apply_evidence_missing", "firewall_post_apply_verify_missing", "firewall_rollback_contract_missing", "firewall_restore_point_or_backup_missing"):
        assert blocker in report["blockers"]
    assert report["phase12_start_allowed"] is False
    assert report["mutation_performed"] is False


def test_firewall_completion_accepts_target_aware_no_reapply_evidence(tmp_path) -> None:
    from mpf.services.phase11_production_firewall_apply_verify_rollback_readiness_service import build_production_firewall_apply_verify_rollback_readiness_report

    (tmp_path / "current-controlled-artifact-gate-target-aware.json").write_text(json.dumps({
        "final_decision": "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS",
        "unknown_mpf_artifacts": [],
        "duplicate_nat_redirect_count": 0,
        "forbidden_public_runtime_exposure": False,
        "backend_public_exposure": False,
        "mutation_performed": False,
    }), encoding="utf-8")
    (tmp_path / "controlled-artifact-reapply-readiness-target-aware.json").write_text(json.dumps({
        "final_decision": "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT",
        "controlled_artifact_reapply_required": False,
        "blockers": [],
        "mutation_performed": False,
        "phase12_start_allowed": False,
    }), encoding="utf-8")
    (tmp_path / "controlled-artifact-reapply-package.json").write_text(json.dumps({
        "final_decision": "NO_CONTROLLED_ARTIFACT_REAPPLY_REQUIRED",
        "package_id": "pkg",
        "package_sha256": "sha",
        "payload": "",
        "scope": [{"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101}],
        "mutation_performed": False,
    }), encoding="utf-8")

    report = build_production_firewall_apply_verify_rollback_readiness_report(tmp_path)

    assert report["production_firewall_apply_verify_rollback"] == "production_firewall_apply_verify_rollback_ready"
    assert report["final_decision"] == "PRODUCTION_FIREWALL_ALREADY_APPLIED_VERIFIED_NO_REAPPLY_REQUIRED"
    assert report["evidence_mode"] == "already_applied_no_reapply_required"
    assert report["no_reapply_required"] is True
    assert report["blockers"] == []
    assert report["mutation_performed"] is False
    assert report["phase12_start_allowed"] is False
    assert report["next_required_step"] == "production_onboarding_flow"


def test_gap_inventory_advances_to_onboarding_after_no_reapply_firewall_evidence(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    (tmp_path / "current-controlled-artifact-gate-target-aware.json").write_text(json.dumps({
        "unknown_mpf_artifacts": [],
        "duplicate_nat_redirect_count": 0,
        "forbidden_public_runtime_exposure": False,
    }), encoding="utf-8")
    (tmp_path / "controlled-artifact-reapply-readiness-target-aware.json").write_text(json.dumps({
        "final_decision": "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT",
        "controlled_artifact_reapply_required": False,
        "blockers": [],
        "mutation_performed": False,
    }), encoding="utf-8")
    (tmp_path / "controlled-artifact-reapply-package.json").write_text(json.dumps({
        "final_decision": "NO_CONTROLLED_ARTIFACT_REAPPLY_REQUIRED",
        "package_id": "pkg",
        "package_sha256": "sha",
        "payload": "",
        "scope": [{"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101}],
        "mutation_performed": False,
    }), encoding="utf-8")
    _write_ready_restart_proof(tmp_path / "restart-autostart-proof")
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *args, **kwargs: {"production_customer_lifecycle_execution": "controlled_execution_evidence_ready", "final_decision": "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"})

    report = svc.build_phase11_operational_completion_gap_inventory_report(
        evidence_dir=tmp_path,
        firewall_completion_evidence_dir=tmp_path,
        onboarding_readiness={"production_onboarding_flow": "missing_or_partial"},
    )

    assert report["production_customer_lifecycle_execution"] == "controlled_execution_evidence_ready"
    assert report["production_firewall_apply_verify_rollback"] == "production_firewall_apply_verify_rollback_ready"
    assert report["next_required_step"] == "production_onboarding_flow"
    assert report["phase12_start_allowed"] is False


def test_gap_inventory_does_not_advance_firewall_from_missing_completion_evidence() -> None:
    report = build_phase11_operational_completion_gap_inventory_report(
        persistence_plan_report={"final_decision": "x", "safety_blockers": []},
        lifecycle_execution_evidence_json=None,
    )
    assert report["production_firewall_apply_verify_rollback"] == "missing_or_partial"
    assert report["production_firewall_apply_verify_rollback_readiness"] is None


def test_gap_inventory_consumes_no_reapply_readiness_from_evidence_dir(tmp_path) -> None:
    (tmp_path / "controlled-artifact-reapply-readiness-target-aware.json").write_text(json.dumps({
        "final_decision": "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT",
        "controlled_artifact_reapply_required": False,
        "live_ready_package_available": False,
        "production_execution_available": False,
        "controlled_artifact_execute_available": False,
        "iptables_restore_invocation_allowed": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "blockers": [],
    }), encoding="utf-8")

    report = build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)

    assert report["next_required_step"] == "production_firewall_apply_verify_rollback"
    assert report["next_required_step"] != "prepare_live_ready_controlled_artifact_reapply_package"
    summary = report["restart_autostart_persistence_fix_plan_summary"]
    assert summary["live_ready_controlled_artifact_reapply_readiness_final_decision"] == "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT"
    assert summary["readiness_blockers"] == []
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"
    for key in ("mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed"):
        assert report[key] is False


def test_gap_inventory_advances_to_controls_when_no_reapply_and_prior_surfaces_ready(tmp_path) -> None:
    report = build_phase11_operational_completion_gap_inventory_report(
        evidence_dir=tmp_path,
        readiness_report={"final_decision": "NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT", "blockers": []},
        lifecycle_execution_evidence_json=None,
        firewall_completion_evidence_dir=None,
        controls_readiness={"production_controls_pause_block_expire": "missing_or_partial"},
        backup_restore_readiness={"backup_restore_drill": "missing_or_partial"},
    )
    # Without lifecycle/firewall evidence, no-reapply only clears stale reapply work and points at the next true blocker.
    assert report["next_required_step"] == "production_firewall_apply_verify_rollback"
    assert report["full_cli_production_operations"] == "missing_or_partial"


def _write_ready_restart_proof(path: Path) -> None:
    from mpf import __version__

    path.mkdir(parents=True, exist_ok=True)
    values = {
        "repository_version.txt": __version__,
        "phase_status.txt": "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5\ncurrent_working_phase: Phase 11 operational completion — Full CLI Production Operations\nphase12_start_allowed: no\nworker_enforcement_allowed: no\nui_allowed: no\ntelegram_allowed: no\nproduction_traffic: controlled_cli_limited\ncustomer_onboarding_allowed: controlled_cli_limited\n",
        "mpf_version.txt": __version__,
        "db_ping.txt": "OK",
        "db_status.txt": "database: OK\nalembic_version: x\nlanes: 1\ncustomers: 2\n",
        "lanes.txt": "btc enabled",
        "customers.txt": "canary-btc-001\nlimited-btc-001\n",
        "docker_ps.txt": "v2raya Up\nbtc running",
        "container_listener_order.txt": "v2raya 127.0.0.1:2015 before btc 127.0.0.1:60010",
        "listeners.txt": "127.0.0.1:2015\n127.0.0.1:60010\n",
        "phase11_firewall_artifacts.txt": "known_controlled_phase11_artifacts: present",
        "unknown_mpf_firewall_artifacts.txt": "unknown_mpf_firewall_artifacts: []",
        "mutation_flags.json": json.dumps({
            "mutation_performed": False,
            "db_mutation_performed": False,
            "firewall_apply_performed": False,
            "conntrack_flush_performed": False,
            "docker_restart_performed": False,
            "systemd_restart_performed": False,
        }),
        "proof-report.json": json.dumps({"restart_autostart_proof": "ready", "final_decision": "RESTART_AUTOSTART_PROOF_READY"}),
    }
    for name, value in values.items():
        (path / name).write_text(value, encoding="utf-8")


def _ready_firewall_json() -> dict[str, object]:
    return {
        "production_firewall_apply_verify_rollback": "production_firewall_apply_verify_rollback_ready",
        "final_decision": "PRODUCTION_FIREWALL_ALREADY_APPLIED_VERIFIED_NO_REAPPLY_REQUIRED",
        "blockers": [],
        "phase12_start_allowed": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
    }


def test_gap_inventory_resolves_nested_restart_autostart_proof(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    nested = tmp_path / "restart-autostart-proof"
    _write_ready_restart_proof(nested)
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution": "missing_or_partial"})

    report = svc.build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)

    assert report["restart_autostart_proof"] == "ready"
    assert report["restart_autostart_evidence_layout"] == "nested_collector"
    assert Path(report["restart_autostart_evidence_dir"]) == nested


def test_gap_inventory_preserves_direct_restart_autostart_proof_layout(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    _write_ready_restart_proof(tmp_path)
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution": "missing_or_partial"})

    report = svc.build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)

    assert report["restart_autostart_proof"] == "ready"
    assert report["restart_autostart_evidence_layout"] == "direct_legacy"


def test_gap_inventory_restart_proof_fails_closed_on_malformed_nested_report(tmp_path) -> None:
    nested = tmp_path / "restart-autostart-proof"
    _write_ready_restart_proof(nested)
    (nested / "proof-report.json").write_text("{", encoding="utf-8")

    report = build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)

    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["restart_autostart_evidence_layout"] == "nested_collector"
    assert "malformed_json_evidence:proof-report.json" in report["restart_autostart_proof_final_decision"] or report["restart_autostart_proof_final_decision"] == "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"


def test_gap_inventory_consumes_valid_firewall_completion_readiness_json(tmp_path) -> None:
    (tmp_path / "production-firewall-apply-verify-rollback-readiness.json").write_text(json.dumps(_ready_firewall_json()), encoding="utf-8")

    report = build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)

    assert report["production_firewall_apply_verify_rollback"] == "production_firewall_apply_verify_rollback_ready"
    assert report["production_firewall_apply_verify_rollback_readiness"]["blockers"] == []
    assert report["phase12_start_allowed"] is False


def test_gap_inventory_firewall_completion_readiness_json_fails_closed_when_unsafe(tmp_path) -> None:
    unsafe = _ready_firewall_json() | {"firewall_apply_performed": True}
    (tmp_path / "production-firewall-apply-verify-rollback-readiness.json").write_text(json.dumps(unsafe), encoding="utf-8")

    report = build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)

    assert report["production_firewall_apply_verify_rollback"] == "missing_or_partial"
    assert "firewall_completion_readiness_json_unsafe" in report["production_firewall_apply_verify_rollback_readiness"]["blockers"]



def test_gap_inventory_progresses_to_usage_when_onboarding_ready_but_usage_missing(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    _write_ready_restart_proof(tmp_path / "restart-autostart-proof")
    (tmp_path / "production-firewall-apply-verify-rollback-readiness.json").write_text(json.dumps(_ready_firewall_json()), encoding="utf-8")
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution": "controlled_execution_evidence_ready", "final_decision": "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"})

    report = svc.build_phase11_operational_completion_gap_inventory_report(
        evidence_dir=tmp_path,
        onboarding_readiness={"production_onboarding_flow": "production_onboarding_flow_ready"},
        usage_report_check_surface={"usage_report_check_surface_ready": False, "final_decision": "BLOCKED_USAGE_REPORT_CHECK_SURFACE", "blockers": ["usage_evidence_missing"]},
    )

    assert report["next_required_step"] == "production_usage_report_check_evidence"
    assert report["phase12_start_allowed"] is False


def test_gap_inventory_progresses_to_abuse_when_usage_ready_but_abuse_missing(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    _write_ready_restart_proof(tmp_path / "restart-autostart-proof")
    (tmp_path / "production-firewall-apply-verify-rollback-readiness.json").write_text(json.dumps(_ready_firewall_json()), encoding="utf-8")
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution": "controlled_execution_evidence_ready", "final_decision": "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"})

    report = svc.build_phase11_operational_completion_gap_inventory_report(
        evidence_dir=tmp_path,
        onboarding_readiness={"production_onboarding_flow": "production_onboarding_flow_ready"},
        usage_report_check_surface={"usage_report_check_surface_ready": True, "final_decision": "USAGE_REPORT_CHECK_SURFACE_READY", "blockers": []},
        abuse_runner_readiness={"production_abuse_runner": "missing_or_partial", "blockers": ["abuse_evidence_missing"]},
    )

    assert report["next_required_step"] == "production_abuse_runner"
    assert report["phase12_start_allowed"] is False

def test_gap_inventory_progresses_to_controls_with_ready_prior_surfaces(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    _write_ready_restart_proof(tmp_path / "restart-autostart-proof")
    (tmp_path / "production-firewall-apply-verify-rollback-readiness.json").write_text(json.dumps(_ready_firewall_json()), encoding="utf-8")
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution": "controlled_execution_evidence_ready", "final_decision": "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"})

    report = svc.build_phase11_operational_completion_gap_inventory_report(
        evidence_dir=tmp_path,
        onboarding_readiness={"production_onboarding_flow": "production_onboarding_flow_ready"},
        usage_report_check_surface={"usage_report_check_surface_ready": True, "final_decision": "USAGE_REPORT_CHECK_SURFACE_READY", "blockers": []},
        abuse_runner_readiness={"production_abuse_runner": "production_abuse_runner_ready"},
        controls_readiness={"production_controls_pause_block_expire": "missing_or_partial", "blockers": ["block_capability_not_defined"]},
        backup_restore_readiness={"backup_restore_drill": "missing_or_partial"},
    )

    assert report["next_required_step"] == "production_controls_pause_block_expire"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False

def test_gap_inventory_progresses_to_backup_restore_when_controls_ready(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    _write_ready_restart_proof(tmp_path / "restart-autostart-proof")
    (tmp_path / "production-firewall-apply-verify-rollback-readiness.json").write_text(json.dumps(_ready_firewall_json()), encoding="utf-8")
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution": "controlled_execution_evidence_ready", "final_decision": "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"})

    report = svc.build_phase11_operational_completion_gap_inventory_report(
        evidence_dir=tmp_path,
        onboarding_readiness={"production_onboarding_flow": "production_onboarding_flow_ready"},
        usage_report_check_surface={"usage_report_check_surface_ready": True, "final_decision": "USAGE_REPORT_CHECK_SURFACE_READY", "blockers": []},
        abuse_runner_readiness={"production_abuse_runner": "production_abuse_runner_ready"},
        controls_readiness={"production_controls_pause_block_expire": "production_controls_pause_block_expire_ready", "production_controls_pause_block_expire_ready": True, "blockers": []},
        backup_restore_readiness={"backup_restore_drill": "missing_or_partial"},
    )

    assert report["next_required_step"] == "backup_restore_drill"
    assert report["backup_restore_drill"] == "missing_or_partial"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == report["ui_allowed"] == report["telegram_allowed"] == "no"


def test_gap_inventory_no_evidence_does_not_call_live_controls_readiness(monkeypatch) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    def fail_if_called(*args, **kwargs):
        raise AssertionError("live controls readiness must not be called without explicit evidence")

    monkeypatch.setattr(svc, "run_phase11_production_controls_pause_block_expire_readiness_report", fail_if_called)

    report = svc.build_phase11_operational_completion_gap_inventory_report()

    assert report["production_controls_pause_block_expire"] == "missing_or_partial"
    assert report["production_controls_pause_block_expire_readiness"]["production_controls_pause_block_expire"] == "missing_or_partial"
    assert "production_controls_pause_block_expire_evidence_missing" in report["production_controls_pause_block_expire_readiness"]["blockers"]
    assert report["phase12_start_allowed"] is False
    for key in ("mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed"):
        assert report[key] is False


def test_gap_inventory_honors_explicit_controls_readiness_ready() -> None:
    report = build_phase11_operational_completion_gap_inventory_report(
        controls_readiness={
            "production_controls_pause_block_expire": "production_controls_pause_block_expire_ready",
            "production_controls_pause_block_expire_ready": True,
            "blockers": [],
            "mutation_performed": False,
            "phase12_start_allowed": False,
        }
    )

    assert report["production_controls_pause_block_expire"] == "production_controls_pause_block_expire_ready"
    assert report["production_controls_pause_block_expire_readiness"]["production_controls_pause_block_expire_ready"] is True
    assert report["phase12_start_allowed"] is False


def _ready_controls_json() -> dict[str, object]:
    return {
        "component": "phase11_production_controls_pause_block_expire_readiness",
        "repository_version": "0.1.293",
        "phase11_operational_completion_required": True,
        "readiness_scope": "read_only_controls_preflight",
        "target_customer_key": "limited-btc-001",
        "operator": "pytest",
        "evidence_collected_at": "2026-06-17T00:00:00Z",
        "scope": "limited-btc-001/btc/20101",
        "ready": True,
        "pause_preflight": {"ready": True},
        "expire_run_preflight": {"ready": True},
        "block_preflight": {"ready": True},
        "production_controls_pause_block_expire": "production_controls_pause_block_expire_ready",
        "production_controls_pause_block_expire_ready": True,
        "blockers": [],
        "warnings": [],
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "final_decision": "PRODUCTION_CONTROLS_PAUSE_BLOCK_EXPIRE_READY",
    }


def test_gap_inventory_honors_controls_evidence_json(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    monkeypatch.setattr(
        svc,
        "run_phase11_production_controls_pause_block_expire_readiness_report",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must consume explicit evidence JSON instead")),
    )
    (tmp_path / "production-controls-pause-block-expire-readiness.json").write_text(json.dumps(_ready_controls_json()), encoding="utf-8")

    report = svc.build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)

    assert report["production_controls_pause_block_expire"] == "production_controls_pause_block_expire_ready"
    assert report["production_controls_pause_block_expire_readiness"]["production_controls_pause_block_expire_ready"] is True
    assert report["production_controls_pause_block_expire_readiness"]["contract_readiness"]["mutation_performed"] is False
    assert report["phase12_start_allowed"] is False


def test_gap_inventory_controls_evidence_and_ready_prior_surfaces_advance_to_backup_restore(monkeypatch, tmp_path) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    _write_ready_restart_proof(tmp_path / "restart-autostart-proof")
    (tmp_path / "production-firewall-apply-verify-rollback-readiness.json").write_text(json.dumps(_ready_firewall_json()), encoding="utf-8")
    (tmp_path / "production-controls-pause-block-expire-readiness.json").write_text(json.dumps(_ready_controls_json()), encoding="utf-8")
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution": "controlled_execution_evidence_ready", "final_decision": "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY"})

    report = svc.build_phase11_operational_completion_gap_inventory_report(
        evidence_dir=tmp_path,
        onboarding_readiness={"production_onboarding_flow": "production_onboarding_flow_ready"},
        usage_report_check_surface={"usage_report_check_surface_ready": True, "final_decision": "USAGE_REPORT_CHECK_SURFACE_READY", "blockers": []},
        abuse_runner_readiness={"production_abuse_runner": "production_abuse_runner_ready"},
    )

    assert report["next_required_step"] == "backup_restore_drill"
    assert report["backup_restore_drill"] == "missing_or_partial"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == report["ui_allowed"] == report["telegram_allowed"] == "no"


def test_gap_inventory_cli_no_evidence_controls_remains_fail_closed_and_read_only(monkeypatch) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc

    def fail_if_called(*args, **kwargs):
        raise AssertionError("CLI no-evidence inventory must not call live controls readiness")

    monkeypatch.setattr(svc, "run_phase11_production_controls_pause_block_expire_readiness_report", fail_if_called)
    result = RUNNER.invoke(app, ["production", "phase11-operational-completion-gap-inventory", "--output", "json"])

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["production_controls_pause_block_expire"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False
    for key in ("mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed"):
        assert report[key] is False


def test_phase11_completion_matrix_has_10_items_and_final_acceptance_last() -> None:
    text = Path("docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md").read_text(encoding="utf-8")
    assert "9. production generic real-customer activation" in text
    assert "10. final acceptance" in text
    assert text.index("9. production generic real-customer activation") < text.index("10. final acceptance")


def test_gap_inventory_generic_activation_blocks_final_acceptance_when_first_8_ready() -> None:
    report = build_phase11_operational_completion_gap_inventory_report(
        readiness_report={"final_decision":"NO_REAPPLY_REQUIRED_CONTROLLED_ARTIFACTS_PRESENT","blockers":[]},
        lifecycle_execution_evidence_json=None,
        firewall_completion_readiness={"production_firewall_apply_verify_rollback":"production_firewall_apply_verify_rollback_ready","final_decision":"PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE_READY","blockers":[],"phase12_start_allowed":False},
        onboarding_readiness={"production_onboarding_flow":"production_onboarding_flow_ready"},
        usage_report_check_surface={"usage_report_check_surface_ready":True,"final_decision":"USAGE_REPORT_CHECK_SURFACE_READY","blockers":[]},
        abuse_runner_readiness={"production_abuse_runner":"production_abuse_runner_ready"},
        controls_readiness={"production_controls_pause_block_expire":"production_controls_pause_block_expire_ready"},
        backup_restore_readiness={"backup_restore_drill":"backup_restore_drill_ready"},
    )
    # restart/lifecycle remain fail-closed here; explicit direct test below covers all prior items.
    assert report["production_generic_real_customer_activation"] == "missing_or_partial"
    assert report["full_cli_production_operations"] == "missing_or_partial"


def test_gap_inventory_next_step_generic_activation_before_final_acceptance(monkeypatch) -> None:
    import mpf.services.phase11_operational_completion_gap_inventory_service as svc
    monkeypatch.setattr(svc, "build_phase11_restart_autostart_proof_report", lambda evidence_dir=None: {"restart_autostart_proof":"ready","final_decision":"RESTART_AUTOSTART_PROOF_READY"})
    monkeypatch.setattr(svc, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution":"controlled_execution_evidence_ready"})
    report = svc.build_phase11_operational_completion_gap_inventory_report(
        evidence_dir=Path('.'),
        firewall_completion_readiness={"production_firewall_apply_verify_rollback":"production_firewall_apply_verify_rollback_ready","final_decision":"PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE_READY","blockers":[],"phase12_start_allowed":False},
        onboarding_readiness={"production_onboarding_flow":"production_onboarding_flow_ready"},
        usage_report_check_surface={"usage_report_check_surface_ready":True,"final_decision":"USAGE_REPORT_CHECK_SURFACE_READY","blockers":[]},
        abuse_runner_readiness={"production_abuse_runner":"production_abuse_runner_ready"},
        controls_readiness={"production_controls_pause_block_expire":"production_controls_pause_block_expire_ready"},
        backup_restore_readiness={"backup_restore_drill":"backup_restore_drill_ready"},
        generic_activation_readiness={"production_generic_real_customer_activation":"missing_or_partial"},
    )
    assert report["next_required_step"] == "production_generic_real_customer_activation"
    assert report["next_required_step"] != "final_phase11_operational_completion_acceptance"
    assert report["full_cli_production_operations_acceptance_pr_required"] is False
