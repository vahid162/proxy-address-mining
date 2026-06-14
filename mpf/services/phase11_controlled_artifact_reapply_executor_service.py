from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.services.phase11_controlled_artifact_reapply_audit_service import ControlledArtifactReapplyAuditRepo
from mpf.services.phase11_controlled_artifact_reapply_core import (
    FileBackupAdapter,
    FlockHostLock,
    ProductionIptablesRestoreRunner,
    _canonical_sha,
    build_plan,
    execute_package,
)
from mpf.repositories import firewall_planner_read_repo
from mpf.services.phase11_controlled_artifact_reapply_package_service import (
    _cmd,
    _phase_text,
    _snapshot_structure_blockers,
)
from mpf.services.phase11_controlled_backend_target_service import build_controlled_backend_target_report


BOUND_PACKET_PATH_MODE = "verified_docker_user_forward_post_dnat"


def _fail_closed_bound_live_plan(expected_version: str, blockers: list[str]) -> dict[str, object]:
    return {
        "component": "phase11_controlled_artifact_reapply_plan",
        "repository_version": __version__,
        "expected_version": expected_version,
        "final_decision": "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE",
        "blockers": sorted(set(["live_ready_binding_revalidation_failed", *blockers])),
        "mutation_performed": False,
    }


def _package_bound_backend_target(package: dict[str, object]) -> dict[str, object]:
    plan = package.get("plan") if isinstance(package.get("plan"), dict) else {}
    target = plan.get("backend_target") if isinstance(plan.get("backend_target"), dict) else {}
    return dict(target)


def build_execution_time_live_ready_reapply_plan(
    *,
    package: dict[str, object],
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_version: str = __version__,
) -> dict[str, object]:
    """Rebuild an execute-time plan with the live-ready bound packet-path semantics.

    The plain controlled artifact plan intentionally fails closed without verified
    packet-path binding.  Live-ready execution must therefore rebuild the same
    bound artifact graph that package review used, while still rereading current
    PostgreSQL planner input, phase status, iptables/ip6tables snapshots, and the
    runtime backend target before any iptables-restore test/apply can occur.
    """

    blockers: list[str] = []
    if expected_version != __version__ or package.get("repository_version") != __version__:
        blockers.append("repository_version_mismatch")
    if package.get("live_ready_package_available") is not True:
        blockers.append("live_ready_package_required")

    bound_target = _package_bound_backend_target(package)
    if bound_target.get("controlled_artifact_graph_binding_mode") != BOUND_PACKET_PATH_MODE:
        blockers.append("packet_path_binding_mode_mismatch")
    if bound_target.get("filter_packet_path") != "docker_user_forward_verified":
        blockers.append("packet_path_binding_not_verified")
    if bound_target.get("backend_public_exposure"):
        blockers.append("forbidden_public_runtime_exposure")
    if bound_target.get("target_fingerprint") != package.get("backend_target_fingerprint"):
        blockers.append("package_backend_target_fingerprint_mismatch")

    cfg = load_config(config_path)
    loaded = firewall_planner_read_repo.load_firewall_planner_input(cfg)
    if not loaded.ok:
        blockers.append("postgresql_planner_input_read_failed")

    current_backend = build_controlled_backend_target_report(expected_version=expected_version)
    if current_backend.get("backend_public_exposure"):
        blockers.append("forbidden_public_runtime_exposure")
    if current_backend.get("health_status") != "healthy" or current_backend.get("running") is not True:
        blockers.append("backend_target_health_not_verified")
    current_ip = current_backend.get("resolved_ipv4") or current_backend.get("target_host")
    bound_ip = bound_target.get("resolved_ipv4") or bound_target.get("target_host")
    if current_ip != bound_ip or current_backend.get("target_port") != bound_target.get("target_port"):
        blockers.append("backend_target_runtime_drift")

    iptables_result = _cmd(["iptables-save"])
    ip6tables_result = _cmd(["ip6tables-save"])
    blockers.extend(_snapshot_structure_blockers(iptables_result, family="iptables"))
    blockers.extend(_snapshot_structure_blockers(ip6tables_result, family="ip6tables"))

    if blockers or not loaded.ok:
        return _fail_closed_bound_live_plan(expected_version, blockers)

    plan = build_plan(
        lanes=loaded.lanes,
        customers=loaded.customers,
        backend_target=bound_target,
        iptables_save_text=iptables_result.stdout,
        ip6tables_save_text=ip6tables_result.stdout,
        phase_status_text=_phase_text(),
        expected_version=expected_version,
    )
    plan["iptables_save_text"] = iptables_result.stdout
    plan["ip6tables_save_text"] = ip6tables_result.stdout
    plan["firewall_snapshot_commands"] = {"iptables-save": iptables_result.__dict__, "ip6tables-save": ip6tables_result.__dict__}
    plan["live_ready_binding_revalidated"] = True
    plan["live_ready_binding_revalidation_hash"] = _canonical_sha(
        {
            "package_id": package.get("package_id"),
            "binding_mode": bound_target.get("controlled_artifact_graph_binding_mode"),
            "backend_target_fingerprint": bound_target.get("target_fingerprint"),
            "current_backend_resolved_ipv4": current_ip,
            "current_backend_target_port": current_backend.get("target_port"),
            "iptables_save_sha256": (plan.get("snapshot_hashes") or {}).get("iptables_save_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None,
            "ip6tables_save_sha256": (plan.get("snapshot_hashes") or {}).get("ip6tables_save_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None,
        }
    )
    return plan


def execute_controlled_artifact_reapply_package(
    *,
    package: dict[str, object],
    package_sha256: str,
    package_id: str,
    operator: str,
    reason: str,
    execute: bool = False,
    yes: bool = False,
    expected_version: str = __version__,
    config_path: Path = DEFAULT_CONFIG_PATH,
    **kwargs,
) -> dict[str, object]:
    cfg = load_config(config_path)
    return execute_package(
        package=package,
        package_sha256=package_sha256,
        package_id=package_id,
        operator=operator,
        reason=reason,
        execute=execute,
        yes=yes,
        expected_version=expected_version,
        live_plan_builder=lambda: build_execution_time_live_ready_reapply_plan(
            package=package,
            config_path=config_path,
            expected_version=expected_version,
        ),
        runner=ProductionIptablesRestoreRunner(),
        backup=FileBackupAdapter(),
        metadata_repo=ControlledArtifactReapplyAuditRepo(cfg),
        lock=FlockHostLock(),
        **kwargs,
    )
