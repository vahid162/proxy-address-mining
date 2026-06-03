"""Read-only Phase 11 restart/autostart proof evaluation service."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from mpf import __version__


_COMPONENT = "phase11_restart_autostart_proof"
_SCOPE = "full_cli_production_operations"
_MISSING_OR_PARTIAL = "missing_or_partial"
_READY = "ready"
_BLOCKED = "BLOCKED_RESTART_AUTOSTART_PROOF_MISSING_OR_PARTIAL"
_READY_DECISION = "RESTART_AUTOSTART_PROOF_READY"
_MUTATION_FLAGS: dict[str, bool] = {
    "mutation_performed": False,
    "db_mutation_performed": False,
    "firewall_apply_performed": False,
    "conntrack_flush_performed": False,
    "docker_restart_performed": False,
    "systemd_restart_performed": False,
}
_SAFE_GATE_FIELDS: dict[str, object] = {
    "phase12_start_allowed": False,
    "worker_enforcement_allowed": "no",
    "ui_allowed": "no",
    "telegram_allowed": "no",
    "production_traffic": "controlled_cli_limited",
    "customer_onboarding_allowed": "controlled_cli_limited",
}


@dataclass(frozen=True)
class _CheckSpec:
    name: str
    evidence_file: str
    description: str


_CHECKS: tuple[_CheckSpec, ...] = (
    _CheckSpec("repository_version_after_sync", "repository_version.txt", "repository version matches the expected package version"),
    _CheckSpec("phase_status_after_restart", "phase_status.txt", "Phase 11 accepted/operational-completion gate is visible and later phases remain blocked"),
    _CheckSpec("mpf_cli_after_restart", "mpf_version.txt", "mpf CLI responds after restart/reboot"),
    _CheckSpec("postgresql_reachable", "db_ping.txt", "PostgreSQL accepts a read-only ping"),
    _CheckSpec("db_schema_status_visible", "db_status.txt", "DB schema/status output is visible"),
    _CheckSpec("lanes_visible_from_db", "lanes.txt", "lanes are visible from DB/service read path"),
    _CheckSpec("customers_visible_from_db", "customers.txt", "customers are visible from DB/service read path"),
    _CheckSpec("accepted_proxy_containers_running", "docker_ps.txt", "accepted limited proxy containers are present/running"),
    _CheckSpec("container_listener_dependency_order_visible", "container_listener_order.txt", "container/listener order and dependency expectations are visible"),
    _CheckSpec("v2raya_ui_local_only", "listeners.txt", "v2rayA UI listener remains local-only on 127.0.0.1"),
    _CheckSpec("btc_backend_local_only", "listeners.txt", "BTC backend listener remains local-only on 127.0.0.1:60010"),
    _CheckSpec("backend_not_publicly_exposed", "listeners.txt", "backend is not publicly exposed"),
    _CheckSpec("known_phase11_firewall_artifacts_recognized", "phase11_firewall_artifacts.txt", "known controlled Phase 11 firewall artifacts are recognized"),
    _CheckSpec("unknown_mpf_firewall_artifacts_empty", "unknown_mpf_firewall_artifacts.txt", "unknown MPF firewall artifacts are empty"),
    _CheckSpec("phase12_blocked", "phase_status.txt", "Phase 12 remains blocked"),
    _CheckSpec("worker_enforcement_disabled", "phase_status.txt", "worker enforcement remains disabled"),
    _CheckSpec("ui_disabled", "phase_status.txt", "UI remains disabled"),
    _CheckSpec("telegram_disabled", "phase_status.txt", "Telegram remains disabled"),
    _CheckSpec("production_traffic_controlled_cli_limited", "phase_status.txt", "production traffic remains controlled_cli_limited"),
    _CheckSpec("customer_onboarding_controlled_cli_limited", "phase_status.txt", "customer onboarding remains controlled_cli_limited"),
    _CheckSpec("report_command_no_mutation", "mutation_flags.json", "the report command and helper declare no mutation"),
)


def _read_text(evidence_dir: Path, name: str) -> str | None:
    path = evidence_dir / name
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _load_json(evidence_dir: Path, name: str) -> dict[str, Any] | None:
    text = _read_text(evidence_dir, name)
    if text is None or not text.strip():
        return None
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _contains_all(text: str, needles: tuple[str, ...]) -> bool:
    return all(needle in text for needle in needles)


def _line_content_without_comments(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def _evaluate_check(name: str, evidence_dir: Path) -> tuple[str, str | None]:
    phase_status = _read_text(evidence_dir, "phase_status.txt") or ""
    listeners = _read_text(evidence_dir, "listeners.txt") or ""

    if name == "repository_version_after_sync":
        text = (_read_text(evidence_dir, "repository_version.txt") or "").strip()
        return ("passed", None) if text == __version__ else ("blocked", f"repository_version.txt must equal {__version__}")
    if name == "phase_status_after_restart":
        required = (
            "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5",
            "current_working_phase: Phase 11 operational completion — Full CLI Production Operations",
            "phase12_start_allowed: no",
        )
        return ("passed", None) if _contains_all(phase_status, required) else ("blocked", "phase_status.txt does not show the accepted Phase 11 operational-completion gate")
    if name == "mpf_cli_after_restart":
        text = (_read_text(evidence_dir, "mpf_version.txt") or "").strip()
        return ("passed", None) if text == __version__ else ("blocked", f"mpf_version.txt must equal {__version__}")
    if name == "postgresql_reachable":
        text = (_read_text(evidence_dir, "db_ping.txt") or "").strip().upper()
        return ("passed", None) if text == "OK" else ("blocked", "db_ping.txt must contain OK")
    if name == "db_schema_status_visible":
        text = _read_text(evidence_dir, "db_status.txt") or ""
        required = ("database: OK", "alembic_version:", "lanes:", "customers:")
        return ("passed", None) if _contains_all(text, required) else ("blocked", "db_status.txt must show database/schema/lanes/customers status")
    if name == "lanes_visible_from_db":
        text = _read_text(evidence_dir, "lanes.txt") or ""
        lines = _line_content_without_comments(text)
        ok = bool(lines) and "no lanes" not in text.lower() and "btc" in text.lower()
        return ("passed", None) if ok else ("blocked", "lanes.txt must show at least the BTC lane from the DB/service read path")
    if name == "customers_visible_from_db":
        text = _read_text(evidence_dir, "customers.txt") or ""
        lower = text.lower()
        lines = _line_content_without_comments(text)
        ok = bool(lines) and "no customers" not in lower and "no non-deleted customers" not in lower
        return ("passed", None) if ok else ("blocked", "customers.txt must show current customer rows from the DB/service read path")
    if name == "accepted_proxy_containers_running":
        text = (_read_text(evidence_dir, "docker_ps.txt") or "").lower()
        ok = "v2raya" in text and "btc" in text and ("up" in text or "running" in text)
        return ("passed", None) if ok else ("blocked", "docker_ps.txt must show v2rayA and BTC proxy/forwarder containers running")
    if name == "container_listener_dependency_order_visible":
        text = (_read_text(evidence_dir, "container_listener_order.txt") or "").lower()
        required = ("v2raya", "btc", "127.0.0.1:2015", "127.0.0.1:60010")
        return ("passed", None) if _contains_all(text, required) else ("blocked", "container_listener_order.txt must show v2rayA/BTC listener dependency order")
    if name == "v2raya_ui_local_only":
        ok = "127.0.0.1:2015" in listeners and "0.0.0.0:2015" not in listeners and "*:2015" not in listeners
        return ("passed", None) if ok else ("blocked", "listeners.txt must show v2rayA UI only on 127.0.0.1:2015")
    if name == "btc_backend_local_only":
        ok = "127.0.0.1:60010" in listeners and "0.0.0.0:60010" not in listeners and "*:60010" not in listeners
        return ("passed", None) if ok else ("blocked", "listeners.txt must show BTC backend only on 127.0.0.1:60010")
    if name == "backend_not_publicly_exposed":
        forbidden = ("0.0.0.0:60010", "*:60010", "[::]:60010", "0.0.0.0:2015", "*:2015", "[::]:2015")
        return ("passed", None) if listeners and not any(item in listeners for item in forbidden) else ("blocked", "listeners.txt shows missing or public backend/UI exposure evidence")
    if name == "known_phase11_firewall_artifacts_recognized":
        text = (_read_text(evidence_dir, "phase11_firewall_artifacts.txt") or "").lower()
        ok = "known_controlled_phase11_artifacts: present" in text or "known_controlled_phase11_artifacts=present" in text
        return ("passed", None) if ok else ("blocked", "phase11_firewall_artifacts.txt must recognize known controlled Phase 11 artifacts")
    if name == "unknown_mpf_firewall_artifacts_empty":
        text = _read_text(evidence_dir, "unknown_mpf_firewall_artifacts.txt")
        if text is None:
            return "blocked", "unknown_mpf_firewall_artifacts.txt is missing"
        lines = _line_content_without_comments(text)
        ok = not lines or lines == ["unknown_mpf_firewall_artifacts: []"] or lines == ["unknown_mpf_firewall_artifacts=[]"]
        return ("passed", None) if ok else ("blocked", "unknown_mpf_firewall_artifacts.txt must be empty or an explicit empty list")
    if name == "phase12_blocked":
        return ("passed", None) if "phase12_start_allowed: no" in phase_status else ("blocked", "phase12_start_allowed must remain no")
    if name == "worker_enforcement_disabled":
        return ("passed", None) if "worker_enforcement_allowed: no" in phase_status else ("blocked", "worker_enforcement_allowed must remain no")
    if name == "ui_disabled":
        return ("passed", None) if "ui_allowed: no" in phase_status else ("blocked", "ui_allowed must remain no")
    if name == "telegram_disabled":
        return ("passed", None) if "telegram_allowed: no" in phase_status else ("blocked", "telegram_allowed must remain no")
    if name == "production_traffic_controlled_cli_limited":
        return ("passed", None) if "production_traffic: controlled_cli_limited" in phase_status else ("blocked", "production_traffic must remain controlled_cli_limited")
    if name == "customer_onboarding_controlled_cli_limited":
        ok = "customer_onboarding_allowed: controlled_cli_limited" in phase_status
        return ("passed", None) if ok else ("blocked", "customer_onboarding_allowed must remain controlled_cli_limited")
    if name == "report_command_no_mutation":
        flags = _load_json(evidence_dir, "mutation_flags.json")
        ok = isinstance(flags, dict) and all(flags.get(key) is False for key in _MUTATION_FLAGS)
        return ("passed", None) if ok else ("blocked", "mutation_flags.json must explicitly set all mutation flags to false")
    return "blocked", f"unknown check {name}"


def build_phase11_restart_autostart_proof_report(evidence_dir: Path | str | None = None) -> dict[str, object]:
    """Evaluate source-backed restart/autostart evidence without performing mutation."""

    checks: list[dict[str, object]] = []
    blockers: list[str] = []
    warnings: list[str] = []

    evidence_path = Path(evidence_dir).expanduser() if evidence_dir else None
    if evidence_path is None:
        blockers.append("restart_autostart_evidence_dir_missing")
        warnings.append("run scripts/phase11_collect_restart_autostart_proof.sh on farm5 and pass its evidence directory")
        for spec in _CHECKS:
            checks.append({"name": spec.name, "status": "blocked", "evidence_file": spec.evidence_file, "description": spec.description, "blocker": "evidence_dir_missing"})
    elif not evidence_path.is_dir():
        blockers.append("restart_autostart_evidence_dir_not_found")
        for spec in _CHECKS:
            checks.append({"name": spec.name, "status": "blocked", "evidence_file": spec.evidence_file, "description": spec.description, "blocker": "evidence_dir_not_found"})
    else:
        for spec in _CHECKS:
            evidence_file = evidence_path / spec.evidence_file
            if not evidence_file.is_file():
                blocker = f"missing_evidence:{spec.evidence_file}"
                blockers.append(blocker)
                checks.append({"name": spec.name, "status": "blocked", "evidence_file": spec.evidence_file, "description": spec.description, "blocker": blocker})
                continue
            status, blocker_message = _evaluate_check(spec.name, evidence_path)
            item: dict[str, object] = {"name": spec.name, "status": status, "evidence_file": spec.evidence_file, "description": spec.description}
            if blocker_message:
                blocker = f"{spec.name}:{blocker_message}"
                blockers.append(blocker)
                item["blocker"] = blocker_message
            checks.append(item)

    ready = not blockers
    return {
        "component": _COMPONENT,
        "repository_version": __version__,
        "phase11_operational_completion_scope": _SCOPE,
        "restart_autostart_proof": _READY if ready else _MISSING_OR_PARTIAL,
        **_SAFE_GATE_FIELDS,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        **_MUTATION_FLAGS,
        "final_decision": _READY_DECISION if ready else _BLOCKED,
        "next_required_step": "implement_production_customer_lifecycle_execution" if ready else "run_restart_autostart_proof_on_farm5",
    }
