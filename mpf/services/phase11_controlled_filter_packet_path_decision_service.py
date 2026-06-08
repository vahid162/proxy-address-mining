"""Decision service for controlled filter packet-path proof."""
from __future__ import annotations

from typing import Any

from mpf.domain.phase11_controlled_filter_packet_path import BACKEND_PORT, BLOCKED, READY, INVALID, PacketPathDecision
from mpf.services.phase11_controlled_filter_packet_path_graph_service import classify_route, ip_in_subnet


def decide_controlled_filter_packet_path(*, evidence: dict[str, Any], graph: dict[str, Any], parsed_firewall: dict[str, Any], command_results: list[dict[str, Any]]) -> PacketPathDecision:
    invalid: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    for result in command_results:
        if result.get("return_code") != 0:
            invalid.append(f"command_failed:{result.get('command_id')}:{result.get('return_code')}")
        if result.get("timed_out") is True:
            invalid.append(f"command_timeout:{result.get('command_id')}")
        if result.get("output_truncated") is True:
            invalid.append(f"command_output_truncated:{result.get('command_id')}")
        if result.get("mutation_performed") is not False:
            invalid.append(f"mutation_performed:{result.get('command_id')}")
    if evidence.get("mutation_performed") is not False:
        invalid.append("mutation_performed")
    fw4 = parsed_firewall.get("ipv4", {}) if isinstance(parsed_firewall.get("ipv4"), dict) else {}
    fw6 = parsed_firewall.get("ipv6", {}) if isinstance(parsed_firewall.get("ipv6"), dict) else {}
    if fw4.get("errors"):
        invalid.extend(f"malformed_ipv4_ruleset:{e}" for e in fw4.get("errors", []))
    if fw6.get("errors"):
        invalid.extend(f"malformed_ipv6_ruleset:{e}" for e in fw6.get("errors", []))
    if invalid:
        return _decision(INVALID, invalid, warnings=warnings)

    backend = evidence.get("backend_target", {}) if isinstance(evidence.get("backend_target"), dict) else {}
    network = evidence.get("docker_network", {}) if isinstance(evidence.get("docker_network"), dict) else {}
    topology = evidence.get("host_topology", {}) if isinstance(evidence.get("host_topology"), dict) else {}
    backend_ip = str(backend.get("resolved_ipv4") or "")
    subnet = str(network.get("ipv4_subnet") or "")
    host_ips = {str(item.get("local")) for item in topology.get("host_addresses", []) if isinstance(item, dict)}
    target_is_local = backend_ip in host_ips
    target_in_subnet = bool(backend_ip and subnet and ip_in_subnet(backend_ip, subnet))
    route_class = classify_route(topology=topology, backend=backend, network=network)
    ip_forward = str(topology.get("ip_forward", "")) == "1"
    chains = set(fw4.get("docker_chains_present", []))
    rules = fw4.get("rules", []) if isinstance(fw4.get("rules"), list) else []
    unknown_mpf = list(fw4.get("unknown_mpf_artifacts", []))
    ipv6_mpf = bool(fw6.get("ipv6_mpf_or_customer_artifacts_present"))

    if backend.get("status") != "ok":
        blockers.append("backend_target_not_healthy")
    if backend.get("backend_public_exposure") is True:
        blockers.append("backend_public_exposure_detected")
    if target_is_local:
        blockers.append("backend_target_is_host_local")
    if not target_in_subnet:
        blockers.append("backend_target_outside_expected_docker_subnet")
    if route_class != "forwarded":
        blockers.append(f"post_dnat_route_not_forwarded:{route_class}")
    if not ip_forward:
        blockers.append("ipv4_forwarding_disabled")
    if "DOCKER-USER" not in chains:
        blockers.append("docker_user_hook_missing")
    if unknown_mpf:
        blockers.append("unknown_mpf_artifacts_present")
    if ipv6_mpf:
        blockers.append("ipv6_mpf_or_customer_artifact_detected")
    if network.get("unknown_connected_containers"):
        blockers.append("unknown_docker_network_containers_present")
    if backend.get("historical_hardcoded_target_assumed") is True or backend_ip == "172.18.0.3":
        blockers.append("historical_backend_target_forbidden")

    hook_info = _hook_order(rules)
    docker_user_reachable = hook_info["docker_user_reachable"] and route_class == "forwarded"
    if not docker_user_reachable:
        blockers.append("docker_user_not_reachable_on_forward_path")
    if hook_info["ambiguous"]:
        blockers.append("docker_user_hook_duplicated_or_ambiguous")
    if hook_info["bypass"]:
        blockers.append("accept_bypass_before_docker_user")
    if not hook_info["precedes_accept"]:
        blockers.append("docker_user_does_not_precede_accept_paths")

    packet_view = "post_dnat_forward_filter" if route_class == "forwarded" and docker_user_reachable else "unknown"
    visible = {"ip": backend_ip if packet_view != "unknown" else None, "port": BACKEND_PORT if packet_view != "unknown" else None}
    renderer_blockers = [
        "current_controlled_artifact_renderer_uses_INPUT_parent_hook",
        "current_customer_filter_rules_match_public_destination_ports_20001_20101",
        "verified_forward_docker_user_hook_is_post_dnat_and_sees_backend_destination_60010",
        "conntrack_original_destination_match_requires_reviewed_artifact_graph_binding",
    ]
    final = READY if not blockers else BLOCKED
    proposed = graph.get("proposed_review_only_graph") if isinstance(graph, dict) else []
    future_reachable = bool(proposed) or docker_user_reachable
    return PacketPathDecision(
        final_decision=final,
        post_dnat_route_class=route_class,
        verified_builtin_filter_path="FORWARD" if route_class == "forwarded" else None,
        verified_user_policy_hook="DOCKER-USER" if final == READY else None,
        input_path_applicable=route_class == "local_input",
        forward_path_applicable=route_class == "forwarded",
        docker_user_reachable=docker_user_reachable,
        hook_precedes_all_relevant_accept_paths=hook_info["precedes_accept"],
        bypass_path_detected=hook_info["bypass"],
        future_mpf_entry_reachable=future_reachable,
        packet_view_at_verified_hook=packet_view,
        destination_visible_at_verified_hook=visible,
        original_destination_available_via_conntrack=True,
        original_destination_match_required=packet_view == "post_dnat_forward_filter",
        current_customer_port_match_compatible=False,
        current_renderer_binding_compatible=False,
        renderer_binding_blockers=renderer_blockers,
        blockers=sorted(set(blockers)),
        warnings=warnings,
        evidence_hashes=evidence.get("evidence_hashes", {}) if isinstance(evidence.get("evidence_hashes"), dict) else {},
    )


