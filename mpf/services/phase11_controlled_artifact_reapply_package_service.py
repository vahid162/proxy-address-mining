from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.repositories import firewall_planner_read_repo
from mpf.services.phase11_controlled_artifact_reapply_core import build_package_from_plan, build_plan
from mpf.services.phase11_controlled_backend_target_service import build_controlled_backend_target_report


@dataclass(frozen=True)
class FirewallSnapshotCommandResult:
    argv: list[str]
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _cmd(argv: list[str]) -> FirewallSnapshotCommandResult:
    try:
        r = subprocess.run(argv, shell=False, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        return FirewallSnapshotCommandResult(argv=argv, command=argv[0], returncode=127, stdout="", stderr=str(exc))
    return FirewallSnapshotCommandResult(argv=argv, command=argv[0], returncode=r.returncode, stdout=r.stdout, stderr=r.stderr)


def _snapshot_structure_blockers(result: FirewallSnapshotCommandResult, *, family: str) -> list[str]:
    failed = f"{family}_save_read_failed"
    invalid = f"{family}_snapshot_empty_or_invalid"
    if not result.ok:
        return [failed]
    text = result.stdout.strip()
    if not text:
        return [invalid]
    tables: list[str] = []
    open_table = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("*"):
            if open_table is not None:
                return [invalid]
            open_table = line[1:]
            tables.append(open_table)
        elif line == "COMMIT":
            if open_table is None:
                return [invalid]
            open_table = None
    if open_table is not None or not tables:
        return [invalid]
    return []


def _phase_text() -> str:
    try:
        return Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def build_controlled_artifact_reapply_plan_report(*, lanes: list[dict[str, Any]], customers: list[dict[str, Any]], backend_target: dict[str, object], iptables_save_text: str = "", ip6tables_save_text: str = "", phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    return build_plan(lanes=lanes, customers=customers, backend_target=backend_target, iptables_save_text=iptables_save_text, ip6tables_save_text=ip6tables_save_text, phase_status_text=phase_status_text, expected_version=expected_version)


def build_controlled_artifact_reapply_package_report(*, plan: dict[str, object]) -> dict[str, object]:
    return build_package_from_plan(plan)


def run_controlled_artifact_reapply_plan(config_path: Path = DEFAULT_CONFIG_PATH, *, expected_version: str = __version__) -> dict[str, object]:
    cfg = load_config(config_path)
    loaded = firewall_planner_read_repo.load_firewall_planner_input(cfg)
    if not loaded.ok:
        return {"component": "phase11_controlled_artifact_reapply_plan", "repository_version": __version__, "expected_version": expected_version, "final_decision": "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE", "blockers": ["postgresql_planner_input_read_failed"], "message": loaded.message, "mutation_performed": False}
    backend = build_controlled_backend_target_report(expected_version=expected_version)
    # 0.1.272: the accepted/current farm5 controlled graph is the corrected
    # Docker-user forward post-DNAT binding. The generic reapply plan must not
    # fall back to the older pre-DNAT INPUT/public-port filter payload after the
    # current controlled artifact gate has passed.
    backend["controlled_artifact_graph_binding_mode"] = "verified_docker_user_forward_post_dnat"
    backend.setdefault("filter_packet_path", "docker_user_forward_verified")
    backend.setdefault("conntrack_original_destination_supported", True)
    iptables_result = _cmd(["iptables-save"])
    ip6tables_result = _cmd(["ip6tables-save"])
    snapshot_blockers = [*_snapshot_structure_blockers(iptables_result, family="iptables"), *_snapshot_structure_blockers(ip6tables_result, family="ip6tables")]
    report = build_controlled_artifact_reapply_plan_report(lanes=loaded.lanes, customers=loaded.customers, backend_target=backend, iptables_save_text=iptables_result.stdout, ip6tables_save_text=ip6tables_result.stdout, phase_status_text=_phase_text(), expected_version=expected_version)
    report["iptables_save_text"] = iptables_result.stdout
    report["ip6tables_save_text"] = ip6tables_result.stdout
    report["firewall_snapshot_commands"] = {"iptables-save": iptables_result.__dict__, "ip6tables-save": ip6tables_result.__dict__}
    if snapshot_blockers:
        report["blockers"] = sorted(set([*report.get("blockers", []), *snapshot_blockers]))
        report["final_decision"] = "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"
    return report


def run_controlled_artifact_reapply_package(config_path: Path = DEFAULT_CONFIG_PATH, *, expected_version: str = __version__) -> dict[str, object]:
    plan = run_controlled_artifact_reapply_plan(config_path, expected_version=expected_version)
    return build_package_from_plan(plan)
