from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from mpf.adapters.docker_compose import DockerContainerSummary
from mpf.adapters.socket_inspector import ListeningSocket
from mpf.services.phase11_restart_autostart_persistence_diagnosis_service import (
    build_phase11_restart_autostart_persistence_diagnosis_report,
)
from mpf.services.phase11_restart_autostart_persistence_fix_service import (
    build_phase11_restart_autostart_persistence_fix_package,
    build_phase11_restart_autostart_persistence_fix_package_from_plan,
    build_phase11_restart_autostart_persistence_fix_plan_report,
    validate_compose_scope,
)
from mpf.services.phase11_controlled_artifact_persistence_plan_service import (
    build_phase11_controlled_artifact_persistence_plan_report,
)
from mpf.interfaces.cli import app
from mpf.services.phase11_restart_autostart_proof_service import build_phase11_restart_autostart_proof_report

RUNNER = CliRunner()
VERSION = "0.1.286"


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
    assert report["next_required_step"] == "fix_restart_autostart_persistence_gap"
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


def test_restart_autostart_proof_blocks_non_empty_unknown_firewall_artifacts(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    _write_ready_evidence(evidence)
    (evidence / "unknown_mpf_firewall_artifacts.txt").write_text("unknown_chain:MPFC_BAD\n", encoding="utf-8")

    report = build_phase11_restart_autostart_proof_report(evidence)

    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"
    assert any("unknown_mpf_firewall_artifacts_empty" in str(blocker) for blocker in report["blockers"])


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


def test_restart_autostart_helper_uses_current_controlled_artifact_gate() -> None:
    text = Path("scripts/phase11_collect_restart_autostart_proof.sh").read_text(encoding="utf-8")

    assert "mpf production current-controlled-artifact-gate" in text
    assert '--iptables-save-file "${OUT_DIR}/iptables_save.txt"' in text
    assert '--ip6tables-save-file "${OUT_DIR}/ip6tables_save.txt"' in text
    assert "current_controlled_artifact_gate.json" in text


def test_restart_autostart_helper_does_not_fake_empty_unknown_artifacts() -> None:
    text = Path("scripts/phase11_collect_restart_autostart_proof.sh").read_text(encoding="utf-8")

    assert ': >"${OUT_DIR}/unknown_mpf_firewall_artifacts.txt"' not in text
    assert 'unknown = report.get("unknown_mpf_artifacts")' in text
    assert "unknown_mpf_firewall_artifacts: []" in text
    assert "artifact_gate_parse_failed" in text


def test_restart_autostart_helper_uses_ip6tables_save_for_ipv6_snapshot() -> None:
    text = Path("scripts/phase11_collect_restart_autostart_proof.sh").read_text(encoding="utf-8")

    assert "run_capture ip6tables_save.txt ip6tables-save" in text
    assert "run_capture ip6tables_save.txt iptables-save" not in text


def _healthy_runtime_containers(*, include_bridge: bool = True) -> list[DockerContainerSummary]:
    containers = [
        DockerContainerSummary("mpf-v2raya", "v2raya", "Up 5 minutes (healthy)", "127.0.0.1:2015->2017/tcp"),
        DockerContainerSummary("mpf-forwarder-btc", "gost", "Up 5 minutes (healthy)", "127.0.0.1:60010->60010/tcp"),
    ]
    if include_bridge:
        containers.append(DockerContainerSummary("mpf-v2raya-socks-bridge", "gost", "Up 5 minutes (healthy)", ""))
    return containers


def _local_only_runtime_sockets() -> list[ListeningSocket]:
    return [
        ListeningSocket("127.0.0.1", 2015, "v2raya"),
        ListeningSocket("127.0.0.1", 60010, "gost"),
    ]


def _artifact_gate(*, known_present: bool = True, unknown: list[str] | None = None) -> dict[str, object]:
    return {
        "final_decision": "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS" if known_present else "PASS_NO_CUSTOMER_ARTIFACTS",
        "known_controlled_artifacts_present": known_present,
        "allowed_controlled_artifacts": ["chain:MPFC_20101"] if known_present else [],
        "unknown_mpf_artifacts": unknown or [],
        "blockers": [],
        "warnings": [],
    }


def test_restart_autostart_persistence_diagnosis_blocks_missing_socks_bridge() -> None:
    report = build_phase11_restart_autostart_persistence_diagnosis_report(
        actual_containers=_healthy_runtime_containers(include_bridge=False),
        listening_sockets=_local_only_runtime_sockets(),
        artifact_gate_report=_artifact_gate(),
    )

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_GAP"
    assert "mpf-v2raya-socks-bridge" in report["missing_containers"]
    assert "missing_container:mpf-v2raya-socks-bridge" in report["blockers"]
    assert report["next_required_step"] == "fix_restart_autostart_persistence_gap"


def test_restart_autostart_persistence_diagnosis_blocks_absent_known_artifacts() -> None:
    report = build_phase11_restart_autostart_persistence_diagnosis_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        artifact_gate_report=_artifact_gate(known_present=False),
    )

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_GAP"
    assert report["known_controlled_phase11_artifacts_present"] is False
    assert report["post_reboot_firewall_customer_artifacts_missing"] is True
    assert "post_reboot_known_controlled_phase11_artifacts_absent" in report["blockers"]


