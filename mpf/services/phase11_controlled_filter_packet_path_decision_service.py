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
from mpf.services.phase11_packet_path_match_semantics import PacketScenario, evaluate_rule_match, scenario_to_packet, unsupported_match_blockers
from mpf.services.phase11_packet_path_policy_routing import policy_routing_blockers

HOOK = "DOCKER-USER"
MAX_STEPS = 512

_SUPPORTED_MATCH_MODULES = {"tcp", "comment"}
_SUPPORTED_VALUE_OPTIONS = {
    "-s",
    "--source",
    "-d",
    "--destination",
    "-p",
    "-i",
    "--in-interface",
    "-o",
    "--out-interface",
    "--dport",
    "--destination-port",
    "--comment",
    "-m",
    "--match",
    "-j",
    "--jump",
    "-g",
    "--goto",
}
_NEGATABLE_MATCH_OPTIONS = {
    "-s",
    "--source",
    "-d",
    "--destination",
    "-p",
    "-i",
    "--in-interface",
    "-o",
    "--out-interface",
    "--dport",
    "--destination-port",
}
_OPTION_ALIASES = {
    "--source": "source",
    "-s": "source",
    "--destination": "destination",
    "-d": "destination",
    "-p": "protocol",
    "--in-interface": "in_interface",
    "-i": "in_interface",
    "--out-interface": "out_interface",
    "-o": "out_interface",
    "--destination-port": "destination_port",
    "--dport": "destination_port",
}


@dataclass
class FlowResult:
    accepts: list[dict[str, Any]] = field(default_factory=list)
    drops: list[dict[str, Any]] = field(default_factory=list)
    returns: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    hook_seen_any: bool = False
    edges: list[dict[str, Any]] = field(default_factory=list)
    hook_entry_count: int = 0


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

    ingress_list = topology.get("external_ingress_interfaces") if isinstance(topology.get("external_ingress_interfaces"), list) else []
    ingress_names = [str(i.get("ifname")) for i in ingress_list if isinstance(i, dict) and i.get("ifname")] or [""]
    scenarios: list[dict[str, Any]] = []
    scenario_results: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []
    for ingress in ingress_names:
        for state in ("NEW", "ESTABLISHED"):
            sid = f"external_nonlocal:{ingress or 'unknown'}:tcp:{state}:60010"
            scenario = PacketScenario(sid, "external_nonlocal_source", ingress, bridge, "tcp", backend_ip, BACKEND_PORT, state, f"route_get_backend_by_ingress:{ingress}")
            scenarios.append(scenario.__dict__)
            flow_s = _walk_chain("FORWARD", 0, chain_map, policies, user_chains, scenario_to_packet(scenario), hook_seen=False, call_stack=[], steps=0, scenario_id=sid)
            graph_edges.extend(flow_s.edges)
            scenario_blockers: list[str] = []
            if flow_s.hook_entry_count > 1:
                scenario_blockers.append("docker_user_hook_duplicated_or_ambiguous")
            if flow_s.unresolved:
                scenario_blockers.extend(flow_s.unresolved)
            if not flow_s.hook_seen_any:
                scenario_blockers.append("docker_user_not_reachable_on_forward_path")
            scenario_bypass = [a for a in flow_s.accepts if not a.get("hook_seen")]
            if scenario_bypass:
                scenario_blockers.append("accept_bypass_before_docker_user")
            if not flow_s.accepts:
                scenario_blockers.append("no_applicable_accept_path_to_backend")
            if any(a.get("hook_seen") is not True for a in flow_s.accepts):
                scenario_blockers.append("docker_user_does_not_precede_accept_paths")
            scenario_results.append({"scenario_id": sid, "hook_entry_count": flow_s.hook_entry_count, "accepts": flow_s.accepts, "blockers": sorted(set(scenario_blockers)), "ready": not scenario_blockers})
            blockers.extend(scenario_blockers)
            blockers.extend(f"scenario:{sid}:{b}" for b in scenario_blockers)
    graph["packet_scenarios"] = scenarios
    graph["scenario_results"] = scenario_results
    graph["verified_cfg_edges"] = graph_edges
    bypass_accepts: list[dict[str, Any]] = []
    flow = FlowResult(accepts=[a for r in scenario_results for a in r.get("accepts", [])], hook_seen_any=any(r.get("hook_entry_count") for r in scenario_results), hook_entry_count=max([int(r.get("hook_entry_count") or 0) for r in scenario_results] or [0]))

    packet_view = "post_dnat_forward_filter" if route_class == "forwarded" and flow.hook_seen_any and not flow.unresolved else "unknown"
    visible = {"ip": backend_ip if packet_view != "unknown" else None, "port": BACKEND_PORT if packet_view != "unknown" else None}
    renderer_blockers = [
        "current_controlled_artifact_renderer_uses_INPUT_parent_hook",
        "current_customer_filter_rules_match_public_destination_ports_20001_20101",
        "verified_forward_docker_user_hook_is_post_dnat_and_sees_backend_destination_60010",
        "conntrack_original_destination_match_requires_reviewed_artifact_graph_binding",
    ]
    final = READY if not blockers else BLOCKED
    verified_future_reachability = final == READY
    graph["future_mpf_entry_reachable"] = verified_future_reachability
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
        future_mpf_entry_reachable=verified_future_reachability,
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
    source = str(backend.get("backend_target_source") or "unknown")
    if backend.get("historical_hardcoded_target_assumed") is True or source in {"historical_hardcoded_fallback", "unverified_static_fallback", "unknown"}:
        blockers.append("backend_target_source_not_verified")
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
    if network.get("bridge_name_verified") is not True:
        blockers.append("docker_bridge_resolution_unverified")
    if topology.get("backend_bridge_membership_verified") is not True:
        blockers.append("backend_bridge_membership_unverified")
    if topology.get("backend_bridge_membership_status") != "verified":
        blockers.append("backend_bridge_membership_unresolved")
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
    bridge = ""
    route = topology.get("route_get_backend")
    if isinstance(route, list) and route and isinstance(route[0], dict):
        bridge = str(route[0].get("dev") or "")
    blockers, _warnings = policy_routing_blockers(topology=topology, bridge=bridge)
    return blockers

