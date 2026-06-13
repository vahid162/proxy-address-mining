"""Topology resolution helpers for Phase 11 packet-path evidence."""
from __future__ import annotations

import ipaddress
import re
from typing import Any

NETWORK_ID_RE = re.compile(r"^[0-9a-f]{64}$")
BRIDGE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
IFACE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")

VALID_BACKEND_TARGET_SOURCES = frozenset({"docker_inspect_verified", "docker_network_inspect_verified", "operator_package_bound"})
REJECTED_BACKEND_TARGET_SOURCES = frozenset({"historical_hardcoded_fallback", "unverified_static_fallback", "unknown"})


def validate_backend_ipv4(value: str, *, source: str) -> tuple[str | None, list[str]]:
    blockers: list[str] = []
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return None, ["backend_ipv4_invalid"]
    if not isinstance(ip, ipaddress.IPv4Address):
        blockers.append("backend_ipv4_not_ipv4")
    if ip.is_loopback:
        blockers.append("backend_ipv4_loopback_forbidden")
    if ip.is_link_local:
        blockers.append("backend_ipv4_link_local_forbidden")
    if ip.is_multicast:
        blockers.append("backend_ipv4_multicast_forbidden")
    if ip.is_unspecified:
        blockers.append("backend_ipv4_unspecified_forbidden")
    if not ip.is_private:
        blockers.append("backend_ipv4_public_forbidden")
    if source not in VALID_BACKEND_TARGET_SOURCES:
        blockers.append(f"backend_target_source_rejected:{source or 'unknown'}")
    return str(ip), blockers


def resolve_docker_bridge(*, network: dict[str, Any], links: list[Any], routes: list[Any], parsed_ipv4: dict[str, Any]) -> dict[str, Any]:
    net_id = str(network.get("network_id") or "")
    endpoint_id = str(network.get("endpoint_id") or "")
    explicit = str(network.get("bridge_name_explicit") or "")
    blockers: list[str] = []
    sources: list[str] = []
    derived = None
    if not NETWORK_ID_RE.fullmatch(net_id):
        blockers.append("docker_network_id_invalid")
    else:
        derived = "br-" + net_id[:12]
        sources.append("network_id_derived_default")
    if endpoint_id and endpoint_id == net_id:
        blockers.append("network_id_endpoint_id_conflated")
    selected = explicit or derived or ""
    source = "explicit_option" if explicit else "derived_network_id" if derived else "unresolved"
    if explicit:
        sources.append("docker_network_option")
        if derived and explicit != derived:
            blockers.append("docker_bridge_explicit_derived_mismatch")
    if not selected or not BRIDGE_RE.fullmatch(selected):
        blockers.append("docker_bridge_name_invalid_or_missing")
    link = _find_link(links, selected)
    if link is None:
        blockers.append("docker_bridge_interface_missing")
    elif str(link.get("operstate") or link.get("state") or "").upper() not in {"UP", "UNKNOWN"} and not link.get("flags"):
        blockers.append("docker_bridge_interface_down")
    elif isinstance(link.get("flags"), list) and "UP" not in link.get("flags", []):
        blockers.append("docker_bridge_interface_down")
    if selected and not _route_uses_dev(routes, selected, str(network.get("ipv4_subnet") or "")):
        blockers.append("docker_bridge_subnet_route_device_mismatch")
    if selected and not _docker_rules_reference_bridge(parsed_ipv4, selected):
        blockers.append("docker_rules_bridge_reference_missing")
    return {
        "bridge_name": selected or None,
        "bridge_name_source": source,
        "bridge_name_candidate": derived,
        "bridge_name_verified": not blockers,
        "bridge_verification_sources": sources + (["ip_link", "ip_route_all", "iptables_save"] if not blockers else []),
        "blockers": sorted(set(blockers)),
    }


def verify_backend_membership(*, bridge_name: str, backend: dict[str, Any], links: list[Any], fdb_entries: list[Any] | None = None, netns_link: list[Any] | None = None, netns_addr: list[Any] | None = None) -> dict[str, Any]:
    mac = str(backend.get("mac_address") or "").lower()
    ip = str(backend.get("resolved_ipv4") or "")
    blockers: list[str] = []
    methods: list[dict[str, Any]] = []
    fdb_ok = None
    if fdb_entries is not None:
        fdb_ok = False
        for row in fdb_entries:
            if not isinstance(row, dict) or str(row.get("mac") or row.get("lladdr") or "").lower() != mac:
                continue
            ifname = str(row.get("dev") or row.get("ifname") or "")
            host = _find_link(links, ifname)
            if host and str(host.get("master") or "") == bridge_name:
                fdb_ok = True
                methods.append({"method": "fdb_mac_to_host_veth", "mac_address": mac, "host_ifname": ifname, "bridge": bridge_name})
                break
        if fdb_ok is False:
            blockers.append("backend_fdb_membership_unverified")
    netns_ok = None
    if netns_link is not None:
        netns_ok = False
        eth0 = next((r for r in netns_link if isinstance(r, dict) and r.get("ifname") == "eth0"), None)
        if eth0 and str(eth0.get("address") or "").lower() == mac:
            iflink = eth0.get("link_index") or eth0.get("iflink")
            host = next((r for r in links if isinstance(r, dict) and r.get("ifindex") == iflink), None)
            addr_ok = _netns_addr_has_ip(netns_addr or [], ip)
            if host and str(host.get("master") or "") == bridge_name and addr_ok:
                netns_ok = True
                methods.append({"method": "netns_eth0_iflink_to_host_veth", "mac_address": mac, "host_ifindex": iflink, "bridge": bridge_name})
        if netns_ok is False:
            blockers.append("backend_netns_membership_unverified")
    if fdb_ok is True and netns_ok is False or fdb_ok is False and netns_ok is True:
        blockers.append("backend_membership_methods_disagree")
    verified = bool(methods) and "backend_membership_methods_disagree" not in blockers
    return {"verified": verified, "status": "verified" if verified else "unresolved", "methods": methods, "blockers": sorted(set(blockers))}


def _find_link(links: list[Any], ifname: str) -> dict[str, Any] | None:
    return next((r for r in links if isinstance(r, dict) and r.get("ifname") == ifname), None)


def _route_uses_dev(routes: list[Any], bridge: str, subnet: str) -> bool:
    return any(isinstance(r, dict) and str(r.get("dev") or "") == bridge and (not subnet or str(r.get("dst") or "") in {subnet, subnet.split('/')[0]}) for r in routes)


def _docker_rules_reference_bridge(parsed_ipv4: dict[str, Any], bridge: str) -> bool:
    for rule in parsed_ipv4.get("rules", []) if isinstance(parsed_ipv4.get("rules"), list) else []:
        match = rule.get("match", {}) if isinstance(rule, dict) and isinstance(rule.get("match"), dict) else {}
        if match.get("out_interface") == bridge or match.get("in_interface") == bridge:
            return True
        if bridge in " ".join(str(x) for x in rule.get("argv", []) if isinstance(rule, dict)):
            return True
    return False


def _netns_addr_has_ip(rows: list[Any], ip: str) -> bool:
    for row in rows:
        for addr in row.get("addr_info", []) if isinstance(row, dict) and isinstance(row.get("addr_info"), list) else []:
            if isinstance(addr, dict) and addr.get("local") == ip:
                return True
    return False