def test_restart_autostart_persistence_diagnosis_passes_only_when_runtime_and_artifacts_ready() -> None:
    report = build_phase11_restart_autostart_persistence_diagnosis_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        artifact_gate_report=_artifact_gate(),
    )

    assert report["final_decision"] == "RESTART_AUTOSTART_PERSISTENCE_READY"
    assert report["missing_containers"] == []
    assert report["known_controlled_phase11_artifacts_present"] is True
    assert report["unknown_mpf_artifacts_empty"] is True
    assert report["post_reboot_firewall_customer_artifacts_missing"] is False
    assert report["blockers"] == []


def test_restart_autostart_persistence_helper_script_is_read_only() -> None:
    text = Path("scripts/phase11_diagnose_restart_autostart_persistence.sh").read_text(encoding="utf-8")
    forbidden = (
        "run_capture_cmd reboot",
        "run_capture_cmd shutdown -r",
        "run_capture_cmd docker restart",
        "run_capture_cmd docker compose up",
        "run_capture_cmd docker compose down",
        "run_capture_cmd docker compose restart",
        "run_capture_cmd systemctl start",
        "run_capture_cmd systemctl restart",
        "run_capture_cmd systemctl enable",
        "run_capture_cmd iptables-restore",
        "run_capture_cmd mpf firewall apply",
        "run_capture_cmd conntrack flush",
        "run_capture_cmd conntrack -F",
        "run_capture_cmd psql -c",
        "run_capture_cmd mpf db migrate",
    )
    for item in forbidden:
        assert item not in text
    for allowed in (
        "mpf phase-status",
        "mpf proxy status",
        "mpf proxy doctor",
        "docker ps -a",
        "docker compose -p",
        "ss -ltnp",
        "iptables-save",
        "ip6tables-save",
        "mpf production current-controlled-artifact-gate",
        "mpf production restart-autostart-proof",
        "mpf production restart-autostart-persistence-diagnosis",
    ):
        assert allowed in text


def test_restart_autostart_persistence_diagnosis_cli_json_fails_closed() -> None:
    result = RUNNER.invoke(app, ["production", "restart-autostart-persistence-diagnosis", "--output", "json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["repository_version"] == VERSION
    assert report["final_decision"] in {
        "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_GAP",
        "RESTART_AUTOSTART_PERSISTENCE_READY",
    }
    assert report["mutation_performed"] is False



def test_restart_autostart_persistence_fix_plan_allows_missing_socks_bridge_as_repair_reason() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(include_bridge=False),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report={"final_decision": "BLOCKED", "blockers": [], "unknown_mpf_artifacts": []},
    )

    assert report["final_decision"] == "RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN_READY"
    assert "missing_container:mpf-v2raya-socks-bridge" in report["repair_reasons"]
    assert report["safety_blockers"] == []
    assert report["docker_restart_performed"] is False


def test_restart_autostart_persistence_fix_plan_allows_unhealthy_socks_bridge_as_repair_reason() -> None:
    containers = _healthy_runtime_containers()
    containers = [
        DockerContainerSummary(item.name, item.image, "Exited (1) 2 minutes ago", item.ports)
        if item.name == "mpf-v2raya-socks-bridge"
        else item
        for item in containers
    ]
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=containers,
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report={"final_decision": "BLOCKED", "blockers": [], "unknown_mpf_artifacts": []},
    )

    assert report["final_decision"] == "RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN_READY"
    assert "unhealthy_container:mpf-v2raya-socks-bridge" in report["repair_reasons"]
    assert report["safety_blockers"] == []
    assert report["likely_socks_bridge_failure_reason"] == "socks_bridge_container_exited_after_reboot"


