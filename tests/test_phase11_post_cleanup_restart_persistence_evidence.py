from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from mpf import __version__
from mpf.interfaces.cli import app
from mpf.services.phase11_current_controlled_artifact_gate_service import build_phase11_current_controlled_artifact_gate_report
from mpf.services.phase11_post_cleanup_restart_persistence_evidence_service import build_phase11_post_cleanup_restart_persistence_evidence_report

PHASE = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
SNAP = """*nat
:MPF_NAT_PRE - [0:0]
-A PREROUTING -p tcp -m comment --comment "mpf:hook:nat_prerouting" -j MPF_NAT_PRE
-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.2:60010
-A MPF_NAT_PRE -p tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.2:60010
COMMIT
"""


def test_restart_autostart_scripts_use_expected_backend_target_and_current_version() -> None:
    for script in [
        Path("scripts/phase11_collect_restart_autostart_proof.sh"),
        Path("scripts/phase11_collect_restart_autostart_proof_after_persistence_fix.sh"),
    ]:
        text = script.read_text(encoding="utf-8")
        assert "0.1.246" not in text
        assert "controlled-backend-target.json" in text
        assert "expected-backend-target.txt" in text
        assert "--expected-backend-target" in text
        assert 'VERSION="0.1.246"' not in text


def test_post_cleanup_bundle_script_is_read_only_and_collects_nested_reports() -> None:
    text = Path("scripts/phase11_collect_post_cleanup_restart_persistence_evidence.sh").read_text(encoding="utf-8")
    assert "controlled-backend-target.json" in text
    assert "current-controlled-artifact-gate.json" in text
    assert "--expected-backend-target" in text
    assert "controlled-artifact-persistence-plan" in text
    assert "restart-autostart-proof" in text
    assert "phase11-operational-completion-gap-inventory" in text
    assert "summary.json" in text and "manifest.json" in text
    forbidden = ["docker restart", "systemctl restart", " reboot", "iptables-restore", "conntrack -F"]
    assert not any(item in text for item in forbidden)
    assert '"mutation_performed":false' in text


def test_expected_backend_target_prevents_false_unknown_artifacts_and_counts_cleanup() -> None:
    report = build_phase11_current_controlled_artifact_gate_report(
        iptables_save_text=SNAP,
        phase_status_text=PHASE,
        expected_backend_target="172.18.0.2:60010",
    )
    assert report["final_decision"] == "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS"
    assert report["unknown_mpf_artifacts"] == []
    assert report["duplicate_nat_redirect_count"] == 0
    assert report["duplicate_controlled_artifact_count"] == 0
    assert report["known_controlled_artifacts_present"] is True
    assert report["production_gates_remain_closed"] is True


def test_backend_target_drift_fails_closed() -> None:
    report = build_phase11_current_controlled_artifact_gate_report(
        iptables_save_text=SNAP,
        phase_status_text=PHASE,
        expected_backend_target="172.18.0.9:60010",
    )
    assert report["final_decision"] == "BLOCKED_UNKNOWN_MPF_ARTIFACTS"
    assert any("dnat_target_mismatch" in item for item in report["unknown_mpf_artifacts"])


def test_composed_post_cleanup_report_keeps_operational_completion_closed(monkeypatch, tmp_path) -> None:
    from mpf.services import phase11_post_cleanup_restart_persistence_evidence_service as svc

    monkeypatch.setattr(svc.backend_service, "build_controlled_backend_target_report", lambda expected_version=__version__: {"status": "ok", "resolved_ipv4": "172.18.0.2", "target_port": 60010})
    monkeypatch.setattr(svc.persistence, "_read_command_stdout", lambda command: SNAP if command[0] == "iptables-save" else "")
    monkeypatch.setattr(svc.persistence, "run_phase11_controlled_artifact_persistence_plan", lambda *a, **k: {"final_decision": "CONTROLLED_ARTIFACT_PERSISTENCE_PLAN_READY", "blockers": [], "mutation_performed": False})
    monkeypatch.setattr(svc.diagnosis, "run_phase11_restart_autostart_persistence_diagnosis", lambda *a, **k: {"final_decision": "RESTART_AUTOSTART_PERSISTENCE_READY", "blockers": [], "mutation_performed": False})
    monkeypatch.setattr(svc.gap_inventory, "run_phase11_operational_completion_gap_inventory_report", lambda *a, **k: {"final_decision": "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED", "full_cli_production_operations": "missing_or_partial", "phase12_start_allowed": False})

    report = build_phase11_post_cleanup_restart_persistence_evidence_report(tmp_path, expected_version=__version__)
    assert report["blockers"] == []
    assert report["current_controlled_artifact_gate"]["unknown_mpf_artifacts"] == []
    assert report["restart_autostart_readiness_state"]["restart_autostart_proof"] == "missing_or_partial"
    assert report["phase11_operational_completion_accepted"] is False
    assert report["production_traffic"] == "controlled_cli_limited"
    assert report["customer_onboarding_allowed"] == "controlled_cli_limited"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"
    for key in ("mutation_performed", "db_mutation_performed", "firewall_apply_performed", "docker_restart_performed", "systemd_restart_performed"):
        assert report[key] is False


