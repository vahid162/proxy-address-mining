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
REVIEWED_BINDING_SEMANTIC_FIELDS = (
    "controlled_artifact_graph_binding_mode",
    "filter_packet_path",
)

PACKAGE_PLACEHOLDER_BACKEND_METADATA = {
    "network_id": {"verified_packet_path_bundle"},
    "endpoint_id": {"verified_packet_path_endpoint"},
    "compose_project": {None},
    "tcp_connect_ok": {None},
}
INFORMATIONAL_BACKEND_METADATA_FIELDS = tuple(PACKAGE_PLACEHOLDER_BACKEND_METADATA)
HARD_BACKEND_BINDING_IDENTITY_FIELDS = (
    "target_host",
    "resolved_ipv4",
    "target_port",
    "btc_backend_port",
    "container_name",
    "running",
    "health_status",
    "backend_public_exposure",
    "listener_public",
    "publish_public",
    "controlled_artifact_graph_binding_mode",
    "filter_packet_path",
)


def _is_ignored_package_placeholder(field: str, package_value: object, runtime_value: object) -> bool:
    placeholders = PACKAGE_PLACEHOLDER_BACKEND_METADATA.get(field)
    if placeholders is None or package_value not in placeholders:
        return False
    if field == "tcp_connect_ok":
        return package_value is None and runtime_value is True
    return True


def _fail_closed_bound_live_plan(expected_version: str, blockers: list[str], *, diagnostics: dict[str, object] | None = None) -> dict[str, object]:
    out = {
        "component": "phase11_controlled_artifact_reapply_plan",
        "repository_version": __version__,
        "expected_version": expected_version,
        "final_decision": "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE",
        "blockers": sorted(set(["live_ready_binding_revalidation_failed", *blockers])),
        "mutation_performed": False,
    }
    if diagnostics:
        out.update(diagnostics)
    return out


def _package_bound_backend_target(package: dict[str, object]) -> dict[str, object]:
    plan = package.get("plan") if isinstance(package.get("plan"), dict) else {}
    target = plan.get("backend_target") if isinstance(plan.get("backend_target"), dict) else {}
    return dict(target)


def _canonical_backend_binding_identity(target: dict[str, object]) -> dict[str, object]:
    listener = target.get("listener_classification") if isinstance(target.get("listener_classification"), dict) else {}
    publish = target.get("publish_classification") if isinstance(target.get("publish_classification"), dict) else {}
    reachability = target.get("reachability") if isinstance(target.get("reachability"), dict) else {}
    identity = {
        "target_host": target.get("target_host") or target.get("resolved_ipv4"),
        "resolved_ipv4": target.get("resolved_ipv4") or target.get("target_host"),
        "target_port": target.get("target_port"),
        "network_id": target.get("network_id"),
        "endpoint_id": target.get("endpoint_id"),
        "container_name": target.get("container_name"),
        "compose_project": target.get("compose_project"),
        "running": target.get("running"),
        "health_status": target.get("health_status"),
        "backend_public_exposure": bool(target.get("backend_public_exposure")),
        "listener_public": bool(listener.get("public")),
        "publish_public": bool(publish.get("public")),
        "controlled_artifact_graph_binding_mode": target.get("controlled_artifact_graph_binding_mode"),
        "filter_packet_path": target.get("filter_packet_path"),
        "btc_backend_port": target.get("target_port"),
        "tcp_connect_ok": reachability.get("tcp_connect_ok"),
    }
    package_cid = target.get("container_id")
    if package_cid is not None:
        identity["container_id"] = package_cid
    return identity


def _runtime_target_with_reviewed_binding_semantics(package_target: dict[str, object], runtime_target: dict[str, object]) -> dict[str, object]:
    """Add package-reviewed packet-path semantics to runtime comparison input.

    The Docker-backed runtime backend resolver proves the live container/network/IP/health/public-exposure
    identity, but it does not own the reviewed packet-path binding fields.  Those fields are already
    validated against the live-ready package before this comparison.  Carrying them into the runtime side
    here keeps the field-by-field evidence explicit without treating resolver shape differences as drift.
    """

    out = dict(runtime_target)
    for field in REVIEWED_BINDING_SEMANTIC_FIELDS:
        if out.get(field) is None and package_target.get(field) is not None:
            out[field] = package_target.get(field)
    return out