def test_restart_autostart_persistence_fix_plan_ready_for_fix_plan_only_when_runtime_local() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report={"final_decision": "RESTART_AUTOSTART_PERSISTENCE_READY", "blockers": [], "unknown_mpf_artifacts": []},
    )

    assert report["final_decision"] == "NO_RUNTIME_REPAIR_REQUIRED"
    assert report["runtime_repair_required"] is False
    assert report["runtime_repair_reasons"] == []
    assert report["next_required_step"] == "collect_restart_autostart_proof_after_persistence_fix"
    assert report["mutation_performed"] is False



def test_restart_autostart_persistence_fix_plan_blocks_unknown_artifacts_as_safety_blocker() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report={"final_decision": "BLOCKED", "blockers": [], "unknown_mpf_artifacts": ["unknown_chain:MPFX"]},
    )

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN"
    assert "unknown_mpf_artifacts_detected" in report["safety_blockers"]



def test_restart_autostart_persistence_fix_plan_blocks_nested_unknown_artifacts_summary() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report={
            "final_decision": "BLOCKED",
            "blockers": [],
            "current_controlled_artifact_gate_summary": {"unknown_mpf_artifacts": ["unknown_chain:MPFX"]},
            "unknown_mpf_artifacts_empty": True,
        },
    )

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN"
    assert "unknown_mpf_artifacts_detected" in report["safety_blockers"]


def test_restart_autostart_persistence_fix_plan_blocks_unknown_artifacts_empty_false() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report={
            "final_decision": "BLOCKED",
            "blockers": [],
            "current_controlled_artifact_gate_summary": {"unknown_mpf_artifacts": []},
            "unknown_mpf_artifacts_empty": False,
        },
    )

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN"
    assert "unknown_mpf_artifacts_detected" in report["safety_blockers"]


def test_restart_autostart_persistence_fix_plan_blocks_unknown_artifacts_blocker() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report={
            "final_decision": "BLOCKED",
            "blockers": ["unknown_mpf_artifacts_present"],
            "current_controlled_artifact_gate_summary": {"unknown_mpf_artifacts": []},
            "unknown_mpf_artifacts_empty": True,
        },
    )

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN"
    assert "unknown_mpf_artifacts_detected" in report["safety_blockers"]


def test_restart_autostart_persistence_fix_plan_blocks_direct_artifact_gate_unknown_artifacts() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        artifact_gate_report=_artifact_gate(known_present=True, unknown=["unknown_chain:MPFX"]),
    )

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PLAN"
    assert "unknown_mpf_artifacts_detected" in report["safety_blockers"]


def test_restart_autostart_fix_package_blocks_nested_unknown_artifacts() -> None:
    report = build_phase11_restart_autostart_persistence_fix_package(
        diagnosis_report={
            "final_decision": "BLOCKED",
            "blockers": [],
            "current_controlled_artifact_gate_summary": {"unknown_mpf_artifacts": ["unknown_chain:MPFX"]},
            "unknown_mpf_artifacts_empty": True,
        },
    )

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE"
    assert "unknown_mpf_artifacts_detected" in report["safety_blockers"]


def test_compose_runtime_contract_keeps_expected_containers_and_local_only_ports() -> None:
    text = Path("compose/mpf-proxy.compose.yaml").read_text(encoding="utf-8")
    for name in ("mpf-v2raya", "mpf-v2raya-socks-bridge", "mpf-forwarder-btc"):
        assert f"container_name: {name}" in text
    assert 'network_mode: "service:mpf-v2raya"' in text
    assert "22070:22070" not in text
    assert '"127.0.0.1:2015:2017"' in text
    assert '"127.0.0.1:60010:60010"' in text
    assert "mpf-v2raya-socks-bridge:" in text
    assert "condition: service_healthy" in text


def test_restart_autostart_fix_helper_is_plan_default_and_guarded() -> None:
    text = Path("scripts/phase11_run_restart_autostart_persistence_fix_package.sh").read_text(encoding="utf-8")
    assert 'MODE="--plan"' in text
    assert '--execute requires --yes' in text
    assert "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never" in text
    for item in (
        "reboot",
        "shutdown",
        "systemctl enable",
        "systemctl start",
        "systemctl restart",
        "iptables-restore",
        "conntrack -F",
        "mpf customer add",
        "mpf customer edit",
        "mpf customer delete",
        "mpf customer renew",
        "unrestricted firewall apply",
    ):
        assert item not in text