def test_cli_post_cleanup_evidence_command_json(monkeypatch, tmp_path) -> None:
    from mpf.services import phase11_post_cleanup_restart_persistence_evidence_service as svc

    monkeypatch.setattr(svc, "build_phase11_post_cleanup_restart_persistence_evidence_report", lambda *a, **k: {"component": "phase11_post_cleanup_restart_persistence_evidence", "repository_version": __version__, "mutation_performed": False, "phase11_operational_completion_accepted": False, "production_traffic": "controlled_cli_limited", "customer_onboarding_allowed": "controlled_cli_limited", "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no", "blockers": [], "final_decision": "POST_CLEANUP_RESTART_PERSISTENCE_EVIDENCE_READY", "next_required_step": "collect_real_restart_autostart_evidence_after_operator_restart_or_reboot"})
    result = CliRunner().invoke(app, ["production", "phase11-post-cleanup-restart-persistence-evidence", "--output", "json", "--config", str(tmp_path / "missing.yaml")])
    assert result.exit_code == 0
    assert "POST_CLEANUP_RESTART_PERSISTENCE_EVIDENCE_READY" in result.output


def test_post_cleanup_summary_uses_supplied_evidence_dir_for_ready_proof(monkeypatch, tmp_path) -> None:
    from mpf.services import phase11_post_cleanup_restart_persistence_evidence_service as svc

    monkeypatch.setattr(svc.backend_service, "build_controlled_backend_target_report", lambda expected_version=__version__: {"status": "ok", "resolved_ipv4": "172.18.0.2", "target_port": 60010})
    monkeypatch.setattr(svc.persistence, "_read_command_stdout", lambda command: SNAP if command[0] == "iptables-save" else "")
    monkeypatch.setattr(svc.persistence, "run_phase11_controlled_artifact_persistence_plan", lambda *a, **k: {"final_decision": "CONTROLLED_ARTIFACT_PERSISTENCE_PLAN_READY", "blockers": [], "mutation_performed": False})
    monkeypatch.setattr(svc.diagnosis, "run_phase11_restart_autostart_persistence_diagnosis", lambda *a, **k: {"final_decision": "RESTART_AUTOSTART_PERSISTENCE_READY", "blockers": [], "mutation_performed": False})
    monkeypatch.setattr(svc.proof, "build_phase11_restart_autostart_proof_report", lambda evidence_dir=None: {"restart_autostart_proof": "ready", "final_decision": "RESTART_AUTOSTART_PROOF_READY", "blockers": [], "mutation_performed": False})

    seen = {}
    def fake_gap(config_path, *, evidence_dir=None, packet_path_evidence_dir=None):
        seen["evidence_dir"] = evidence_dir
        return {"final_decision": "PHASE11_FULL_CLI_PRODUCTION_OPERATIONS_REQUIRED", "full_cli_production_operations": "missing_or_partial", "restart_autostart_proof": "ready", "phase12_start_allowed": False, "next_required_step": "implement_production_customer_lifecycle_execution"}
    monkeypatch.setattr(svc.gap_inventory, "run_phase11_operational_completion_gap_inventory_report", fake_gap)

    report = build_phase11_post_cleanup_restart_persistence_evidence_report(tmp_path, expected_version=__version__, evidence_dir=tmp_path)
    assert seen["evidence_dir"] == tmp_path
    assert report["restart_autostart_readiness_state"]["restart_autostart_proof"] == "ready"
    assert "restart_autostart_evidence_dir_missing" not in str(report)
    assert report["next_required_step"] == "implement_production_customer_lifecycle_execution"
    assert report["phase11_operational_completion_accepted"] is False
