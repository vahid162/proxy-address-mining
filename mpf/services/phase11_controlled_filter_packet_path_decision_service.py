"""Decision service for controlled filter packet-path proof.

The READY proof is intentionally conservative: it explores a match-aware control
flow graph for the exact post-DNAT packet class and blocks on ambiguity, cycles,
policy-routing ambiguity, or any applicable ACCEPT path that does not traverse
DOCKER-USER first.
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import Any

from mpf.domain.phase11_controlled_filter_packet_path import BACKEND_PORT, BLOCKED, READY, INVALID, PacketPathDecision
from mpf.services.phase11_controlled_filter_packet_path_graph_service import classify_route, ip_in_subnet

HOOK = "DOCKER-USER"
MAX_STEPS = 512


@dataclass
class FlowResult:
    accepts: list[dict[str, Any]] = field(default_factory=list)
    drops: list[dict[str, Any]] = field(default_factory=list)
    returns: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    hook_seen_any: bool = False
    edges: list[dict[str, Any]] = field(default_factory=list)


def decide_controlled_filter_packet_path(*, evidence: dict[str, Any], graph: dict[str, Any], parsed_firewall: dict[str, Any], command_results: list[dict[str, Any]]) -> PacketPathDecision:
    invalid = _invalid_command_blockers(command_results, evidence)
    fw4 = parsed_firewall.get("ipv4", {}) if isinstance(parsed_firewall.get("ipv4"), dict) else {}
    fw6 = parsed_firewall.get("ipv6", {}) if isinstance(parsed_firewall.get("ipv6"), dict) else {}
    if fw4.get("errors"):
        invalid.extend(f"malformed_ipv4_ruleset:{e}" for e in fw4.get("errors", []))
    if fw6.get("errors"):
        invalid.extend(f"malformed_ipv6_ruleset:{e}" for e in fw6.get("errors", []))
    for err in evidence.get("parse_errors", []) if isinstance(evidence.get("parse_errors"), list) else []:
        invalid.append(str(err))
    if invalid:
        return _decision(INVALID, invalid, warnings=[])

    blockers: list[str] = []
    warnings: list[str] = []
    backend = evidence.get("backend_target", {}) if isinstance(evidence.get("backend_target"), dict) else {}
    network = evidence.get("docker_network", {}) if isinstance(evidence.get("docker_network"), dict) else {}
    topology = evidence.get("host_topology", {}) if isinstance(evidence.get("host_topology"), dict) else {}
    backend_ip = str(backend.get("resolved_ipv4") or "")
    bridge = str(network.get("bridge_name") or "")
    subnet = str(network.get("ipv4_subnet") or "")
    host_ips = {str(item.get("local")) for item in topology.get("host_addresses", []) if isinstance(item, dict)}
    target_is_local = backend_ip in host_ips
    route_class = classify_route(topology=topology, backend=backend, network=network)
    target_in_subnet = bool(backend_ip and subnet and ip_in_subnet(backend_ip, subnet))

    blockers.extend(_topology_blockers(backend=backend, network=network, topology=topology, backend_ip=backend_ip, subnet=subnet, bridge=bridge, route_class=route_class, target_is_local=target_is_local, target_in_subnet=target_in_subnet))
    if fw4.get("unknown_mpf_artifacts"):
        blockers.append("unknown_mpf_artifacts_present")
    if fw6.get("ipv6_mpf_or_customer_artifacts_present"):
        blockers.append("ipv6_mpf_or_customer_artifact_detected")

    rules = fw4.get("rules", []) if isinstance(fw4.get("rules"), list) else []
    chains = fw4.get("chains", []) if isinstance(fw4.get("chains"), list) else []
    chain_map: dict[str, list[dict[str, Any]]] = {}
    policies: dict[str, str | None] = {}
    user_chains: set[str] = set()
    for chain in chains:
        if not isinstance(chain, dict) or chain.get("table") != "filter":
            continue
        name = str(chain.get("name"))
        policies[name] = chain.get("policy") if isinstance(chain.get("policy"), str) else None
        if not chain.get("built_in"):
            user_chains.add(name)
    for rule in rules:
        if isinstance(rule, dict) and rule.get("table") == "filter":
            chain_map.setdefault(str(rule.get("chain")), []).append(rule)
    for values in chain_map.values():
        values.sort(key=lambda r: int(r.get("rule_index", 0)))

    packet = {"protocol": "tcp", "destination": backend_ip, "destination_port": BACKEND_PORT, "out_interface": bridge, "ingress_interface_known": False}
    applicable_hook_count = sum(1 for rule in chain_map.get("FORWARD", []) if rule.get("jump_target") == HOOK and _rule_applies(rule, packet, target_is_hook=True) is True)
    flow = _walk_chain("FORWARD", 0, chain_map, policies, user_chains, packet, hook_seen=False, call_stack=[], steps=0)
    graph["verified_cfg_edges"] = flow.edges
    graph["future_mpf_entry_reachable"] = bool(flow.hook_seen_any and not flow.unresolved)

    if applicable_hook_count > 1:
        blockers.append("docker_user_hook_duplicated_or_ambiguous")
    if flow.unresolved:
        blockers.extend(flow.unresolved)
    if not flow.hook_seen_any:
        blockers.append("docker_user_not_reachable_on_forward_path")
    bypass_accepts = [a for a in flow.accepts if not a.get("hook_seen")]
    if bypass_accepts:
        blockers.append("accept_bypass_before_docker_user")
    if not flow.accepts:
        blockers.append("no_applicable_accept_path_to_backend")
    if any(a.get("hook_seen") is not True for a in flow.accepts):
        blockers.append("docker_user_does_not_precede_accept_paths")

    packet_view = "post_dnat_forward_filter" if route_class == "forwarded" and flow.hook_seen_any and not flow.unresolved else "unknown"
    visible = {"ip": backend_ip if packet_view != "unknown" else None, "port": BACKEND_PORT if packet_view != "unknown" else None}
    renderer_blockers = [
        "current_controlled_artifact_renderer_uses_INPUT_parent_hook",
        "current_customer_filter_rules_match_public_destination_ports_20001_20101",
        "verified_forward_docker_user_hook_is_post_dnat_and_sees_backend_destination_60010",
        "conntrack_original_destination_match_requires_reviewed_artifact_graph_binding",
    ]
    final = READY if not blockers else BLOCKED
    return PacketPathDecision(
        final_decision=final,
        post_dnat_route_class=route_class,
        verified_builtin_filter_path="FORWARD" if route_class == "forwarded" else None,
        verified_user_policy_hook=HOOK if final == READY else None,
        input_path_applicable=route_class == "local_input",
        forward_path_applicable=route_class == "forwarded",
        docker_user_reachable=flow.hook_seen_any and not flow.unresolved,
        hook_precedes_all_relevant_accept_paths=bool(flow.accepts) and not bypass_accepts and not flow.unresolved,
        bypass_path_detected=bool(bypass_accepts),
        future_mpf_entry_reachable=flow.hook_seen_any and not flow.unresolved and not bypass_accepts,
        packet_view_at_verified_hook=packet_view,
        destination_visible_at_verified_hook=visible,
        original_destination_available_via_conntrack="unresolved",
        original_destination_match_required=packet_view == "post_dnat_forward_filter",
        current_customer_port_match_compatible=False,
        current_renderer_binding_compatible=False,
        renderer_binding_blockers=renderer_blockers,
        blockers=sorted(set(blockers)),
        warnings=warnings,
        evidence_hashes=evidence.get("evidence_hashes", {}) if isinstance(evidence.get("evidence_hashes"), dict) else {},
    )


def _invalid_command_blockers(command_results: list[dict[str, Any]], evidence: dict[str, Any]) -> list[str]:
    invalid: list[str] = []
    seen: set[str] = set()
    for result in command_results:
        cid = str(result.get("command_id"))
        if cid in seen:
            invalid.append(f"duplicate_command_id:{cid}")
        seen.add(cid)
        if result.get("return_code") != 0:
            invalid.append(f"command_failed:{cid}:{result.get('return_code')}")
        if result.get("timed_out") is True:
            invalid.append(f"command_timeout:{cid}")
        if result.get("output_truncated") is True:
            invalid.append(f"command_output_truncated:{cid}")
        if result.get("mutation_performed") is not False:
            invalid.append(f"mutation_performed:{cid}")
    if evidence.get("mutation_performed") is not False:
        invalid.append("mutation_performed")
    return invalid


def _topology_blockers(*, backend: dict[str, Any], network: dict[str, Any], topology: dict[str, Any], backend_ip: str, subnet: str, bridge: str, route_class: str, target_is_local: bool, target_in_subnet: bool) -> list[str]:
    blockers: list[str] = []
    if backend.get("status") != "ok":
        blockers.append("backend_target_not_healthy")
    if network.get("status") != "ok":
        blockers.append("docker_network_not_verified")
    if backend.get("backend_public_exposure") is True:
        blockers.append("backend_public_exposure_detected")
    if target_is_local:
        blockers.append("backend_target_is_host_local")
    if not target_in_subnet:
        blockers.append("backend_target_outside_expected_docker_subnet")
    if route_class != "forwarded":
        blockers.append(f"post_dnat_route_not_forwarded:{route_class}")
    if str(topology.get("ip_forward", "")) != "1":
        blockers.append("ipv4_forwarding_disabled")
    if network.get("unknown_connected_containers"):
        blockers.append("unknown_docker_network_containers_present")
    if backend.get("historical_hardcoded_target_assumed") is True or backend_ip == "172.18.0.3":
        blockers.append("historical_backend_target_forbidden")
    if network.get("network_name") != "mpf-proxy-internal":
        blockers.append("docker_network_name_mismatch")
    if network.get("driver") != "bridge":
        blockers.append("docker_network_driver_not_bridge")
    if not network.get("network_id") or backend.get("network_id") != network.get("network_id"):
        blockers.append("docker_network_id_mismatch")
    if backend.get("network_inspect_container_id_match") is not True:
        blockers.append("backend_container_missing_from_network_inspect")
    if backend.get("network_inspect_ipv4_match") is not True:
        blockers.append("backend_ipv4_mismatch_between_inspects")
    if not _bridge_exists(topology, bridge):
        blockers.append("docker_bridge_interface_missing")
    if not topology.get("backend_bridge_membership_verified"):
        blockers.append("backend_bridge_membership_unverified")
    blockers.extend(_policy_routing_blockers(topology))
    if subnet:
        try:
            ipaddress.ip_network(subnet, strict=False)
        except ValueError:
            blockers.append("docker_network_subnet_invalid")
    if network.get("gateway_invalid"):
        blockers.append("docker_network_gateway_invalid")
    return blockers


def _bridge_exists(topology: dict[str, Any], bridge: str) -> bool:
    if not bridge:
        return False
    return any(isinstance(item, dict) and item.get("ifname") == bridge for item in topology.get("links", []))


def _policy_routing_blockers(topology: dict[str, Any]) -> list[str]:
    rules = topology.get("policy_rules", [])
    if not isinstance(rules, list):
        return ["policy_routing_rules_malformed"]
    blockers: list[str] = []
    for rule in rules:
        if not isinstance(rule, dict):
            blockers.append("policy_routing_rule_malformed")
            continue
        table = str(rule.get("table", "main"))
        priority = int(rule.get("priority", rule.get("pref", 32766))) if str(rule.get("priority", rule.get("pref", 32766))).isdigit() else 32766
        selectors = {k for k in rule if k in {"from", "to", "fwmark", "iif", "oif", "uidrange", "ipproto", "sport", "dport"}}
        if table not in {"main", "local", "default", "255", "254", "253"} or selectors or priority < 32766:
            blockers.append("policy_routing_ambiguous")
    route = topology.get("route_get_backend", [])
    if not isinstance(route, list) or len(route) != 1 or not isinstance(route[0], dict):
        blockers.append("route_get_backend_ambiguous")
    elif str(route[0].get("type", "unicast")) in {"unreachable", "blackhole", "prohibit"}:
        blockers.append(f"route_get_backend_{route[0].get('type')}")
    return sorted(set(blockers))


def _walk_chain(chain: str, start: int, chain_map: dict[str, list[dict[str, Any]]], policies: dict[str, str | None], user_chains: set[str], packet: dict[str, Any], *, hook_seen: bool, call_stack: list[str], steps: int) -> FlowResult:
    result = FlowResult(hook_seen_any=hook_seen or chain == HOOK)
    if steps > MAX_STEPS:
        result.unresolved.append("cfg_traversal_limit_exceeded")
        return result
    if chain in call_stack:
        result.unresolved.append(f"cfg_cycle_detected:{'->'.join([*call_stack, chain])}")
        return result
    rules = chain_map.get(chain, [])
    idx = start
    local_hook = hook_seen or chain == HOOK
    while idx < len(rules):
        rule = rules[idx]
        idx += 1
        applies = _rule_applies(rule, packet, target_is_hook=(rule.get("jump_target") == HOOK))
        if applies == "unresolved":
            result.unresolved.append(f"rule_match_unresolved:{chain}:{rule.get('rule_index')}")
            continue
        if applies is False:
            continue
        target = rule.get("jump_target")
        edge = {"source_chain": chain, "rule_index": rule.get("rule_index"), "rule_hash": rule.get("rule_hash"), "target": target, "jump_kind": rule.get("jump_kind"), "hook_seen_before": local_hook}
        result.edges.append(edge)
        if target == HOOK:
            local_hook = True
            result.hook_seen_any = True
        if target in {"ACCEPT", "DROP", "REJECT"}:
            terminal = {"chain": chain, "rule_index": rule.get("rule_index"), "hook_seen": local_hook, "target": target, "rule_hash": rule.get("rule_hash")}
            if target == "ACCEPT":
                result.accepts.append(terminal)
            else:
                result.drops.append(terminal)
            return result
        if target == "RETURN":
            result.returns.append({"chain": chain, "rule_index": rule.get("rule_index"), "hook_seen": local_hook})
            return result
        if isinstance(target, str) and target in user_chains:
            child = _walk_chain(target, 0, chain_map, policies, user_chains, packet, hook_seen=local_hook, call_stack=[*call_stack, chain], steps=steps + 1)
            result.edges.extend(child.edges)
            result.unresolved.extend(child.unresolved)
            result.accepts.extend(child.accepts)
            result.drops.extend(child.drops)
            result.hook_seen_any = result.hook_seen_any or child.hook_seen_any
            if rule.get("jump_kind") == "goto":
                result.returns.extend(child.returns)
                return result
            if child.accepts or child.drops:
                return result
            local_hook = local_hook or child.hook_seen_any
            continue
    policy = policies.get(chain)
    if policy == "ACCEPT":
        result.accepts.append({"chain": chain, "rule_index": "policy", "hook_seen": local_hook, "target": "ACCEPT"})
    elif policy in {"DROP", "REJECT"}:
        result.drops.append({"chain": chain, "rule_index": "policy", "hook_seen": local_hook, "target": policy})
    else:
        result.returns.append({"chain": chain, "rule_index": "end", "hook_seen": local_hook})
    result.hook_seen_any = result.hook_seen_any or local_hook
    return result


def _rule_applies(rule: dict[str, Any], packet: dict[str, Any], *, target_is_hook: bool) -> bool | str:
    match = rule.get("match", {}) if isinstance(rule.get("match"), dict) else {}
    proto = match.get("protocol")
    if proto and proto != packet["protocol"]:
        return False
    dport = match.get("destination_port")
    if dport is not None and dport != packet["destination_port"]:
        return False
    dst = match.get("destination")
    if dst and not _ip_match(str(packet["destination"]), str(dst)):
        return False
    out_if = match.get("out_interface")
    if out_if and out_if != packet.get("out_interface"):
        return False
    in_if = match.get("in_interface")
    if in_if and target_is_hook:
        return False
    return True


def _ip_match(ip: str, pattern: str) -> bool:
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(pattern, strict=False)
    except ValueError:
        return ip == pattern


def _decision(final: str, blockers: list[str], *, warnings: list[str]) -> PacketPathDecision:
    return PacketPathDecision(final_decision=final, blockers=sorted(set(blockers)), warnings=sorted(set(warnings)))  # type: ignore[arg-type]
