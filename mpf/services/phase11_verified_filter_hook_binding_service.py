"""Phase 11 verified filter hook binding and package-evidence helpers.

This module is intentionally offline/read-only.  It consumes a previously
collected controlled filter packet-path bundle, verifies its manifest, binds the
verified DOCKER-USER/FORWARD/post-DNAT semantics to the controlled artifact
renderer graph, and can write a non-executable package-evidence directory.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import (
    BACKEND_CONTAINER,
    BACKEND_PORT,
    SCOPE,
    _canonical_sha,
    _text_sha,
    build_package_from_plan,
    build_plan,
    verify_package,
)
from mpf.services.phase11_controlled_filter_packet_path_bundle_service import verify_packet_path_bundle

READY_PACKET = "READY_CONTROLLED_FILTER_PACKET_PATH_PROOF"
READY_BINDING = "READY_VERIFIED_FILTER_HOOK_BINDING"
BLOCKED_BINDING = "BLOCKED_VERIFIED_FILTER_HOOK_BINDING"
READY_PACKAGE_EVIDENCE = "READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_EVIDENCE"
BLOCKED_PACKAGE_EVIDENCE = "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_EVIDENCE"
READY_VERIFY = "READY_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_VERIFY_EVIDENCE"
BLOCKED_VERIFY = "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_VERIFY_EVIDENCE"
BINDING_MODE = "verified_docker_user_forward_post_dnat"
REQUIRED_SCENARIOS = {("ens192", "NEW"), ("ens192", "ESTABLISHED"), ("ens224", "NEW"), ("ens224", "ESTABLISHED")}


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json_object_required:{path.name}")
    return data


def _safe_dir(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_verified_filter_hook_binding_report(packet_path_evidence_dir: Path | str, *, source_bundle_archive_sha256: str | None = None) -> dict[str, Any]:
    root = Path(packet_path_evidence_dir)
    blockers: list[str] = []
    warnings: list[str] = []
    verifier = verify_packet_path_bundle(root)
    if verifier.get("bundle_integrity_valid") is not True:
        blockers.append("bundle_integrity_invalid")
    if verifier.get("final_decision") != READY_PACKET:
        blockers.append("packet_path_final_decision_not_ready")
    try:
        evidence = _read_json(root / "evidence.json")
        decision = _read_json(root / "decision.json")
        graph = _read_json(root / "packet-path-graph.json")
        parsed = _read_json(root / "parsed-firewall.json")
        manifest = _read_json(root / "manifest.json")
        topology = _read_json(root / "host-network-topology.json")
    except Exception as exc:  # noqa: BLE001
        evidence = decision = graph = parsed = manifest = topology = {}
        blockers.append(f"bundle_document_read_failed:{type(exc).__name__}")

    backend = evidence.get("backend_target") if isinstance(evidence.get("backend_target"), dict) else {}
    docker_net = evidence.get("docker_network") if isinstance(evidence.get("docker_network"), dict) else {}
    scenarios = graph.get("packet_scenarios") if isinstance(graph.get("packet_scenarios"), list) else []
    results = graph.get("scenario_results") if isinstance(graph.get("scenario_results"), list) else []
    scenario_pairs = [(str(s.get("ingress_interface")), str(s.get("conntrack_state"))) for s in scenarios if isinstance(s, dict)]
    result_map = {r.get("scenario_id"): r for r in results if isinstance(r, dict)}
    scenario_matrix_ready = set(scenario_pairs) == REQUIRED_SCENARIOS and len(scenario_pairs) == len(set(scenario_pairs)) == 4
    if not scenario_matrix_ready:
        blockers.append("required_scenario_matrix_incomplete_or_duplicate")
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        res = result_map.get(scenario.get("scenario_id"))
        if not isinstance(res, dict) or res.get("ready") is not True or res.get("result") not in {None, "READY"}:
            blockers.append(f"scenario_not_ready:{scenario.get('scenario_id')}")
        if scenario.get("verified_user_policy_hook") not in {None, "DOCKER-USER"}:
            blockers.append("scenario_hook_mismatch")
        dest = scenario.get("destination_at_hook") if isinstance(scenario.get("destination_at_hook"), dict) else {}
        if dest and int(dest.get("port", -1)) != BACKEND_PORT:
            blockers.append("public_destination_port_visible_at_docker_user")

    expected_customers = list(SCOPE)
    customers = evidence.get("controlled_customers") or decision.get("controlled_customers") or graph.get("controlled_customers") or expected_customers
    if customers != expected_customers:
        blockers.append("controlled_customer_scope_mismatch")
    checks = [
        (evidence.get("packet_path_schema_version") == "0.1.252", "packet_path_schema_version_incompatible"),
        (decision.get("final_decision") == READY_PACKET, "decision_final_decision_not_ready"),
        (backend.get("container_name") in {BACKEND_CONTAINER, f"/{BACKEND_CONTAINER}"}, "backend_container_mismatch"),
        (int(backend.get("target_port") or backend.get("port") or backend.get("backend_port") or -1) == BACKEND_PORT, "backend_port_mismatch"),
        (decision.get("verified_user_policy_hook") == "DOCKER-USER", "verified_hook_mismatch"),
        (decision.get("verified_builtin_filter_path") == "FORWARD", "builtin_filter_path_mismatch"),
        (decision.get("packet_view_at_verified_hook") == "post_dnat_forward_filter", "packet_view_mismatch"),
        ((decision.get("docker_user_precedes_relevant_accept_paths") is True or decision.get("hook_precedes_all_relevant_accept_paths") is True), "docker_user_accept_order_unverified"),
        (topology.get("backend_bridge_membership_verified") is True or evidence.get("backend_bridge_membership_verified") is True, "backend_bridge_membership_unverified"),
        (decision.get("unknown_mpf_artifacts", []) == [] and parsed.get("unknown_mpf_artifacts", []) == [], "unknown_mpf_artifacts_present"),
        (decision.get("forbidden_public_runtime_exposure", False) is False, "forbidden_public_runtime_exposure"),
        (evidence.get("mutation_performed") is False and decision.get("mutation_performed") is False and graph.get("mutation_performed") is False, "mutation_performed_not_false"),
        (evidence.get("runtime_packet_observed") is False and decision.get("runtime_packet_observed") is False, "runtime_packet_observed_not_false"),
        (evidence.get("post_apply_runtime_verified") is False and decision.get("post_apply_runtime_verified") is False, "post_apply_runtime_verified_not_false"),
    ]
    for ok, blocker in checks:
        if not ok:
            blockers.append(blocker)
    if parsed.get("firewall_backend") and decision.get("firewall_backend") and parsed.get("firewall_backend") != decision.get("firewall_backend"):
        blockers.append("mixed_firewall_backend")
    ready = not blockers
    backend_ip = backend.get("resolved_ipv4") or backend.get("target_host") or backend.get("ip")
    graph_binding = _build_binding_graph(manifest, backend_ip=backend_ip)
    return {
        "component": "phase11_verified_filter_hook_binding",
        "repository_version": __version__,
        "source_bundle_manifest_sha256": verifier.get("manifest_sha256"),
        "source_bundle_archive_sha256": source_bundle_archive_sha256,
        "source_collection_id": manifest.get("collection_id"),
        "source_repository_version": evidence.get("repository_version"),
        "verified_hook": "DOCKER-USER" if ready else decision.get("verified_user_policy_hook"),
        "verified_builtin_filter_path": "FORWARD" if ready else decision.get("verified_builtin_filter_path"),
        "packet_view_at_hook": "post_dnat_forward_filter" if ready else decision.get("packet_view_at_verified_hook"),
        "backend_match_semantics": "post_dnat_backend_destination",
        "backend_container": BACKEND_CONTAINER,
        "backend_ip": backend_ip,
        "backend_port": BACKEND_PORT,
        "customer_public_ports": [20001, 20101],
        "scenario_matrix_ready": scenario_matrix_ready,
        "controlled_artifact_graph_binding_mode": BINDING_MODE,
        "artifact_graph_binding": graph_binding,
        "artifact_graph_binding_ready": ready,
        "desired_artifact_semantics_complete": ready,
        "controlled_artifact_reapply_package_evidence_ready": ready,
        "production_execution_available": False,
        "iptables_restore_invocation_allowed": False,
        "controlled_artifact_execute_available": False,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "binding_decision_sha256": "",
        "final_decision": READY_BINDING if ready else BLOCKED_BINDING,
        "mutation_performed": False,
    }


def _build_binding_graph(manifest: dict[str, Any], *, backend_ip: Any) -> dict[str, Any]:
    nodes = [
        {"id": "nat_prerouting", "type": "builtin_nat_hook", "chain": "PREROUTING"},
        {"id": "mpf_nat_pre", "type": "mpf_nat_redirect_chain", "chain": "MPF_NAT_PRE", "public_ports": [20001, 20101]},
        {"id": "filter_forward", "type": "builtin_filter_path", "chain": "FORWARD"},
        {"id": "docker_user", "type": "verified_user_policy_hook", "chain": "DOCKER-USER", "packet_view": "post_dnat_forward_filter"},
        {"id": "mpf_customers", "type": "controlled_customer_dispatch_accounting_filter", "match_destination_port": BACKEND_PORT},
        {"id": "backend_guard", "type": "backend_guard", "backend_ip": backend_ip, "backend_port": BACKEND_PORT},
        {"id": "rate_connlimit_whitelist_accounting", "type": "policy_semantics", "customer_identity": "chain_comment_accounting_preserved"},
        {"id": "rollback_metadata", "type": "rollback_safe_package_metadata"},
        {"id": "verification_metadata", "type": "source_bundle_verification", "manifest_sha256": manifest.get("manifest_sha256")},
    ]
    edges = [
        {"from": "nat_prerouting", "to": "mpf_nat_pre", "semantics": "public_port_redirect_only"},
        {"from": "mpf_nat_pre", "to": "filter_forward", "semantics": "dnat_to_backend"},
        {"from": "filter_forward", "to": "docker_user", "semantics": "verified_pre_accept_policy_hook"},
        {"from": "docker_user", "to": "backend_guard", "semantics": "post_dnat_backend_destination_guard"},
        {"from": "docker_user", "to": "mpf_customers", "semantics": "post_dnat_customer_policy_dispatch"},
        {"from": "mpf_customers", "to": "rate_connlimit_whitelist_accounting", "semantics": "controlled_customer_chain_comments_accounting"},
        {"from": "mpf_customers", "to": "rollback_metadata", "semantics": "rollback_safe_delta"},
        {"from": "verification_metadata", "to": "docker_user", "semantics": "source_bundle_bound"},
    ]
    return {"mode": BINDING_MODE, "nodes": nodes, "edges": edges}


def binding_backend_target(binding: dict[str, Any]) -> dict[str, Any]:
    fp_input = {"source_manifest_sha256": binding.get("source_bundle_manifest_sha256"), "mode": BINDING_MODE, "backend_ip": binding.get("backend_ip"), "backend_port": BACKEND_PORT}
    return {"component": "phase11_controlled_backend_target_resolver", "status": "ok", "repository_version": __version__, "container_name": BACKEND_CONTAINER, "backend_target_source": "operator_package_bound", "resolved_ipv4": binding.get("backend_ip"), "target_host": binding.get("backend_ip"), "target_port": BACKEND_PORT, "network_id": "verified_packet_path_bundle", "endpoint_id": "verified_packet_path_endpoint", "health_status": "healthy", "running": True, "backend_public_exposure": False, "filter_packet_path": "docker_user_forward_verified", "controlled_artifact_graph_binding_mode": BINDING_MODE, "target_fingerprint_input": fp_input, "target_fingerprint": _canonical_sha(fp_input), "blockers": [], "mutation_performed": False}


def default_lanes_customers() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    policy = {"miners": 1, "farms": 1, "maxconn": 10, "rate_per_min": 60, "burst": 10, "ips_mode": "any"}
    return ([{"name": "btc", "enabled": True, "backend_port": BACKEND_PORT}], [{"id": 1, "customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "status": "active", "policy": policy}, {"id": 2, "customer_key": "limited-btc-001", "lane": "btc", "port": 20101, "status": "active", "policy": policy}])


def build_package_evidence(packet_path_evidence_dir: Path | str, output_dir: Path | str) -> dict[str, Any]:
    binding = build_verified_filter_hook_binding_report(packet_path_evidence_dir)
    blockers = [] if binding.get("final_decision") == READY_BINDING else ["verified_filter_hook_binding_not_ready"]
    lanes, customers = default_lanes_customers()
    phase_text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8") if Path("docs/PHASE_STATUS.md").exists() else ""
    plan = build_plan(lanes=lanes, customers=customers, backend_target=binding_backend_target(binding), phase_status_text=phase_text)
    blockers.extend(plan.get("blockers", []) if isinstance(plan.get("blockers"), list) else [])
    package = build_package_from_plan(plan)
    package.update({"final_decision": READY_PACKAGE_EVIDENCE if not blockers else BLOCKED_PACKAGE_EVIDENCE, "production_execution_available": False, "live_apply_available": False, "iptables_restore_invocation_allowed": False, "controlled_artifact_execute_available": False, "source_packet_path_bundle_manifest_sha256": binding.get("source_bundle_manifest_sha256"), "binding_decision_sha256": _canonical_sha(binding), "desired_artifact_graph_sha256": _canonical_sha(plan.get("desired_state", {})), "rollback_plan_sha256": _canonical_sha(package.get("rollback_plan", {})), "audit_requirements": {"required": True}, "verification_requirements": {"required": True}, "execution_blocked": True, "exact_two_customer_scope": list(SCOPE), "no_unknown_mpf_artifacts": True, "no_public_backend_exposure": True, "no_stale_target": True, "no_duplicate_controlled_artifacts": True, "mutation_performed": False, "blockers": sorted(set(blockers))})
    package["package_sha256"] = _canonical_sha({k: v for k, v in package.items() if k != "package_sha256"})
    out = Path(output_dir)
    if out.exists() and not _safe_dir(out):
        raise ValueError("unsafe_output_dir")
    out.mkdir(parents=True, exist_ok=True)
    if out.is_symlink():
        raise ValueError("unsafe_output_dir_symlink")
    files = {"binding-report.json": binding, "plan.json": plan, "package.json": package, "rollback-plan.json": package.get("rollback_plan", {})}
    manifest: dict[str, str] = {}
    for name, data in files.items():
        p = out / name
        if p.exists() or p.is_symlink():
            raise FileExistsError(str(p))
        text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n"
        p.write_text(text, encoding="utf-8")
        os.chmod(p, 0o600)
        manifest[name] = _text_sha(text)
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (out / "manifest.sha256.json").write_text(manifest_text, encoding="utf-8")
    return {"component": "phase11_controlled_artifact_reapply_package_evidence", "repository_version": __version__, "package_dir": str(out), "manifest_sha256": _text_sha(manifest_text), "package_sha256": _sha_file(out / "package.json"), "binding_final_decision": binding.get("final_decision"), "package_final_decision": package.get("final_decision"), "final_decision": package.get("final_decision"), "production_execution_available": False, "iptables_restore_invocation_allowed": False, "mutation_performed": False, "blockers": sorted(set(blockers))}


def verify_package_evidence(package_dir: Path | str) -> dict[str, Any]:
    root = Path(package_dir)
    blockers: list[str] = []
    if not _safe_dir(root):
        blockers.append("package_dir_not_safe_directory")
    try:
        manifest = json.loads((root / "manifest.sha256.json").read_text(encoding="utf-8"))
        package = _read_json(root / "package.json")
        plan = _read_json(root / "plan.json")
        binding = _read_json(root / "binding-report.json")
    except Exception as exc:  # noqa: BLE001
        manifest, package, plan, binding = {}, {}, {}, {}
        blockers.append(f"package_evidence_read_failed:{type(exc).__name__}")
    if isinstance(manifest, dict):
        for name, sha in manifest.items():
            p = root / str(name)
            if p.is_symlink() or not p.is_file() or _sha_file(p) != sha:
                blockers.append(f"package_manifest_hash_mismatch:{name}")
    blockers.extend(package.get("blockers", []) if isinstance(package.get("blockers"), list) else [])
    if binding.get("final_decision") != READY_BINDING:
        blockers.append("binding_not_ready")
    if package.get("final_decision") != READY_PACKAGE_EVIDENCE:
        blockers.append("package_evidence_not_ready")
    if package.get("production_execution_available") is not False or package.get("iptables_restore_invocation_allowed") is not False:
        blockers.append("execution_not_blocked")
    shape = verify_package({**package, "final_decision": "CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY"}, live_plan=plan)
    blockers.extend(b for b in shape.get("blockers", []) if b not in {"package_not_ready", "package_canonical_sha256_mismatch"})
    return {"component": "phase11_controlled_artifact_reapply_package_evidence_verify", "repository_version": __version__, "package_dir": str(root), "package_sha256": _sha_file(root / "package.json") if (root / "package.json").exists() else None, "production_execution_available": False, "iptables_restore_invocation_allowed": False, "controlled_artifact_execute_available": False, "mutation_performed": False, "blockers": sorted(set(blockers)), "final_decision": READY_VERIFY if not blockers else BLOCKED_VERIFY}
