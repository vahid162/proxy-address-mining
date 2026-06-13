"""Deterministic evidence-derived packet-path graph builder."""
from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Any

from mpf.domain.phase11_controlled_filter_packet_path import PacketPathEdge, PacketPathGraph, PacketPathNode, BACKEND_PORT

DOCKER_CHAIN_NODES = {
    "FORWARD": "filter_chain:FORWARD",
    "INPUT": "filter_chain:INPUT",
    "DOCKER-USER": "filter_chain:DOCKER-USER",
    "DOCKER-FORWARD": "filter_chain:DOCKER-FORWARD",
    "DOCKER-CT": "filter_chain:DOCKER-CT",
    "DOCKER-BRIDGE": "filter_chain:DOCKER-BRIDGE",
    "DOCKER": "filter_chain:DOCKER",
    "DOCKER-ISOLATION-STAGE-1": "filter_chain:DOCKER-ISOLATION-STAGE-1",
    "DOCKER-ISOLATION-STAGE-2": "filter_chain:DOCKER-ISOLATION-STAGE-2",
}


def build_packet_path_graph(*, collection_id: str, hostname: str, backend: dict[str, Any], network: dict[str, Any], topology: dict[str, Any], parsed_ipv4: dict[str, Any]) -> PacketPathGraph:
    backend_ip = str(backend.get("resolved_ipv4") or "")
    bridge = str(network.get("bridge_name") or "")
    chain_names = {str(c.get("name")) for c in parsed_ipv4.get("chains", []) if isinstance(c, dict) and c.get("table") == "filter"}
    nodes = [
        PacketPathNode("external_ingress", "external_ingress", "future external ingress"),
        PacketPathNode("nat_prerouting", "nat_prerouting", "nat PREROUTING"),
        PacketPathNode("future_mpf_nat_entry", "future_mpf_nat_entry", "future controlled MPF NAT entry"),
        PacketPathNode("post_dnat_route_decision", "post_dnat_route_decision", "post-DNAT route decision", {"backend_ipv4": backend_ip}),
        PacketPathNode("future_mpf_filter_entry", "future_mpf_filter_entry", "future MPF filter entry"),
        PacketPathNode("backend_bridge", "backend_bridge", "backend bridge", {"bridge": bridge}),
        PacketPathNode("backend_container", "backend_container", "backend container", {"ip": backend_ip, "port": BACKEND_PORT}),
    ]
    for chain in sorted(chain_names | set(DOCKER_CHAIN_NODES)):
        nodes.append(PacketPathNode(_node_for_chain(chain), "filter_chain", chain, {"chain": chain}))
    edges = [
        PacketPathEdge("external_ingress", "nat_prerouting", "reachable_from", {"evidence_ref": "static_future_packet_class"}),
        PacketPathEdge("future_mpf_nat_entry", "post_dnat_route_decision", "dnat_to", {"to": f"{backend_ip}:{BACKEND_PORT}", "evidence_ref": "review_only_future_nat_entry"}),
    ]
    route_class = classify_route(topology=topology, backend=backend, network=network)
    if route_class == "forwarded":
        edges.append(PacketPathEdge("post_dnat_route_decision", "filter_chain:FORWARD", "routes_to", {"route_evidence_ref": "host-network-topology.json:route_get_backend", "route_device": bridge}))
    elif route_class == "local_input":
        edges.append(PacketPathEdge("post_dnat_route_decision", "filter_chain:INPUT", "routes_to", {"route_evidence_ref": "host-network-topology.json:route_get_backend"}))
    else:
        edges.append(PacketPathEdge("post_dnat_route_decision", "filter_chain:FORWARD", "not_reachable_from", {"route_evidence_ref": "host-network-topology.json:route_get_backend"}))
    for rule in parsed_ipv4.get("rules", []) if isinstance(parsed_ipv4.get("rules"), list) else []:
        if not isinstance(rule, dict) or rule.get("table") != "filter":
            continue
        src = _node_for_chain(str(rule.get("chain")))
        target = str(rule.get("jump_target") or "")
        dst = _node_for_chain(target) if target else "future_mpf_filter_entry"
        edges.append(PacketPathEdge(src, dst, "jumps_to" if rule.get("jump_kind") == "jump" else "routes_to" if rule.get("jump_kind") == "goto" else "precedes", {"scenario_id": "static_all", "source_chain": rule.get("chain"), "target_chain_or_verdict": target, "rule_index": rule.get("rule_index"), "rule_hash": rule.get("rule_hash"), "match_outcome": "un-evaluated", "evidence_reference": "parsed-firewall.json", "hook_seen_before": None, "hook_seen_after": None}))
    if topology.get("backend_bridge_membership_verified") is True:
        edges.append(PacketPathEdge("backend_bridge", "backend_container", "reachable_from", {"membership_verified": True, "docker_network_evidence_ref": "sanitized-docker-network.json", "backend_evidence_ref": "sanitized-backend-target.json"}))
    return PacketPathGraph(collection_id=collection_id, hostname=hostname, nodes=nodes, edges=edges)


def _node_for_chain(chain: str) -> str:
    if chain in DOCKER_CHAIN_NODES:
        return DOCKER_CHAIN_NODES[chain]
    if chain in {"ACCEPT", "DROP", "REJECT", "RETURN"}:
        return f"verdict:{chain}"
    return f"filter_chain:{chain}" if chain else "filter_chain:unknown"


def classify_route(*, topology: dict[str, Any], backend: dict[str, Any], network: dict[str, Any]) -> str:
    backend_ip = str(backend.get("resolved_ipv4") or "")
    host_ips = {str(item.get("local")) for item in topology.get("host_addresses", []) if isinstance(item, dict)}
    if backend_ip and backend_ip in host_ips:
        return "local_input"
    route = topology.get("route_get_backend")
    expected_bridge = str(network.get("bridge_name") or "")
    if isinstance(route, list) and len(route) == 1 and isinstance(route[0], dict):
        item = route[0]
        if str(item.get("type", "unicast")) in {"unreachable", "blackhole", "prohibit", "throw"}:
            return "unresolved"
        dev = str(item.get("dev") or "")
        if dev and expected_bridge and dev == expected_bridge:
            return "forwarded"
    return "unresolved"


def ip_in_subnet(ip: str, subnet: str) -> bool:
    try:
        return ip_address(ip) in ip_network(subnet, strict=False)
    except ValueError:
        return False
