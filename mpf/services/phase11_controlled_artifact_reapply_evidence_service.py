from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import collect_evidence_bundle
from mpf.services.phase11_controlled_backend_target_service import build_controlled_backend_target_report


def _cmd(argv: list[str]) -> dict[str, object]:
    try:
        result = subprocess.run(argv, shell=False, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        return {"argv": argv, "returncode": 127, "stdout": "", "stderr": str(exc), "sha256": None}
    return {"argv": argv, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "sha256": hashlib.sha256(result.stdout.encode()).hexdigest()}


def _phase_status_text() -> str:
    try:
        return Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def build_controlled_artifact_reapply_evidence_report(*, plan=None, package=None) -> dict[str, object]:
    evidence = collect_evidence_bundle(plan=plan, package=package)
    read_only = {
        "repository_version": __version__,
        "phase_status_text": _phase_status_text(),
        "backend_target_resolution": build_controlled_backend_target_report(),
        "iptables_save": _cmd(["iptables-save"]),
        "ip6tables_save": _cmd(["ip6tables-save"]),
        "listeners": _cmd(["ss", "-ltn"]),
        "docker_inspect_forwarder": _cmd(["docker", "inspect", "mpf-forwarder-btc"]),
        "db_status": _cmd(["mpf", "db", "status", "--output", "json"]),
        "proxy_doctor": _cmd(["mpf", "proxy", "doctor", "--output", "json"]),
    }
    evidence["read_only_evidence"] = read_only
    evidence["sha256_manifest"] = {key: hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest() for key, value in read_only.items()}
    evidence["mutation_performed"] = False
    return evidence
