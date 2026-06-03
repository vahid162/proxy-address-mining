from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from mpf.config import MPFConfig
from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.repositories.lane_repo import LaneRecord
from mpf.services import firewall_apply_rollback_operational_surface_service as surface_service

RUNNER = CliRunner()
CONFIG_PATH = Path("configs/mpf.example.yaml")

KNOWN_CONTROLLED_SNAPSHOT = """*filter
:INPUT ACCEPT [0:0]
:MPFC_20001 - [0:0]
:MPFC_20101 - [0:0]
-A MPFC_20001 -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_connlimit_reject" -j REJECT
-A MPFC_20001 -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_hashlimit_reject" -j REJECT
-A MPFC_20101 -p tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_connlimit_reject" -j REJECT
-A MPFC_20101 -p tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_hashlimit_reject" -j REJECT
COMMIT
*nat
:PREROUTING ACCEPT [0:0]
:MPF_NAT_PRE - [0:0]
-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010
-A MPF_NAT_PRE -p tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010
COMMIT
"""

CLEAN_SOURCE_BACKED_SNAPSHOT = """*filter
:INPUT ACCEPT [0:0]
COMMIT
"""

UNKNOWN_MPF_SNAPSHOT = """*filter
:INPUT ACCEPT [0:0]
:MPFO_BAD - [0:0]
COMMIT
"""


def cfg() -> MPFConfig:
    return MPFConfig.model_validate(
        {
            "server": {"name": "test"},
            "database": {"url": "postgresql://test/mpf"},
            "lanes": {"btc": {"enabled": True, "backend_port": 60010, "chain_prefix": "BTC"}},
        }
    )


def _mock_safe_reads(monkeypatch) -> list[str]:
    calls: list[str] = []

    def db_status(_config):
        calls.append("db_status")
        return SimpleNamespace(ok=True, message="OK", alembic_version="0002", public_table_count=20, lanes=1, customers=1, job_runs=1, firewall_applies=0, abuse_states=1)

    def lanes(_config):
        calls.append("lane_list")
        return SimpleNamespace(ok=True, message="OK", lanes=[LaneRecord("btc", True, 60010, "BTC", "stratum", "db")])

    def customers(_config, **kwargs):
        calls.append("active_customer_list")
        assert kwargs == {"status": "active", "include_deleted": False, "limit": 1000}
        return SimpleNamespace(ok=True, message="OK", customers=[CustomerRecord(1, "btc-1", "btc", "alice", 20001, "active", "immediate", None, None)])

    monkeypatch.setattr(surface_service.db_service, "status", db_status)
    monkeypatch.setattr(surface_service.lane_service, "list_lane_status", lanes)
    monkeypatch.setattr(surface_service.customer_read_service, "list_customer_status", customers)
    return calls


def test_firewall_apply_rollback_operational_surface_returns_ready_without_mutation(monkeypatch) -> None:
    calls = _mock_safe_reads(monkeypatch)
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(cfg(), snapshot_reader=lambda: KNOWN_CONTROLLED_SNAPSHOT)
    assert report["component"] == "controlled_firewall_apply_rollback_operational_surface"
    assert report["status"] == "READY"
    assert report["final_decision"] == "FIREWALL_APPLY_ROLLBACK_SURFACE_READY"
    assert report["firewall_apply_rollback_surface_ready"] is True
    assert report["firewall_apply_mode"] == "plan_only"
    assert report["runtime_activation_allowed"] is False
    assert report["lanes_visible_from_db"] == ["btc"]
    assert report["active_customers_visible_from_db"] == ["btc-1"]
    assert report["active_customer_count"] == 1
    assert report["controlled_artifact_gate_status"] == "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS"
    assert report["known_controlled_artifacts_present"] is True
    assert report["unknown_mpf_artifacts"] == []
    assert report["unknown_mpf_artifacts_count"] == 0
    assert report["forbidden_public_runtime_exposure"] is False
    assert calls == ["db_status", "lane_list", "active_customer_list"]
    assert all(item["status"] == "present" for item in report["controlled_apply_workflow_components_checked"])
    assert all(item["status"] == "present" for item in report["controlled_rollback_workflow_components_checked"])
    for key in (
        "restore_point_required",
        "firewall_snapshot_backup_required",
        "operator_lock_required",
        "verify_required",
        "rollback_artifact_required",
        "package_hash_validation_required",
        "operator_confirmation_required",
    ):
        assert report[key] is True
    for key in (
        "mutation_performed",
        "db_mutation_performed",
        "firewall_apply_performed",
        "firewall_rollback_performed",
        "iptables_restore_executed",
        "docker_action_performed",
        "systemd_action_performed",
        "conntrack_action_performed",
        "worker_enforcement_enabled",
        "ui_enabled",
        "telegram_enabled",
        "phase12_start_allowed",
        "direct_cli_firewall_mutation",
        "direct_db_writes_from_cli_handlers",
        "apply_execution_allowed_by_default",
        "rollback_execution_allowed_by_default",
    ):
        assert report[key] is False
    assert report["iptables_save_executed"] is True
    assert report["iptables_save_mode"] == "read_only"
    assert report["artifact_snapshot_source"] == "iptables-save stdout"
    assert report["artifact_snapshot_collected"] is True
    assert report["firewall_change"] == report["nat_change"] == report["runtime_change"] == "no"
    assert report["next_required_step"] == "implement_restart_autostart_proof"