def test_controlled_artifact_persistence_plan_blocks_absent_artifacts_when_no_official_reapply_plan() -> None:
    report = build_phase11_controlled_artifact_persistence_plan_report(
        current_controlled_artifact_gate_result=_artifact_gate(known_present=False),
        listening_sockets=_local_only_runtime_sockets(),
        customer_records=[],
        phase_status_text=PHASE_STATUS,
        candidate_reapply_restore_path_reuse={
            "candidate_reapply_services_declared": False,
            "raw_iptables_reapply_implemented_here": False,
            "safe_reuse_identified_for_execution_in_this_pr": False,
            "execution_package_available": False,
            "execution_decision": "CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_NOT_AVAILABLE",
        },
    )

    assert report["final_decision"] == "BLOCKED_CONTROLLED_ARTIFACT_PERSISTENCE_PLAN"
    assert "candidate_reapply_or_restore_services_not_identified" in report["blockers"]


def test_controlled_artifact_persistence_plan_blocks_unknown_public_and_missing_customers() -> None:
    base_gate = _artifact_gate(known_present=False)
    missing = build_phase11_controlled_artifact_persistence_plan_report(
        current_controlled_artifact_gate_result=base_gate,
        listening_sockets=_local_only_runtime_sockets(),
        customer_records=[],
        phase_status_text=PHASE_STATUS,
    )
    assert missing["final_decision"] == "BLOCKED_CONTROLLED_ARTIFACT_PERSISTENCE_PLAN"
    assert any(str(item).startswith("required_controlled_customer_missing_or_mismatched") for item in missing["blockers"])

    unknown = build_phase11_controlled_artifact_persistence_plan_report(
        current_controlled_artifact_gate_result=_artifact_gate(known_present=True, unknown=["unknown_chain:MPFX"]),
        listening_sockets=_local_only_runtime_sockets(),
        customer_records=[],
        phase_status_text=PHASE_STATUS,
    )
    assert "unknown_mpf_artifacts_detected" in unknown["blockers"]

    public = build_phase11_controlled_artifact_persistence_plan_report(
        current_controlled_artifact_gate_result=base_gate,
        listening_sockets=[ListeningSocket("0.0.0.0", 60010, "gost")],
        customer_records=[],
        phase_status_text=PHASE_STATUS,
    )
    assert "backend_public_exposure_detected" in public["blockers"]


def test_controlled_artifact_persistence_plan_ready_only_for_classified_local_records() -> None:
    class Record:
        def __init__(self, customer_key: str, lane: str, port: int, status: str = "active") -> None:
            self.customer_key = customer_key
            self.lane = lane
            self.port = port
            self.status = status

    report = build_phase11_controlled_artifact_persistence_plan_report(
        current_controlled_artifact_gate_result=_artifact_gate(known_present=False),
        listening_sockets=_local_only_runtime_sockets(),
        customer_records=[Record("canary-btc-001", "btc", 20001), Record("limited-btc-001", "btc", 20101)],
        phase_status_text=PHASE_STATUS,
    )

    assert report["final_decision"] == "CONTROLLED_ARTIFACT_PERSISTENCE_PLAN_READY"
    assert report["known_controlled_artifacts_present"] is False
    assert report["controlled_artifacts_absent_after_reboot"] is True
    assert report["next_required_step"] == "prepare_live_ready_controlled_artifact_reapply_package"
    assert report["safe_reuse_identified_for_execution_in_this_pr"] is False
    assert report["execution_package_available"] is False
    assert report["artifact_reapply_execution_decision"] == "CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_BLOCKED_UNTIL_REAL_ADAPTERS_AND_FARM5_READY_PACKAGE"


def test_new_phase11_fix_plan_cli_surfaces_json() -> None:
    for args in (
        ["production", "restart-autostart-persistence-fix-plan", "--output", "json"],
        ["production", "restart-autostart-persistence-fix-package", "--output", "json"],
        ["production", "controlled-artifact-persistence-plan", "--output", "json"],
    ):
        result = RUNNER.invoke(app, args)
        assert result.exit_code == 0, result.output
        report = json.loads(result.output)
        assert report["repository_version"] == VERSION
        assert report.get("mutation_performed") is False or report.get("mutation_declaration", {}).get("normal_service_code_performs_mutation") is False



