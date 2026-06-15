"""Phase 11 live-ready controlled artifact reapply package review service.

Read-only bridge from verified packet-path/filter-hook evidence to the live-ready
controlled artifact reapply package. This module never executes packages and
never invokes the firewall restore apply command.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.repositories import firewall_planner_read_repo
from mpf.services import phase11_controlled_artifact_reapply_package_service as package_service
from mpf.services import phase11_controlled_artifact_refresh_service as refresh_service
from mpf.services.phase11_controlled_artifact_reapply_core import SCOPE, _canonical_sha, _package_content_for_hash, _text_sha, build_package_from_plan, build_plan, verify_package
from mpf.services.phase11_verified_filter_hook_binding_service import READY_BINDING, binding_backend_target, build_verified_filter_hook_binding_report

READY = "READY_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"
BLOCKED = "BLOCKED_LIVE_READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"
PACKAGE_READY = "CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY"
VERIFY_READY = "CONTROLLED_ARTIFACT_REAPPLY_VERIFY_READY"


def _atomic_write_json(path: Path, data: object) -> str:
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.chmod(0o600)
    os.replace(tmp, path)
    return _text_sha(text)


def _atomic_write_text(path: Path, text: str) -> str:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.chmod(0o600)
    os.replace(tmp, path)
    return _text_sha(text)


def _scope_blockers(customers: list[dict[str, Any]]) -> list[str]:
    got = sorted((str(c.get("customer_key")), int(c.get("port", -1))) for c in customers)
    want = sorted((str(c["customer_key"]), int(c["public_port"])) for c in SCOPE)
    return [] if got == want and len(customers) == 2 else ["controlled_customer_scope_mismatch"]


def _load_planner_input(config_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    try:
        loaded = firewall_planner_read_repo.load_firewall_planner_input(load_config(config_path))
    except Exception as exc:  # noqa: BLE001
        return [], [], ["postgresql_planner_input_read_failed", str(exc)]
    if not loaded.ok:
        return [], [], ["postgresql_planner_input_read_failed", loaded.message]
    return loaded.lanes, loaded.customers, _scope_blockers(loaded.customers)


def build_fail_closed_live_ready_reapply_package_report(expected_version: str, blockers: list[str], *, binding: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "component": "phase11_live_ready_reapply_package",
        "repository_version": __version__,
        "expected_version": expected_version,
        "binding_final_decision": (binding or {}).get("final_decision"),
        "live_ready_package_available": False,
        "package_verified_against_live_plan": False,
        "package_generated": False,
        "backup_requirements_ready": False,
        "rollback_plan_ready": False,
        "lock_requirements_ready": False,
        "operator_confirmations_required": [],
        "production_execution_available": False,
        "controlled_artifact_execute_available": False,
        "iptables_restore_invocation_allowed": False,
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
        "blockers": sorted(set(blockers)),
        "final_decision": BLOCKED,
    }


def build_live_ready_reapply_package_report(
    *,
    packet_path_evidence_dir: Path | str | None,
    lanes: list[dict[str, Any]],
    customers: list[dict[str, Any]],
    iptables_save_text: str = "",
    ip6tables_save_text: str = "",
    phase_status_text: str = "",
    expected_version: str = __version__,
    output_dir: Path | str | None = None,
    second_plan: dict[str, Any] | None = None,
    controlled_refresh_mode: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    if expected_version != __version__:
        blockers.append("repository_version_mismatch")
    if packet_path_evidence_dir is None or not Path(packet_path_evidence_dir).is_dir():
        return build_fail_closed_live_ready_reapply_package_report(expected_version, ["packet_path_evidence_dir_missing", *blockers])
    binding = build_verified_filter_hook_binding_report(packet_path_evidence_dir)
    binding_ready = binding.get("final_decision") == READY_BINDING
    blockers.extend(_scope_blockers(customers))
    backend_target = binding_backend_target(binding)
    if controlled_refresh_mode and "conntrack_original_destination_supported" not in backend_target:
        backend_target["conntrack_original_destination_supported"] = True
    if controlled_refresh_mode and not binding_ready:
        refresh_plan = refresh_service.build_refresh_plan(lanes=lanes, customers=customers, backend_target=backend_target, iptables_save_text=iptables_save_text, ip6tables_save_text=ip6tables_save_text, phase_status_text=phase_status_text, expected_version=expected_version)
        refresh_package = refresh_service.build_refresh_package_from_plan(refresh_plan)
        if refresh_plan.get("final_decision") == refresh_service.REFRESH_READY:
            return {"component": "phase11_live_ready_controlled_artifact_refresh_package", "repository_version": __version__, "expected_version": expected_version, "binding_final_decision": binding.get("final_decision"), "binding_bypassed_for_exact_stale_refresh": True, "stale_graph_classifier": refresh_plan.get("stale_graph_classifier"), "plan_final_decision": refresh_plan.get("final_decision"), "package_final_decision": refresh_package.get("final_decision"), "package_id": refresh_package.get("package_id"), "package_sha256": refresh_package.get("package_sha256"), "execution_precondition_fingerprint": refresh_package.get("execution_precondition_fingerprint"), "live_ready_package_available": True, "controlled_artifact_refresh_execute_available": True, "controlled_artifact_execute_available": False, "iptables_restore_invocation_allowed": True, "mutation_performed": False, "db_mutation_performed": False, "firewall_apply_performed": False, "conntrack_flush_performed": False, "docker_restart_performed": False, "systemd_restart_performed": False, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no", "blockers": [], "final_decision": "READY_LIVE_READY_CONTROLLED_ARTIFACT_REFRESH_PACKAGE"}
        blockers.append("controlled_refresh_exact_stale_graph_not_ready")
        blockers.extend(str(b) for b in refresh_plan.get("blockers", []) if isinstance(refresh_plan.get("blockers"), list))
    if not binding_ready:
        blockers.append("verified_filter_hook_binding_not_ready")
    blockers.extend(str(b) for b in binding.get("blockers", []) if isinstance(binding.get("blockers"), list))
    if backend_target.get("backend_public_exposure"):
        blockers.append("forbidden_public_runtime_exposure")
    plan = build_plan(lanes=lanes, customers=customers, backend_target=backend_target, iptables_save_text=iptables_save_text, ip6tables_save_text=ip6tables_save_text, phase_status_text=phase_status_text, expected_version=expected_version)
    if plan.get("final_decision") != PACKAGE_READY:
        blockers.append("live_plan_final_decision_blocked")
    blockers.extend(str(b) for b in plan.get("blockers", []) if isinstance(plan.get("blockers"), list))
    package = build_package_from_plan(plan)
    verify_plan = second_plan or build_plan(lanes=lanes, customers=customers, backend_target=backend_target, iptables_save_text=iptables_save_text, ip6tables_save_text=ip6tables_save_text, phase_status_text=phase_status_text, expected_version=expected_version)
    classification = plan.get("artifact_classification") if isinstance(plan.get("artifact_classification"), dict) else {}
    unknown = classification.get("unknown_mpf", []) if isinstance(classification.get("unknown_mpf", []), list) else []
    if unknown:
        blockers.append("unknown_mpf_artifacts_present")
    package["production_execution_available"] = False
    package["controlled_artifact_execute_available"] = False
    package["iptables_restore_invocation_allowed"] = False

    # The live-ready builder adds review/execution-availability metadata after
    # the core package builder creates the package. Keep that metadata in the
    # canonical package hash, and use the same core helper as executor preflight.
    package["live_ready_package_available"] = False
    package["package_sha256"] = _canonical_sha(_package_content_for_hash(package))
    verify = verify_package(package, live_plan=verify_plan)
    if verify.get("final_decision") != VERIFY_READY and "package_verification_drift_or_blocked" not in blockers:
        blockers.append("package_verification_drift_or_blocked")
    blockers.extend(str(b) for b in verify.get("blockers", []) if isinstance(verify.get("blockers"), list))

    if blockers:
        final = BLOCKED
        live_ready = False
    else:
        final = READY
        live_ready = True
    package["live_ready_package_available"] = live_ready
    package["package_sha256"] = _canonical_sha(_package_content_for_hash(package))
    verify = verify_package(package, live_plan=verify_plan)
    package_verified_against_live_plan = verify.get("final_decision") == VERIFY_READY
    backup_requirements_ready = bool((package.get("backup_requirements") or {}).get("required")) if isinstance(package.get("backup_requirements"), dict) else False
    rollback_plan_ready = isinstance(package.get("rollback_plan"), dict) and bool((package.get("rollback_plan") or {}).get("manual_review_required"))
    lock_requirements_ready = bool((package.get("lock_requirements") or {}).get("exclusive_lock_required")) if isinstance(package.get("lock_requirements"), dict) else False
    operator_confirmations_required = package.get("operator_confirmations", []) if isinstance(package.get("operator_confirmations"), list) else []
    package_generated = package.get("component") == "phase11_controlled_artifact_reapply_package"
    files_written: dict[str, str] = {}
    if output_dir:
        out = Path(output_dir)
        if out.exists() and (not out.is_dir() or out.is_symlink()):
            return build_fail_closed_live_ready_reapply_package_report(expected_version, ["unsafe_output_dir"], binding=binding)
        out.mkdir(parents=True, exist_ok=True)
        human = "Phase 11 live-ready controlled artifact reapply package review only. No firewall execution.\n"
        machine = {"classification": classification, "payload_sha256": plan.get("payload_sha256")}
        artifacts = {
            "controlled-artifact-reapply-plan.json": plan,
            "controlled-artifact-reapply-package.json": package,
            "controlled-artifact-reapply-verify.json": verify,
            "machine-diff.json": machine,
            "rollback-plan.json": package.get("rollback_plan", {}),
        }
        for name, data in artifacts.items():
            files_written[name] = _atomic_write_json(out / name, data)
        files_written["human-diff.txt"] = _atomic_write_text(out / "human-diff.txt", human)
        _atomic_write_json(out / "manifest.sha256.json", files_written)
    return {
        "component": "phase11_live_ready_reapply_package",
        "repository_version": __version__,
        "expected_version": expected_version,
        "binding_final_decision": binding.get("final_decision"),
        "plan_final_decision": plan.get("final_decision"),
        "package_final_decision": package.get("final_decision"),
        "verify_final_decision": verify.get("final_decision"),
        "package_id": package.get("package_id"),
        "package_sha256": package.get("package_sha256"),
        "execution_precondition_fingerprint": package.get("execution_precondition_fingerprint"),
        "unknown_mpf_artifacts": unknown,
        "forbidden_public_runtime_exposure": bool(backend_target.get("backend_public_exposure")),
        "live_ready_package_available": live_ready,
        "package_verified_against_live_plan": package_verified_against_live_plan,
        "package_generated": package_generated,
        "backup_requirements_ready": backup_requirements_ready,
        "rollback_plan_ready": rollback_plan_ready,
        "lock_requirements_ready": lock_requirements_ready,
        "operator_confirmations_required": operator_confirmations_required,
        "controlled_artifact_reapply_required": plan.get("final_decision") == PACKAGE_READY,
        "output_dir": str(output_dir) if output_dir else None,
        "files_written": files_written,
        "production_execution_available": False,
        "controlled_artifact_execute_available": False,
        "iptables_restore_invocation_allowed": False,
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
        "blockers": sorted(set(blockers)) if final == BLOCKED else [],
        "final_decision": final,
    }


def run_live_ready_reapply_package_report(config_path: Path = DEFAULT_CONFIG_PATH, *, packet_path_evidence_dir: Path | str | None, output_dir: Path | str | None = None, expected_version: str = __version__) -> dict[str, Any]:
    lanes, customers, blockers = _load_planner_input(config_path)
    if blockers:
        return build_fail_closed_live_ready_reapply_package_report(expected_version, blockers)
    ipt = package_service._cmd(["iptables-save"])
    ip6 = package_service._cmd(["ip6tables-save"])
    phase_text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8") if Path("docs/PHASE_STATUS.md").exists() else ""
    snapshot_blockers = [*package_service._snapshot_structure_blockers(ipt, family="iptables"), *package_service._snapshot_structure_blockers(ip6, family="ip6tables")]
    report = build_live_ready_reapply_package_report(packet_path_evidence_dir=packet_path_evidence_dir, lanes=lanes, customers=customers, iptables_save_text=ipt.stdout, ip6tables_save_text=ip6.stdout, phase_status_text=phase_text, expected_version=expected_version, output_dir=output_dir)
    if snapshot_blockers and report.get("final_decision") == READY:
        report["blockers"] = sorted(set([*report.get("blockers", []), *snapshot_blockers]))
        report["final_decision"] = BLOCKED
        report["live_ready_package_available"] = False
    return report