def test_firewall_apply_rollback_surface_blocks_on_db_failure(monkeypatch) -> None:
    monkeypatch.setattr(surface_service.db_service, "status", lambda _config: SimpleNamespace(ok=False, message="down"))
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(cfg(), snapshot_reader=lambda: KNOWN_CONTROLLED_SNAPSHOT)
    assert report["status"] == "BLOCKED"
    assert report["blockers"] == ["database_read_failed"]
    assert report["mutation_performed"] is False
    assert report["firewall_apply_performed"] is False


def test_firewall_apply_rollback_surface_blocks_on_unsafe_config(monkeypatch) -> None:
    _mock_safe_reads(monkeypatch)
    config = cfg()
    config.firewall.apply_mode = "manual_apply"  # type: ignore[assignment]
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(config, snapshot_reader=lambda: KNOWN_CONTROLLED_SNAPSHOT)
    assert report["status"] == "BLOCKED"
    assert "firewall_apply_mode_not_plan_only" in report["blockers"]

    config = cfg()
    config.proxy.runtime_activation_allowed = True
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(config, snapshot_reader=lambda: KNOWN_CONTROLLED_SNAPSHOT)
    assert report["status"] == "BLOCKED"
    assert "proxy_runtime_activation_allowed_enabled" in report["blockers"]


def test_firewall_apply_rollback_surface_blocks_on_artifact_gate_risks(monkeypatch) -> None:
    _mock_safe_reads(monkeypatch)
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(
        cfg(),
        snapshot_reader=lambda: UNKNOWN_MPF_SNAPSHOT,
    )
    assert report["status"] == "BLOCKED"
    assert report["unknown_mpf_artifacts_count"] == 1
    assert "unknown_mpf_artifacts_detected" in report["blockers"]

    report = surface_service.build_firewall_apply_rollback_operational_surface_report(
        cfg(),
        snapshot_reader=lambda: KNOWN_CONTROLLED_SNAPSHOT,
        ip6tables_save_text=":MPF6_BAD - [0:0]",
    )
    assert report["status"] == "BLOCKED"
    assert report["forbidden_public_runtime_exposure"] is False
    assert report["unknown_mpf_artifacts_count"] == 1
    assert "unknown_mpf_artifacts_detected" in report["blockers"]


def test_firewall_apply_rollback_surface_blocks_for_forbidden_public_exposure(monkeypatch) -> None:
    _mock_safe_reads(monkeypatch)
    monkeypatch.setattr(
        surface_service.phase11_current_controlled_artifact_gate_service,
        "build_phase11_current_controlled_artifact_gate_report",
        lambda **_kwargs: {
            "final_decision": "BLOCKED_PUBLIC_EXPOSURE",
            "known_controlled_artifacts_present": True,
            "allowed_controlled_artifacts": ["chain:MPFC_20001"],
            "unknown_mpf_artifacts": [],
            "forbidden_public_runtime_exposure": True,
        },
    )
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(cfg(), snapshot_reader=lambda: KNOWN_CONTROLLED_SNAPSHOT)
    assert report["status"] == "BLOCKED"
    assert report["forbidden_public_runtime_exposure"] is True
    assert "forbidden_public_runtime_exposure_detected" in report["blockers"]