def test_restart_autostart_fix_package_blocks_when_safety_blockers_present() -> None:
    from mpf.services.phase11_restart_autostart_persistence_fix_service import (
        build_phase11_restart_autostart_persistence_fix_package,
    )

    report = build_phase11_restart_autostart_persistence_fix_package(expected_version="0.1.246")

    assert report["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE"
    assert "wrong_expected_version" in report["safety_blockers"]


def _write_fake_phase11_fix_mpf(path: Path, *, plan_safety_blockers: list[str], repair_reasons: list[str], package_safety_blockers: list[str] | None = None) -> None:
    package = {
        "final_decision": "RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE_READY",
        "repository_version": VERSION,
        "expected_version": VERSION,
        "safety_blockers": package_safety_blockers or [],
        "repair_reasons": repair_reasons,
        "runtime_repair_required": bool(repair_reasons),
        "runtime_repair_reasons": repair_reasons,
        "runtime_reconciliation_execution_allowed": bool(repair_reasons) and not (package_safety_blockers or []),
        "observations_supplied": True,
        "source_plan_safety_blockers": plan_safety_blockers,
        "backend_public_exposure_detected": False,
        "phase_gate_summary": {
            "phase12_start_allowed": False,
            "worker_enforcement_allowed": "no",
            "ui_allowed": "no",
            "telegram_allowed": "no",
        },
        "exact_allowed_operation_set": ["controlled_docker_compose_runtime_reconciliation_up_no_build_pull_never"],
        "exact_docker_compose_command_plan": {
            "project_name": "mpf-proxy",
            "compose_file": "compose/mpf-proxy.compose.yaml",
            "profile": "phase4-runtime",
            "execute_command": "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never",
        },
        "required_execute_command": "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never",
    }
    plan = {
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "safety_blockers": plan_safety_blockers,
        "repair_reasons": repair_reasons,
        "runtime_repair_required": bool(repair_reasons),
        "runtime_repair_reasons": repair_reasons,
        "runtime_reconciliation_execution_allowed": bool(repair_reasons) and not plan_safety_blockers,
        "observations_supplied": True,
        "backend_public_exposure_detected": False,
        "local_only_listener_state": {
            "checks": {
                "v2raya_ui": {"public_bind_detected": False},
                "btc_backend": {"public_bind_detected": False},
            }
        },
    }
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        f"PACKAGE = {json.dumps(package)!r}\n"
        f"PLAN = {json.dumps(plan)!r}\n"
        "args = sys.argv[1:]\n"
        "if args[:1] == ['phase-status']:\n"
        "    print('current_working_phase: Phase 11 operational completion — Full CLI Production Operations')\n"
        "    print('phase12_start_allowed: no')\n"
        "    print('worker_enforcement_allowed: no')\n"
        "    print('ui_allowed: no')\n"
        "    print('telegram_allowed: no')\n"
        "elif args[:2] == ['production', 'restart-autostart-persistence-fix-package']:\n"
        "    print(PACKAGE)\n"
        "elif args[:2] == ['production', 'restart-autostart-persistence-fix-plan']:\n"
        "    print(PLAN)\n"
        "else:\n"
        "    print(json.dumps({'ok': True, 'mutation_performed': False}))\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_fake_docker(path: Path, log_path: Path) -> None:
    path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"printf '%s\\n' \"$*\" >> {log_path}\n"
        "printf 'fake docker %s\\n' \"$*\"\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_restart_autostart_fix_helper_refuses_execute_when_safety_blockers_present(tmp_path: Path) -> None:
    fake_mpf = tmp_path / "mpf"
    fake_docker = tmp_path / "docker"
    docker_log = tmp_path / "docker.log"
    _write_fake_phase11_fix_mpf(
        fake_mpf,
        plan_safety_blockers=["phase_gate_mismatch"],
        repair_reasons=["unhealthy_container:mpf-v2raya-socks-bridge"],
    )
    _write_fake_docker(fake_docker, docker_log)

    result = subprocess.run(
        ["scripts/phase11_run_restart_autostart_persistence_fix_package.sh", "--execute", "--yes", "--out-dir", str(tmp_path / "out")],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "MPF_BIN": str(fake_mpf), "PATH": f"{tmp_path}:{os.environ['PATH']}"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "plan safety_blockers must be empty before execute" in result.stderr
    assert not docker_log.exists()


def test_restart_autostart_fix_helper_allows_execute_for_repair_reasons_without_safety_blockers(tmp_path: Path) -> None:
    fake_mpf = tmp_path / "mpf"
    fake_docker = tmp_path / "docker"
    docker_log = tmp_path / "docker.log"
    _write_fake_phase11_fix_mpf(
        fake_mpf,
        plan_safety_blockers=[],
        repair_reasons=["unhealthy_container:mpf-v2raya-socks-bridge"],
    )
    _write_fake_docker(fake_docker, docker_log)

    result = subprocess.run(
        ["scripts/phase11_run_restart_autostart_persistence_fix_package.sh", "--execute", "--yes", "--out-dir", str(tmp_path / "out")],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "MPF_BIN": str(fake_mpf), "PATH": f"{tmp_path}:{os.environ['PATH']}"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    docker_calls = docker_log.read_text(encoding="utf-8")
    assert "compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never" in docker_calls


def test_restart_autostart_fix_helper_refuses_execute_when_unknown_safety_blocker_present(tmp_path: Path) -> None:
    fake_mpf = tmp_path / "mpf"
    fake_docker = tmp_path / "docker"
    docker_log = tmp_path / "docker.log"
    _write_fake_phase11_fix_mpf(
        fake_mpf,
        plan_safety_blockers=["unknown_mpf_artifacts_detected"],
        package_safety_blockers=["unknown_mpf_artifacts_detected"],
        repair_reasons=["unhealthy_container:mpf-v2raya-socks-bridge"],
    )
    _write_fake_docker(fake_docker, docker_log)

    result = subprocess.run(
        ["scripts/phase11_run_restart_autostart_persistence_fix_package.sh", "--execute", "--yes", "--out-dir", str(tmp_path / "out")],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "MPF_BIN": str(fake_mpf), "PATH": f"{tmp_path}:{os.environ['PATH']}"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "package safety_blockers must be empty before execute" in result.stderr
    assert not docker_log.exists()


def _farm5_absent_artifact_diagnosis() -> dict[str, object]:
    return {
        "final_decision": "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_GAP",
        "blockers": ["post_reboot_known_controlled_phase11_artifacts_absent"],
        "unknown_mpf_artifacts": [],
        "unknown_mpf_artifacts_empty": True,
        "known_controlled_phase11_artifacts_present": False,
        "backend_public_exposure_detected": False,
        "current_controlled_artifact_gate_summary": {
            "known_controlled_artifacts_present": False,
            "unknown_mpf_artifacts": [],
        },
    }


def test_compose_scope_accepts_canonical_absolute_relative_dot_and_symlink(tmp_path: Path) -> None:
    canonical = Path("compose/mpf-proxy.compose.yaml").resolve()
    for candidate in (canonical, Path("compose/mpf-proxy.compose.yaml"), Path("./compose/mpf-proxy.compose.yaml")):
        result = validate_compose_scope(candidate)
        assert result["valid"] is True
        assert result["same_file"] is True
        assert result["blocker"] is None

    link = tmp_path / "official-compose-link.yaml"
    link.symlink_to(canonical)
    result = validate_compose_scope(link)
    assert result["valid"] is True
    assert result["configured_resolved_path"] == result["canonical_resolved_path"]


def test_compose_scope_rejects_unrelated_same_basename_and_suffix(tmp_path: Path) -> None:
    other_dir = tmp_path / "other" / "compose"
    other_dir.mkdir(parents=True)
    other = other_dir / "mpf-proxy.compose.yaml"
    other.write_text(Path("compose/mpf-proxy.compose.yaml").read_text(encoding="utf-8"), encoding="utf-8")

    result = validate_compose_scope(other)
    assert result["valid"] is False
    assert result["blocker"] == "compose_scope_mismatch"

    suffix_dir = tmp_path / "prefix" / "compose"
    suffix_dir.mkdir(parents=True)
    suffix = suffix_dir / "mpf-proxy.compose.yaml"
    suffix.write_text("services: {}\n", encoding="utf-8")
    result = validate_compose_scope(suffix)
    assert result["valid"] is False
    assert result["blocker"] == "compose_scope_mismatch"


def test_farm5_healthy_runtime_absent_artifact_plan_has_no_runtime_repair() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report=_farm5_absent_artifact_diagnosis(),
        artifact_gate_report=_artifact_gate(known_present=False),
        compose_file=Path("compose/mpf-proxy.compose.yaml").resolve(),
    )

    assert report["safety_blockers"] == []
    assert report["runtime_repair_required"] is False
    assert report["runtime_repair_reasons"] == []
    assert report["missing_containers"] == []
    assert report["local_only_listener_state"]["blockers"] == []
    assert report["final_decision"] == "NO_RUNTIME_REPAIR_REQUIRED"
    assert report["controlled_artifact_reapply_required"] is True
    assert report["controlled_artifact_reapply_execution_available"] is False
    assert report["next_required_step"] == "prepare_live_ready_controlled_artifact_reapply_package"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"


def test_farm5_healthy_runtime_package_uses_source_plan_and_disables_execute() -> None:
    plan = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report=_farm5_absent_artifact_diagnosis(),
        artifact_gate_report=_artifact_gate(known_present=False),
        compose_file=Path("compose/mpf-proxy.compose.yaml").resolve(),
    )
    package = build_phase11_restart_autostart_persistence_fix_package_from_plan(plan)

    assert package["source_plan_final_decision"] == plan["final_decision"]
    assert package["source_plan_runtime_repair_required"] is False
    assert package["source_plan_runtime_repair_reasons"] == []
    assert package["final_decision"] == "NO_RUNTIME_REPAIR_REQUIRED"
    assert package["runtime_reconciliation_execution_allowed"] is False
    assert package["required_execute_command"] is None


def test_missing_runtime_observations_fail_closed_without_fabricated_ready() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        diagnosis_report={"final_decision": "BLOCKED", "blockers": [], "unknown_mpf_artifacts": []},
    )
    package = build_phase11_restart_autostart_persistence_fix_package_from_plan(report)

    assert "runtime_observations_not_supplied" in report["safety_blockers"]
    assert report["missing_containers"] == []
    assert report["runtime_repair_reasons"] == []
    assert package["final_decision"] == "BLOCKED_RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE"
    assert package["required_execute_command"] is None


def test_unhealthy_socks_bridge_still_produces_controlled_runtime_repair_package() -> None:
    containers = [
        DockerContainerSummary(item.name, item.image, "Exited (1) 2 minutes ago", item.ports)
        if item.name == "mpf-v2raya-socks-bridge"
        else item
        for item in _healthy_runtime_containers()
    ]
    plan = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=containers,
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report={"final_decision": "BLOCKED", "blockers": [], "unknown_mpf_artifacts": [], "unknown_mpf_artifacts_empty": True},
        compose_file=Path("compose/mpf-proxy.compose.yaml"),
    )
    package = build_phase11_restart_autostart_persistence_fix_package_from_plan(plan)

    assert plan["runtime_repair_required"] is True
    assert "unhealthy_container:mpf-v2raya-socks-bridge" in plan["runtime_repair_reasons"]
    assert package["final_decision"] == "RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE_READY"
    assert package["required_execute_command"] is not None


