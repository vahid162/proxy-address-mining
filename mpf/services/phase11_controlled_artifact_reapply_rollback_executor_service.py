from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import CommandResult, ProductionIptablesRestoreRunner, _text_sha

READY_TEST_ONLY = "CONTROLLED_ARTIFACT_REAPPLY_ROLLBACK_TEST_READY"
APPLIED = "CONTROLLED_ARTIFACT_REAPPLY_ROLLBACK_APPLIED_PENDING_REVIEW"
BLOCKED = "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_ROLLBACK"


def _run(runner: Any, argv: list[str], payload: str) -> CommandResult:
    result = runner.run(argv, input_text=payload)
    if isinstance(result, CommandResult):
        return result
    return CommandResult(int(getattr(result, "returncode", 1)), str(getattr(result, "stdout", "")), str(getattr(result, "stderr", "")))


def build_exact_inverse_payload(rollback_plan: dict[str, object]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if rollback_plan.get("manual_review_required") is not True:
        blockers.append("manual_review_required_flag_missing")
    if rollback_plan.get("broad_restore") is True or rollback_plan.get("restore_payload"):
        blockers.append("broad_restore_refused")
    delta = rollback_plan.get("exact_inverse_delta")
    if not isinstance(delta, list) or not delta:
        blockers.append("exact_inverse_delta_missing")
        return "", blockers
    ordered: list[tuple[str, str]] = []
    for item in sorted([d for d in delta if isinstance(d, dict)], key=lambda d: int(d.get("dependency_order", 0)), reverse=True):
        table = str(item.get("table") or "")
        rule = str(item.get("exact_rule_text") or "")
        if table not in {"filter", "nat"}:
            blockers.append(f"rollback_table_not_allowed:{table}")
            continue
        if any(bad in rule for bad in ("*raw", "*mangle", "COMMIT", "iptables-restore", "systemctl", "docker", "conntrack")):
            blockers.append("broad_restore_refused")
            continue
        if rule.startswith("-A "):
            ordered.append((table, "-D " + rule[3:]))
        elif rule.startswith("-N "):
            ordered.append((table, "-X " + rule[3:]))
        else:
            blockers.append("rollback_rule_not_invertible")
    parts: list[str] = []
    current_table: str | None = None
    for table, line in ordered:
        if table != current_table:
            if current_table is not None:
                parts.append("COMMIT")
            parts.append(f"*{table}")
            current_table = table
        parts.append(line)
    if current_table is not None:
        parts.append("COMMIT")
    return "\n".join(parts) + ("\n" if parts else ""), sorted(set(blockers))


def execute_reviewed_rollback(
    *,
    package: dict[str, object],
    operator: str,
    reason: str,
    yes: bool = False,
    apply: bool = False,
    env: dict[str, str] | None = None,
    runner: Any | None = None,
    expected_version: str = __version__,
) -> dict[str, object]:
    blockers: list[str] = []
    if expected_version != __version__ or package.get("repository_version") != __version__:
        blockers.append("version_mismatch")
    if not operator.strip() or not reason.strip():
        blockers.append("operator_and_reason_required")
    rollback_plan = package.get("rollback_plan") if isinstance(package.get("rollback_plan"), dict) else {}
    payload, payload_blockers = build_exact_inverse_payload(rollback_plan)
    blockers.extend(payload_blockers)
    if not payload.strip():
        blockers.append("rollback_payload_empty")
    runtime_env = os.environ if env is None else env
    if apply:
        if not yes:
            blockers.append("yes_confirmation_required")
        if runtime_env.get("MPF_PHASE11_CONTROLLED_ARTIFACT_ROLLBACK") != "allow":
            blockers.append("controlled_artifact_rollback_env_gate_missing")
    if blockers:
        return {"component": "phase11_controlled_artifact_reapply_rollback_executor", "repository_version": __version__, "final_decision": BLOCKED, "blockers": sorted(set(blockers)), "rollback_test_invoked": False, "rollback_apply_invoked": False, "firewall_mutation_performed": False, "payload_sha256": _text_sha(payload), "payload": payload}
    runner = runner or ProductionIptablesRestoreRunner()
    test = _run(runner, ["iptables-restore", "--test", "--noflush"], payload)
    if test.returncode != 0:
        return {"component": "phase11_controlled_artifact_reapply_rollback_executor", "repository_version": __version__, "final_decision": BLOCKED, "blockers": ["rollback_restore_test_failed"], "rollback_test_invoked": True, "rollback_apply_invoked": False, "firewall_mutation_performed": False, "payload_sha256": _text_sha(payload), "payload": payload, "test": test.__dict__}
    if not apply:
        return {"component": "phase11_controlled_artifact_reapply_rollback_executor", "repository_version": __version__, "final_decision": READY_TEST_ONLY, "blockers": [], "rollback_test_invoked": True, "rollback_apply_invoked": False, "firewall_mutation_performed": False, "payload_sha256": _text_sha(payload), "payload": payload, "test": test.__dict__}
    applied = _run(runner, ["iptables-restore", "--noflush"], payload)
    if applied.returncode != 0:
        return {"component": "phase11_controlled_artifact_reapply_rollback_executor", "repository_version": __version__, "final_decision": BLOCKED, "blockers": ["rollback_restore_apply_failed"], "rollback_test_invoked": True, "rollback_apply_invoked": True, "firewall_mutation_performed": False, "payload_sha256": _text_sha(payload), "payload": payload, "test": test.__dict__, "apply": applied.__dict__}
    return {"component": "phase11_controlled_artifact_reapply_rollback_executor", "repository_version": __version__, "final_decision": APPLIED, "blockers": [], "rollback_test_invoked": True, "rollback_apply_invoked": True, "firewall_mutation_performed": True, "payload_sha256": _text_sha(payload), "payload": payload, "test": test.__dict__, "apply": applied.__dict__, "post_rollback_required_checks": ["current-controlled-artifact-gate", "doctor", "proxy doctor"]}


def load_package(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("package_json_must_be_object")
    return value
