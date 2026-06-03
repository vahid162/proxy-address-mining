from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_restart_autostart_proof_service import build_phase11_restart_autostart_proof_report

RUNNER = CliRunner()
VERSION = "0.1.245"


PHASE_STATUS = """current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
current_working_phase: Phase 11 operational completion — Full CLI Production Operations
production_traffic: controlled_cli_limited
customer_onboarding_allowed: controlled_cli_limited
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: no
"""


def _write_ready_evidence(path: Path) -> None:
    path.mkdir()
    (path / "repository_version.txt").write_text(f"{VERSION}\n", encoding="utf-8")
    (path / "phase_status.txt").write_text(PHASE_STATUS, encoding="utf-8")
    (path / "mpf_version.txt").write_text(f"{VERSION}\n", encoding="utf-8")
    (path / "db_ping.txt").write_text("OK\n", encoding="utf-8")
    (path / "db_status.txt").write_text(
        "database: OK\nalembic_version: abc\npublic_table_count: 10\nlanes: 1\ncustomers: 1\n",
        encoding="utf-8",
    )
    (path / "lanes.txt").write_text("btc\tenabled=True\tbackend_port=60010\tsource=db\n", encoding="utf-8")
    (path / "customers.txt").write_text("1\tlimited-btc-001\tbtc\tLimited BTC\tport=20001\tstatus=active\n", encoding="utf-8")
    (path / "docker_ps.txt").write_text("mpf-v2raya\tUp 2 minutes\nmpf-btc-forwarder\tUp 2 minutes\n", encoding="utf-8")
    (path / "container_listener_order.txt").write_text(
        "v2raya before btc; v2raya 127.0.0.1:2015; btc 127.0.0.1:60010\n",
        encoding="utf-8",
    )
    (path / "listeners.txt").write_text(
        "LISTEN 0 4096 127.0.0.1:2015 0.0.0.0:*\nLISTEN 0 4096 127.0.0.1:60010 0.0.0.0:*\n",
        encoding="utf-8",
    )
    (path / "phase11_firewall_artifacts.txt").write_text("known_controlled_phase11_artifacts: present\n", encoding="utf-8")
    (path / "unknown_mpf_firewall_artifacts.txt").write_text("", encoding="utf-8")
    (path / "mutation_flags.json").write_text(
        json.dumps(
            {
                "mutation_performed": False,
                "db_mutation_performed": False,
                "firewall_apply_performed": False,
                "conntrack_flush_performed": False,
                "docker_restart_performed": False,
                "systemd_restart_performed": False,
            }
        ),
        encoding="utf-8",
    )


def test_restart_autostart_proof_fails_closed_without_evidence() -> None:
    report = build_phase11_restart_autostart_proof_report()
    assert report["component"] == "phase11_restart_autostart_proof"
    assert report["repository_version"] == VERSION
    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"
    assert report["next_required_step"] == "run_restart_autostart_proof_on_farm5"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"
    assert report["production_traffic"] == "controlled_cli_limited"
    assert report["customer_onboarding_allowed"] == "controlled_cli_limited"
    assert report["blockers"]
    for key in (
        "mutation_performed",
        "db_mutation_performed",
        "firewall_apply_performed",
        "conntrack_flush_performed",
        "docker_restart_performed",
        "systemd_restart_performed",
    ):
        assert report[key] is False


def test_restart_autostart_proof_fails_closed_on_partial_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "repository_version.txt").write_text(f"{VERSION}\n", encoding="utf-8")

    report = build_phase11_restart_autostart_proof_report(evidence)

    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"
    assert any(str(blocker).startswith("missing_evidence:") for blocker in report["blockers"])


def test_restart_autostart_proof_ready_with_complete_source_backed_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    _write_ready_evidence(evidence)

    report = build_phase11_restart_autostart_proof_report(evidence)

    assert report["restart_autostart_proof"] == "ready"
    assert report["final_decision"] == "RESTART_AUTOSTART_PROOF_READY"
    assert report["next_required_step"] == "implement_production_customer_lifecycle_execution"
    assert report["blockers"] == []
    assert all(check["status"] == "passed" for check in report["checks"])


def test_restart_autostart_proof_blocks_public_backend_listener(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    _write_ready_evidence(evidence)
    (evidence / "listeners.txt").write_text("LISTEN 0 4096 0.0.0.0:60010 0.0.0.0:*\n", encoding="utf-8")

    report = build_phase11_restart_autostart_proof_report(evidence)

    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"
    assert any("btc_backend_local_only" in str(blocker) for blocker in report["blockers"])


def test_restart_autostart_proof_cli_json_fails_closed_without_evidence() -> None:
    result = RUNNER.invoke(app, ["production", "restart-autostart-proof", "--output", "json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["repository_version"] == VERSION
    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"
    assert report["mutation_performed"] is False


def test_restart_autostart_helper_script_is_read_only() -> None:
    text = Path("scripts/phase11_collect_restart_autostart_proof.sh").read_text(encoding="utf-8")
    forbidden = (
        "iptables-restore",
        "conntrack -F",
        "docker restart",
        "systemctl restart",
        "systemctl start",
        "sudo reboot",
        "shutdown -r",
    )
    for item in forbidden:
        assert item not in text
    assert "iptables-save" in text
    assert "mpf production restart-autostart-proof" in text