def _decision(final: str, blockers: list[str], *, warnings: list[str]) -> PacketPathDecision:
    return PacketPathDecision(final_decision=final, blockers=sorted(set(blockers)), warnings=sorted(set(warnings)))  # type: ignore[arg-type]


def _hook_order(rules: list[dict[str, Any]]) -> dict[str, bool]:
    forward = [r for r in rules if r.get("table") == "filter" and r.get("chain") == "FORWARD"]
    docker_user_indexes = [int(r.get("rule_index", -1)) for r in forward if r.get("jump_target") == "DOCKER-USER"]
    accept_indexes = [int(r.get("rule_index", -1)) for r in forward if r.get("terminal_verdict") == "ACCEPT" or r.get("jump_target") in {"ACCEPT", "DOCKER", "DOCKER-FORWARD", "DOCKER-CT"}]
    if not docker_user_indexes:
        return {"docker_user_reachable": False, "ambiguous": False, "bypass": False, "precedes_accept": False}
    first_hook = min(docker_user_indexes)
    ambiguous = len(docker_user_indexes) != 1
    first_accept = min(accept_indexes) if accept_indexes else None
    bypass = first_accept is not None and first_accept < first_hook
    precedes = first_accept is None or first_hook < first_accept
    return {"docker_user_reachable": True, "ambiguous": ambiguous, "bypass": bypass, "precedes_accept": precedes}
