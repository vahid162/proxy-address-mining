from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__

SCOPE = {
    "candidate_customer_key": "limited-btc-001",
    "lane": "btc",
    "public_port": 20101,
    "backend_target": "172.18.0.3:60010",
}
CANARY_KEY = "canary-btc-001"
SAFE_ARTIFACT_DECISIONS = {"PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS", "PASS_NO_CUSTOMER_ARTIFACTS"}
PHASE11_PRE_FINAL_ACCEPTANCE_GATE = {
    "current_accepted_phase": "Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5",
    "current_working_phase": "Phase 11 — Production / Customer Activation Gate planning/readiness",
    "production_traffic": "none",
    "firewall_apply_allowed": "no",
    "abuse_automation_allowed": "no",
    "customer_onboarding_allowed": "db_only",
    "proxy_data_plane_allowed": "limited_runtime_local_only",
    "ui_allowed": "no",
    "telegram_allowed": "no",
}
PHASE11_POST_FINAL_ACCEPTANCE_GATE = {
    "current_accepted_phase": "Phase 11 — Production / Customer Activation Gate accepted on farm5",
    "current_working_phase": "Phase 11 operational completion — Full CLI Production Operations",
    "server_state": "farm5 controlled CLI-limited BTC production/customer activation is accepted; Phase 11 operational completion now requires Full CLI Production Operations acceptance before Phase 12 implementation",
    "production_traffic": "controlled_cli_limited",
    "firewall_apply_allowed": "controlled",
    "abuse_automation_allowed": "controlled_operator_gated",
    "customer_onboarding_allowed": "controlled_cli_limited",
    "proxy_data_plane_allowed": "limited_runtime_local_only",
    "worker_enforcement_allowed": "no",
    "ui_allowed": "no",
    "telegram_allowed": "no",
    "phase12_start_allowed": "no",
    "live_snapshot_read_allowed": "iptables_save_read_only",
    "restore_lock_record_execution_allowed": "controlled_boundary_only",
}
# Backward-compatible alias for historical pre-acceptance services and fixtures.
PHASE_GATE_REQUIREMENTS = PHASE11_PRE_FINAL_ACCEPTANCE_GATE

OK_STATUSES = {"OK", "PASS", "HEALTHY", "READY"}


def status_is_ok(value: object, *, verdict_key: str | None = None) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("ok") is True:
        return True
    if str(value.get("status", "")).strip().upper() in OK_STATUSES:
        return True
    return verdict_key is not None and str(value.get(verdict_key, "")).strip().upper() in OK_STATUSES


def source_db_ok(source: dict[str, object]) -> bool:
    return source.get("db_ok") is True or status_is_ok(source.get("db_status"))


