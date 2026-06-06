from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.repositories import firewall_planner_read_repo
from mpf.services.phase11_controlled_artifact_reapply_core import build_package_from_plan, build_plan
from mpf.services.phase11_controlled_backend_target_service import build_controlled_backend_target_report


def _cmd(argv: list[str]) -> str:
    try:
        r = subprocess.run(argv, shell=False, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return ""
    return r.stdout if r.returncode == 0 else ""


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
    return build_controlled_artifact_reapply_plan_report(lanes=loaded.lanes, customers=loaded.customers, backend_target=backend, iptables_save_text=_cmd(["iptables-save"]), ip6tables_save_text=_cmd(["ip6tables-save"]), phase_status_text=_phase_text(), expected_version=expected_version)


def run_controlled_artifact_reapply_package(config_path: Path = DEFAULT_CONFIG_PATH, *, expected_version: str = __version__) -> dict[str, object]:
    plan = run_controlled_artifact_reapply_plan(config_path, expected_version=expected_version)
    return build_package_from_plan(plan)