def _walk_chain(chain: str, start: int, chain_map: dict[str, list[dict[str, Any]]], policies: dict[str, str | None], user_chains: set[str], packet: dict[str, Any], *, hook_seen: bool, call_stack: list[str], steps: int, scenario_id: str = "legacy") -> FlowResult:
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
        edge = {"scenario_id": scenario_id, "source_chain": chain, "target_chain_or_verdict": target, "rule_index": rule.get("rule_index"), "rule_hash": rule.get("rule_hash"), "target": target, "jump_kind": rule.get("jump_kind"), "match_outcome": True, "evidence_reference": "parsed-firewall.json", "hook_seen_before": local_hook, "hook_seen_after": (local_hook or target == HOOK)}
        result.edges.append(edge)
        if target == HOOK:
            local_hook = True
            result.hook_seen_any = True
            result.hook_entry_count += 1
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
            child = _walk_chain(target, 0, chain_map, policies, user_chains, packet, hook_seen=local_hook, call_stack=[*call_stack, chain], steps=steps + 1, scenario_id=scenario_id)
            result.edges.extend(child.edges)
            result.unresolved.extend(child.unresolved)
            result.accepts.extend(child.accepts)
            result.drops.extend(child.drops)
            result.hook_seen_any = result.hook_seen_any or child.hook_seen_any
            result.hook_entry_count += child.hook_entry_count
            if rule.get("jump_kind") == "goto":
                result.returns.extend(child.returns)
                return result
            if child.accepts or child.drops:
                return result
            local_hook = local_hook or child.hook_seen_any
            continue
        if target is not None:
            result.unresolved.append(f"unsupported_target_semantics:{chain}:{rule.get('rule_index')}:{target}")
            return result
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
    ev = evaluate_rule_match(rule, packet)
    if ev.applies is None:
        return "unresolved"
    if ev.applies is False:
        return False
    match = rule.get("match", {}) if isinstance(rule.get("match"), dict) else {}
    # Source matching for the synthetic external class is only supported when
    # fully modeled by policy routing; fail closed for raw source-only rules.
    if "source" in match:
        return "unresolved"
    return True

def _unsupported_match_blocker(rule: dict[str, Any]) -> bool:
    return bool(unsupported_match_blockers(rule))

def _protocol_match(value: str, packet_protocol: str) -> bool | None:
    normalized = value.strip().lower()
    packet = packet_protocol.strip().lower()
    if normalized in {"all", "0"}:
        return True
    if packet == "tcp" and normalized in {"tcp", "6"}:
        return True
    if normalized in {"udp", "17", "icmp", "1", "icmpv6", "ipv6-icmp", "58", "sctp", "132", "gre", "47", "esp", "50", "ah", "51"}:
        return False
    return None


def _port_match(value: object, packet_port: int) -> bool | None:
    if isinstance(value, int):
        return value == packet_port
    text = str(value).strip()
    if text.isdigit():
        return int(text) == packet_port
    if ":" not in text or text.count(":") != 1:
        return None
    start_text, end_text = text.split(":", 1)
    if start_text and not start_text.isdigit():
        return None
    if end_text and not end_text.isdigit():
        return None
    start = int(start_text) if start_text else 0
    end = int(end_text) if end_text else 65535
    if not (0 <= start <= end <= 65535):
        return None
    return start <= packet_port <= end


def _interface_match(pattern: str, interface: str) -> bool | None:
    if not pattern or not interface:
        return None
    if pattern.endswith("+"):
        return interface.startswith(pattern[:-1])
    return pattern == interface


def _ip_match(ip: str, pattern: str) -> bool | None:
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(pattern, strict=False)
    except ValueError:
        return None


def _decision(final: str, blockers: list[str], *, warnings: list[str]) -> PacketPathDecision:
    return PacketPathDecision(final_decision=final, blockers=sorted(set(blockers)), warnings=sorted(set(warnings)))  # type: ignore[arg-type]