def source_proxy_ok(source: dict[str, object]) -> bool:
    return source.get("proxy_ok") is True or status_is_ok(source.get("proxy_doctor"), verdict_key="final_verdict")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_hashed_json(kwargs: dict[str, object], path_key: str, hash_key: str, blockers: list[str]) -> dict[str, object] | None:
    raw_path = str(kwargs.get(path_key, "")).strip()
    expected_hash = str(kwargs.get(hash_key, "")).strip()
    if not raw_path:
        blockers.append(f"{path_key}_missing")
        return None
    if not expected_hash:
        blockers.append(f"{hash_key}_missing")
    path = Path(raw_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - reports must fail closed rather than traceback
        blockers.append(f"{path_key}_invalid")
        return None
    if not isinstance(payload, dict):
        blockers.append(f"{path_key}_invalid")
        return None
    try:
        actual_hash = sha256_file(path)
    except OSError:
        blockers.append(f"{path_key}_invalid")
        return None
    if not expected_hash or actual_hash != expected_hash:
        blockers.append(f"{path_key}_hash_mismatch")
    return payload


def validate_confirmations(kwargs: dict[str, object], names: tuple[str, ...], blockers: list[str]) -> None:
    for name in names:
        if kwargs.get(name) is not True:
            blockers.append(f"missing_confirmation:{name}")


def validate_expected_version(kwargs: dict[str, object], blockers: list[str]) -> str:
    expected_version = str(kwargs.get("expected_version", "")).strip()
    if expected_version != __version__:
        blockers.append("expected_version_mismatch")
    return expected_version


def validate_operator(kwargs: dict[str, object], blockers: list[str]) -> None:
    if not str(kwargs.get("operator", "")).strip():
        blockers.append("operator_missing")
    if not str(kwargs.get("reason", "")).strip():
        blockers.append("reason_missing")


def validate_scope(payload: dict[str, object] | None, blockers: list[str], tag: str) -> None:
    if payload is None:
        return
    for key, expected in SCOPE.items():
        value = payload.get(key)
        if key == "lane":
            value = payload.get("candidate_lane", value)
        elif key == "public_port":
            value = payload.get("candidate_public_port", value)
        elif key == "backend_target":
            value = payload.get("candidate_backend_target", value)
        if value != expected:
            blockers.append(f"scope_mismatch:{tag}:{key}")


def validate_rollback_package_scope(payload: dict[str, object] | None, blockers: list[str]) -> None:
    if payload is None:
        return
    if payload.get("component") != "phase11e_limited_activation_rollback_package":
        blockers.append("scope_mismatch:rollback_package:schema")
    rollback_scope = {
        "candidate_customer_key": payload.get("rollback_customer_key"),
        "lane": payload.get("rollback_lane"),
        "public_port": payload.get("rollback_public_port"),
        "backend_target": payload.get("rollback_backend_target"),
    }
    for key, expected in SCOPE.items():
        if rollback_scope[key] != expected:
            blockers.append(f"scope_mismatch:rollback_package:{key}")


def validate_artifact_gate(payload: dict[str, object] | None, blockers: list[str]) -> None:
    if payload is None:
        return
    if payload.get("final_decision") not in SAFE_ARTIFACT_DECISIONS:
        blockers.append("artifact_gate_not_passed")
    if payload.get("unknown_mpf_artifacts") != []:
        blockers.append("unknown_mpf_artifacts")
    if payload.get("forbidden_public_runtime_exposure") is not False:
        blockers.append("forbidden_public_runtime_exposure")
    if payload.get("production_gates_remain_closed") is not True:
        blockers.append("production_gates_not_closed")


def _extract_current_state_block(text: str) -> str | None:
    marker = "## Current State"
    marker_index = text.find(marker)
    if marker_index == -1:
        return None
    section = text[marker_index + len(marker):]
    next_heading = section.find("\n## ")
    if next_heading != -1:
        section = section[:next_heading]
    block_start = section.find("```text")
    if block_start == -1:
        return None
    block_body_start = block_start + len("```text")
    block_end = section.find("```", block_body_start)
    if block_end == -1:
        return None
    block = section[block_body_start:block_end].strip()
    return block or None


def validate_current_phase_gate(
    blockers: list[str],
    *,
    phase_status_path: Path = Path("docs/PHASE_STATUS.md"),
    requirements: dict[str, str] = PHASE11_POST_FINAL_ACCEPTANCE_GATE,
) -> None:
    try:
        text = phase_status_path.read_text(encoding="utf-8")
    except OSError:
        blockers.append("current_phase_gate_unreadable")
        return
    current_state = _extract_current_state_block(text)
    if current_state is None:
        blockers.append("current_phase_gate_malformed")
        return
    current_values: dict[str, str] = {}
    for line in current_state.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current_values[key.strip()] = value.strip()
    for key, value in requirements.items():
        if current_values.get(key) != value:
            blockers.append(f"current_phase_gate_open:{key}")


def base_report(component: str, expected_version: str) -> dict[str, object]:
    return {
        "component": component,
        "expected_version": expected_version,
        "repository_version": __version__,
        **SCOPE,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "abuse_automation_enabled": False,
        "phase11_accepted": False,
    }
