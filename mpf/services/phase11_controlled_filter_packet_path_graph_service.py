"""Deterministic packet-path graph builder for Phase 11 evidence."""
from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Any

from mpf.domain.phase11_controlled_filter_packet_path import PacketPathEdge, PacketPathGraph, PacketPathNode, BACKEND_PORT


def build_packet_path_graph(*, collection_id: str, hostname: str, backend: dict[str, Any], network: dict[str, Any], topology: dict[str, Any], parsed_ipv4: dict[str, Any]) -> PacketPathGraph:
    backend_ip = str(backend.get("resolved_ipv4") or "")
    bridge = str(network.get("bridge_name") or network.get("gateway_interface") or "")
    nodes = [
        PacketPathNode("external_ingress", "external_ingress", "future external ingress"),
        PacketPathNode("nat_prerouting", "nat_prerouting", "nat PREROUTING"),
        PacketPathNode("docker_nat_dispatch", "docker_nat_dispatch", "Docker nat dispatch"),
        PacketPathNode("future_mpf_nat_entry", "future_mpf_nat_entry", "future controlled MPF NAT entry"),
        PacketPathNode("post_dnat_route_decision", "post_dnat_route_decision", "post-DNAT route decision", {"backend_ipv4": backend_ip}),
        PacketPathNode("local_input", "local_input", "INPUT path"),
        PacketPathNode("forward", "forward", "FORWARD path"),
        PacketPathNode("docker_user", "docker_user", "DOCKER-USER hook"),
        PacketPathNode("docker_forward", "docker_forward", "Docker forward chains"),
        PacketPathNode("docker_accept", "docker_accept", "first Docker accept"),
        PacketPathNode("other_filter_chain", "other_filter_chain", "other filter chain"),
        PacketPathNode("future_mpf_filter_entry", "future_mpf_filter_entry", "future MPF filter entry"),
        PacketPathNode("customer_dispatch", "customer_dispatch", "customer dispatch"),
        PacketPathNode("customer_policy", "customer_policy", "customer policy"),
        PacketPathNode("accounting", "accounting", "accounting"),
        PacketPathNode("backend_bridge", "backend_bridge", "backend bridge", {"bridge": bridge}),
        PacketPathNode("backend_container", "backend_container", "backend container", {"ip": backend_ip, "port": BACKEND_PORT}),
    ]
    edges = [
        PacketPathEdge("external_ingress", "nat_prerouting", "reachable_from"),
        PacketPathEdge("nat_prerouting", "future_mpf_nat_entry", "precedes"),
        PacketPathEdge("nat_prerouting", "docker_nat_dispatch", "precedes", {"docker_local_only_publish_distinguishable": True}),
        PacketPathEdge("future_mpf_nat_entry", "post_dnat_route_decision", "dnat_to", {"to": f"{backend_ip}:{BACKEND_PORT}"}),
    ]
    route_class = classify_route(topology=topology, backend=backend, network=network)
    if route_class == "forwarded":
        edges += [
            PacketPathEdge("post_dnat_route_decision", "forward", "routes_to"),
            PacketPathEdge("forward", "docker_user", "jumps_to"),
            PacketPathEdge("docker_user", "forward", "returns_to"),
            PacketPathEdge("forward", "docker_forward", "jumps_to"),
            PacketPathEdge("docker_forward", "docker_accept", "jumps_to"),
            PacketPathEdge("docker_accept", "backend_bridge", "routes_to"),
        ]
    elif route_class == "local_input":
        edges.append(PacketPathEdge("post_dnat_route_decision", "local_input", "routes_to"))
    else:
        edges.append(PacketPathEdge("post_dnat_route_decision", "forward", "not_reachable_from"))
    edges += [
        PacketPathEdge("docker_user", "future_mpf_filter_entry", "jumps_to"),
        PacketPathEdge("future_mpf_filter_entry", "customer_dispatch", "jumps_to"),
        PacketPathEdge("customer_dispatch", "customer_policy", "jumps_to"),
        PacketPathEdge("customer_policy", "accounting", "precedes"),
        PacketPathEdge("backend_bridge", "backend_container", "reachable_from"),
    ]
    return PacketPathGraph(collection_id=collection_id, hostname=hostname, nodes=nodes, edges=edges)


def classify_route(*, topology: dict[str, Any], backend: dict[str, Any], network: dict[str, Any]) -> str:
    backend_ip = str(backend.get("resolved_ipv4") or "")
    host_ips = {str(item.get("local")) for item in topology.get("host_addresses", []) if isinstance(item, dict)}
    if backend_ip and backend_ip in host_ips:
        return "local_input"
    route = topology.get("route_get_backend")
    if isinstance(route, list) and len(route) == 1 and isinstance(route[0], dict):
        item = route[0]
        dev = str(item.get("dev") or "")
        expected_bridge = str(network.get("bridge_name") or network.get("gateway_interface") or "")
        if dev and expected_bridge and dev == expected_bridge:
            return "forwarded"
    return "unresolved"


def ip_in_subnet(ip: str, subnet: str) -> bool:
    try:
        return ip_address(ip) in ip_network(subnet, strict=False)
    except ValueError:
        return False