def test_empty_iptables_snapshot_blocks_and_cannot_false_green(monkeypatch) -> None:
    _mock_safe_reads(monkeypatch)
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(cfg(), snapshot_reader=lambda: "")
    assert report["status"] == "BLOCKED"
    assert report["controlled_artifact_gate_status"] == "BLOCKED"
    assert "artifact_snapshot_missing_or_empty" in report["blockers"]
    assert report["known_controlled_artifacts_present"] is False
    assert report["unknown_mpf_artifacts"] == []
    assert report["artifact_snapshot_collected"] is False
    assert report["firewall_apply_rollback_surface_ready"] is False


def test_pass_no_customer_artifacts_requires_source_backed_non_empty_snapshot(monkeypatch) -> None:
    _mock_safe_reads(monkeypatch)
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(cfg(), snapshot_reader=lambda: CLEAN_SOURCE_BACKED_SNAPSHOT)
    assert report["status"] == "READY"
    assert report["controlled_artifact_gate_status"] == "PASS_NO_CUSTOMER_ARTIFACTS"
    assert report["artifact_snapshot_collected"] is True
    assert report["artifact_snapshot_sha256"]
    assert report["iptables_save_executed"] is True
    assert report["unknown_mpf_artifacts"] == []


def test_default_subprocess_empty_snapshot_blocks(monkeypatch) -> None:
    _mock_safe_reads(monkeypatch)
    monkeypatch.setattr(surface_service.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""))
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(cfg())
    assert report["status"] == "BLOCKED"
    assert report["iptables_save_executed"] is True
    assert report["iptables_save_mode"] == "read_only"
    assert "artifact_snapshot_missing_or_empty" in report["blockers"]


def test_phase_status_path_is_repo_root_anchored(monkeypatch, tmp_path) -> None:
    _mock_safe_reads(monkeypatch)
    monkeypatch.chdir(tmp_path)
    report = surface_service.build_firewall_apply_rollback_operational_surface_report(cfg(), snapshot_reader=lambda: KNOWN_CONTROLLED_SNAPSHOT)
    assert report["status"] == "READY"
    assert report["controlled_artifact_gate_status"] == "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS"
    assert surface_service._PHASE_STATUS_PATH.is_absolute()
    assert surface_service._PHASE_STATUS_PATH.name == "PHASE_STATUS.md"


def test_firewall_apply_rollback_cli_is_thin_and_calls_service(monkeypatch) -> None:
    from mpf.interfaces import cli

    expected = {"component": "controlled_firewall_apply_rollback_operational_surface", "status": "READY", "mutation_performed": False}
    monkeypatch.setattr(cli, "_load", lambda _path: cfg())
    monkeypatch.setattr(cli.firewall_apply_rollback_operational_surface_service, "build_firewall_apply_rollback_operational_surface_report", lambda config: expected)
    result = RUNNER.invoke(app, ["production", "firewall-apply-rollback-operational-surface", "--config", str(CONFIG_PATH), "--output", "json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == expected
    source = inspect.getsource(cli.production_firewall_apply_rollback_operational_surface)
    assert "build_firewall_apply_rollback_operational_surface_report" in source
    for forbidden in ("query_database", "execute(", "iptables", "iptables-save", "iptables-restore", "conntrack", "docker", "systemctl", "subprocess"):
        assert forbidden not in source.lower()


def test_firewall_apply_rollback_cli_fails_closed_without_traceback_when_config_load_fails(monkeypatch) -> None:
    from mpf.interfaces import cli

    monkeypatch.setattr(cli, "_load", lambda _path: (_ for _ in ()).throw(FileNotFoundError("missing config")))
    result = RUNNER.invoke(app, ["production", "firewall-apply-rollback-operational-surface", "--output", "json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["status"] == "BLOCKED"
    assert report["blockers"] == ["configuration_load_failed"]
    assert report["mutation_performed"] is False
    assert report["db_mutation_performed"] is False
    assert report["firewall_apply_performed"] is False
    assert report["firewall_rollback_performed"] is False
    assert report["iptables_restore_executed"] is False
    assert "Traceback" not in result.output


def test_cli_handler_does_not_contain_direct_mutation_terms() -> None:
    from mpf.interfaces import cli

    source = inspect.getsource(cli.production_firewall_apply_rollback_operational_surface).lower()
    for forbidden in ("insert ", "update ", "delete ", "drop ", "commit", "iptables", "conntrack", "docker", "systemctl", "subprocess"):
        assert forbidden not in source