def _backend_binding_identity_comparison(package_target: dict[str, object], runtime_target: dict[str, object]) -> dict[str, object]:
    runtime_with_reviewed_semantics = _runtime_target_with_reviewed_binding_semantics(package_target, runtime_target)
    package_identity = _canonical_backend_binding_identity(package_target)
    runtime_identity = _canonical_backend_binding_identity(runtime_with_reviewed_semantics)
    if "container_id" in package_identity and "container_id" not in runtime_identity:
        package_identity.pop("container_id", None)
    if "container_id" in runtime_identity and "container_id" not in package_identity:
        runtime_identity.pop("container_id", None)
    fields = sorted(set(package_identity) | set(runtime_identity))
    compared = {}
    hard_mismatched: list[str] = []
    informational_mismatched: list[str] = []
    ignored_placeholder_fields: list[str] = []
    for field in fields:
        package_value = package_identity.get(field)
        runtime_value = runtime_identity.get(field)
        raw_match = package_value == runtime_value
        ignored_placeholder = False if raw_match else _is_ignored_package_placeholder(field, package_value, runtime_value)
        hard_identity_field = field in HARD_BACKEND_BINDING_IDENTITY_FIELDS
        canonical_match = raw_match or ignored_placeholder or not hard_identity_field
        compared[field] = {
            "package": package_value,
            "runtime": runtime_value,
            "match": raw_match,
            "canonical_match": canonical_match,
            "hard_identity_field": hard_identity_field,
            "informational_field": field in INFORMATIONAL_BACKEND_METADATA_FIELDS,
            "ignored_package_placeholder": ignored_placeholder,
        }
        if ignored_placeholder:
            ignored_placeholder_fields.append(field)
        elif not raw_match and hard_identity_field:
            hard_mismatched.append(field)
        elif not raw_match:
            informational_mismatched.append(field)
    mismatched = sorted(set(hard_mismatched + informational_mismatched))
    return {
        "canonical_backend_binding_identity_match": not hard_mismatched,
        "compared_stable_fields": compared,
        "mismatched_fields": mismatched,
        "hard_identity_mismatched_fields": sorted(hard_mismatched),
        "informational_mismatched_fields": sorted(informational_mismatched),
        "ignored_package_placeholder_fields": sorted(ignored_placeholder_fields),
        "hard_identity_fields": list(HARD_BACKEND_BINDING_IDENTITY_FIELDS),
        "informational_metadata_fields": list(INFORMATIONAL_BACKEND_METADATA_FIELDS),
        "reviewed_binding_semantic_fields": list(REVIEWED_BINDING_SEMANTIC_FIELDS),
        "package_backend_target_fingerprint": package_target.get("target_fingerprint"),
        "live_backend_target_fingerprint": runtime_target.get("target_fingerprint"),
    }


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
    binding_comparison = _backend_binding_identity_comparison(bound_target, current_backend)
    if not current_backend.get("target_fingerprint"):
        blockers.append("backend_target_fingerprint_missing")
    if binding_comparison["canonical_backend_binding_identity_match"] is not True:
        blockers.append("backend_target_binding_identity_drift")

    iptables_result = _cmd(["iptables-save"])
    ip6tables_result = _cmd(["ip6tables-save"])
    blockers.extend(_snapshot_structure_blockers(iptables_result, family="iptables"))
    blockers.extend(_snapshot_structure_blockers(ip6tables_result, family="ip6tables"))

    diagnostics = {
        "package_backend_target_fingerprint": bound_target.get("target_fingerprint"),
        "live_backend_target_fingerprint": current_backend.get("target_fingerprint"),
        "package_execution_precondition_fingerprint": package.get("execution_precondition_fingerprint"),
        "drift_comparison": binding_comparison,
        "canonical_backend_binding_identity_match": binding_comparison["canonical_backend_binding_identity_match"],
    }
    if "backend_target_binding_identity_drift" in blockers:
        diagnostics["root_cause_blocker"] = "backend_target_binding_identity_drift"

    if blockers or not loaded.ok:
        return _fail_closed_bound_live_plan(expected_version, blockers, diagnostics=diagnostics)

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
    plan.update(diagnostics)
    plan["live_execution_precondition_fingerprint"] = plan.get("execution_precondition_fingerprint")
    plan["live_ready_binding_revalidated"] = True
    plan["live_ready_binding_revalidation_hash"] = _canonical_sha(
        {
            "package_id": package.get("package_id"),
            "binding_mode": bound_target.get("controlled_artifact_graph_binding_mode"),
            "backend_target_fingerprint": bound_target.get("target_fingerprint"),
            "current_backend_target_fingerprint": current_backend.get("target_fingerprint"),
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
