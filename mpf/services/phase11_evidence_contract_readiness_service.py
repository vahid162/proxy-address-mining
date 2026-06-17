"""Read-only evidence-dir contracts for remaining Phase 11 operational surfaces."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from mpf import __version__

_FALSE_FLAGS = (
    "mutation_performed",
    "db_mutation_performed",
    "firewall_apply_performed",
    "conntrack_flush_performed",
    "docker_restart_performed",
    "systemd_restart_performed",
    "phase12_start_allowed",
)

_GATE_FLAGS = {
    "worker_enforcement_allowed": "no",
    "ui_allowed": "no",
    "telegram_allowed": "no",
    "production_traffic": "controlled_cli_limited",
    "customer_onboarding_allowed": "controlled_cli_limited",
}


def _load(evidence_dir: Path | str | None, name: str) -> dict[str, Any] | None:
    if not evidence_dir:
        return None
    p = Path(evidence_dir) / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"_invalid_json": True}


def build_contract_readiness_report(
    kind: str, evidence_dir: Path | str | None = None
) -> dict[str, Any]:
    filename = f"{kind}.json"
    data = _load(evidence_dir, filename)
    blockers = []
    if data is None:
        blockers.append(f"{kind}_evidence_missing")
    elif data.get("_invalid_json"):
        blockers.append(f"{kind}_evidence_invalid_json")
    else:
        if kind == "production_controls_pause_block_expire":
            if data.get("pause_preflight", {}).get("ready") is not True:
                blockers.append("pause_preflight_not_ready")
            if data.get("expire_run_preflight", {}).get("ready") is not True:
                blockers.append("expire_run_preflight_not_ready")
            if data.get("block_preflight", {}).get("ready") is not True:
                blockers.append("block_preflight_not_ready")
            if data.get("production_controls_pause_block_expire_ready") is not True:
                blockers.append(f"{kind}_ready_flag_missing")
        elif (
            data.get(kind) not in {f"{kind}_ready", "ready"}
            and data.get("ready") is not True
        ):
            blockers.append(f"{kind}_ready_flag_missing")
        for k in _FALSE_FLAGS:
            if data.get(k) not in (False, None):
                blockers.append(f"unsafe_or_mutating_flag:{k}")
        for k, expected in _GATE_FLAGS.items():
            if data.get(k, expected) != expected:
                blockers.append(f"unsafe_gate_flag:{k}")
        for k in ("operator", "evidence_collected_at", "scope", "final_decision"):
            if not data.get(k):
                blockers.append(f"{kind}_missing_{k}")
    ready = not blockers
    return {
        "component": f"phase11_{kind}_readiness",
        "repository_version": __version__,
        kind: f"{kind}_ready" if ready else "missing_or_partial",
        f"{kind}_ready": ready,
        "expected_evidence_file": filename,
        "required_fields": [
            "operator",
            "evidence_collected_at",
            "scope",
            "final_decision",
            "ready",
        ],
        "blockers": blockers,
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
        "final_decision": (
            f"{kind.upper()}_READY"
            if ready
            else f"BLOCKED_{kind.upper()}_MISSING_OR_PARTIAL"
        ),
    }