def test_public_exposure_remains_safety_blocker() -> None:
    report = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=[ListeningSocket("0.0.0.0", 60010, "gost"), ListeningSocket("127.0.0.1", 2015, "v2raya")],
        diagnosis_report={"final_decision": "BLOCKED", "blockers": [], "unknown_mpf_artifacts": [], "backend_public_exposure_detected": True},
    )
    assert "backend_public_exposure_detected" in report["safety_blockers"]
    assert "non_local_listener:btc_backend:60010" in report["safety_blockers"]


def test_helper_refuses_execute_when_no_runtime_repair_required(tmp_path: Path) -> None:
    fake_mpf = tmp_path / "mpf"
    fake_docker = tmp_path / "docker"
    docker_log = tmp_path / "docker.log"
    _write_fake_phase11_fix_mpf(fake_mpf, plan_safety_blockers=[], repair_reasons=[])
    text = fake_mpf.read_text(encoding="utf-8")
    text = text.replace('"final_decision": "RESTART_AUTOSTART_PERSISTENCE_FIX_PACKAGE_READY"', '"final_decision": "NO_RUNTIME_REPAIR_REQUIRED"')
    text = text.replace('"required_execute_command": "docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d --no-build --pull never"', '"required_execute_command": null')
    fake_mpf.write_text(text, encoding="utf-8")
    fake_mpf.chmod(0o755)
    _write_fake_docker(fake_docker, docker_log)

    result = subprocess.run(
        ["scripts/phase11_run_restart_autostart_persistence_fix_package.sh", "--execute", "--yes", "--out-dir", str(tmp_path / "out")],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "MPF_BIN": str(fake_mpf), "PATH": f"{tmp_path}:{os.environ['PATH']}"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "no Docker runtime repair is required; controlled execution refused" in result.stderr
    assert not docker_log.exists()


def test_gap_inventory_chooses_controlled_artifact_reapply_for_farm5_fixture() -> None:
    from mpf.services.phase11_operational_completion_gap_inventory_service import build_phase11_operational_completion_gap_inventory_report

    plan = build_phase11_restart_autostart_persistence_fix_plan_report(
        actual_containers=_healthy_runtime_containers(),
        listening_sockets=_local_only_runtime_sockets(),
        diagnosis_report=_farm5_absent_artifact_diagnosis(),
        artifact_gate_report=_artifact_gate(known_present=False),
        compose_file=Path("compose/mpf-proxy.compose.yaml"),
    )
    report = build_phase11_operational_completion_gap_inventory_report(persistence_plan_report=plan)

    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["next_required_step"] == "controlled_artifact_reapply_readiness_snapshot_required"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"


def _write_ready_restart_evidence(root: Path) -> None:
    import json
    from mpf import __version__
    (root / "repository_version.txt").write_text(__version__, encoding="utf-8")
    (root / "mpf_version.txt").write_text(__version__, encoding="utf-8")
    phase = """current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
current_working_phase: Phase 11 operational completion — Full CLI Production Operations
phase12_start_allowed: no
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
production_traffic: controlled_cli_limited
customer_onboarding_allowed: controlled_cli_limited
"""
    (root / "phase_status.txt").write_text(phase, encoding="utf-8")
    (root / "db_ping.txt").write_text("OK\n", encoding="utf-8")
    (root / "db_status.txt").write_text("database: OK\nalembic_version: head\nlanes: 1\ncustomers: 2\n", encoding="utf-8")
    (root / "lanes.txt").write_text("btc enabled\n", encoding="utf-8")
    (root / "customers.txt").write_text("canary-btc-001\nlimited-btc-001\n", encoding="utf-8")
    (root / "docker_ps.txt").write_text("mpf-v2raya Up\nmpf-btc-forwarder Up\n", encoding="utf-8")
    listeners = "LISTEN 0 4096 127.0.0.1:2015\nLISTEN 0 4096 127.0.0.1:60010\n"
    (root / "listeners.txt").write_text(listeners, encoding="utf-8")
    (root / "container_listener_order.txt").write_text("v2raya btc 127.0.0.1:2015 127.0.0.1:60010\n", encoding="utf-8")
    (root / "phase11_firewall_artifacts.txt").write_text("known_controlled_phase11_artifacts: present\n", encoding="utf-8")
    (root / "unknown_mpf_firewall_artifacts.txt").write_text("unknown_mpf_firewall_artifacts: []\n", encoding="utf-8")
    (root / "mutation_flags.json").write_text(json.dumps({"mutation_performed": False, "db_mutation_performed": False, "firewall_apply_performed": False, "conntrack_flush_performed": False, "docker_restart_performed": False, "systemd_restart_performed": False}), encoding="utf-8")
    for name in ("controlled-backend-target.json", "current-controlled-artifact-gate.json", "proof-report.json", "proof_report.json"):
        (root / name).write_text(json.dumps({"component": name, "status": "ok"}), encoding="utf-8")


def test_restart_autostart_proof_ready_with_valid_evidence_dir(tmp_path: Path) -> None:
    from mpf.services.phase11_restart_autostart_proof_service import build_phase11_restart_autostart_proof_report
    _write_ready_restart_evidence(tmp_path)
    report = build_phase11_restart_autostart_proof_report(tmp_path)
    assert report["restart_autostart_proof"] == "ready"
    assert report["final_decision"] == "RESTART_AUTOSTART_PROOF_READY"
    assert report["blockers"] == []
    assert report["next_required_step"] == "implement_production_customer_lifecycle_execution"
    for key in ("mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed"):
        assert report[key] is False


def test_restart_autostart_proof_malformed_json_fails_closed(tmp_path: Path) -> None:
    from mpf.services.phase11_restart_autostart_proof_service import build_phase11_restart_autostart_proof_report
    _write_ready_restart_evidence(tmp_path)
    (tmp_path / "proof-report.json").write_text("# command: bad\n{}", encoding="utf-8")
    report = build_phase11_restart_autostart_proof_report(tmp_path)
    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert "malformed_json_evidence:proof-report.json" in report["blockers"]


def test_restart_autostart_proof_script_json_captures_have_no_comment_headers() -> None:
    text = Path("scripts/phase11_collect_restart_autostart_proof.sh").read_text(encoding="utf-8")
    assert "run_capture_json proof-report.json" in text
    assert "run_capture_json controlled-backend-target.json" in text
    assert "run_capture proof-report.json" not in text
    assert ".meta.txt" in text
