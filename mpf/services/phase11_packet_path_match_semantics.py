"""Typed iptables match semantics for Phase 11 packet-path analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import ipaddress

SUPPORTED_MODULES = {"tcp", "comment", "conntrack", "addrtype"}
TERMINAL_TARGETS = {"ACCEPT", "DROP", "REJECT", "RETURN"}

@dataclass(frozen=True)
class PacketScenario:
    scenario_id: str
    source_class: str
    ingress_interface: str
    output_interface: str
    protocol: str
    destination: str
    destination_port: int
    conntrack_state: str
    route_evidence_ref: str

@dataclass
class MatchEvaluation:
    applies: bool | None
    unresolved: list[str] = field(default_factory=list)


def scenario_to_packet(s: PacketScenario) -> dict[str, Any]:
    return {"protocol": s.protocol, "destination": s.destination, "destination_port": s.destination_port, "out_interface": s.output_interface, "in_interface": s.ingress_interface, "conntrack_state": s.conntrack_state}


def unsupported_match_blockers(rule: dict[str, Any]) -> list[str]:
    argv = [str(x) for x in rule.get("argv", []) if isinstance(x, str)]
    if len(argv) < 2 or argv[0] != "-A":
        return ["malformed_rule_argv"]
    blockers: list[str] = []
    seen: set[str] = set()
    i = 2
    value_opts = {"-s", "--source", "-d", "--destination", "-p", "-i", "--in-interface", "-o", "--out-interface", "--dport", "--destination-port", "--comment", "-m", "--match", "-j", "--jump", "-g", "--goto", "--ctstate", "--dst-type"}
    negatable = {"-s", "--source", "-d", "--destination", "-p", "-i", "--in-interface", "-o", "--out-interface", "--dport", "--destination-port"}
    while i < len(argv):
        neg = argv[i] == "!"
        if neg:
            i += 1
            if i >= len(argv) or argv[i] not in negatable:
                return ["unsupported_negation"]
        tok = argv[i]
        if tok not in value_opts or i + 1 >= len(argv):
            return [f"unknown_or_malformed_option:{tok}"]
        val = argv[i+1]
        if tok in {"-m", "--match"} and val not in SUPPORTED_MODULES:
            return [f"unknown_match_module:{val}"]
        key = tok if tok not in {"-j", "--jump", "-g", "--goto", "-m", "--match", "--comment"} else tok + ":" + val
        if key in seen and tok not in {"-m", "--match"}:
            return [f"duplicate_match_condition:{tok}"]
        seen.add(key)
        i += 2
    return blockers


def evaluate_rule_match(rule: dict[str, Any], packet: dict[str, Any]) -> MatchEvaluation:
    blockers = unsupported_match_blockers(rule)
    if blockers:
        return MatchEvaluation(None, blockers)
    m = rule.get("match", {}) if isinstance(rule.get("match"), dict) else {}
    for key, fn in (
        ("protocol", lambda v: _protocol_match(str(v), str(packet.get("protocol")))),
        ("destination_port", lambda v: _port_match(v, int(packet.get("destination_port")))),
        ("destination", lambda v: _ip_match(str(packet.get("destination")), str(v))),
        ("source", lambda v: None),
        ("out_interface", lambda v: _interface_match(str(v), str(packet.get("out_interface") or ""))),
        ("in_interface", lambda v: _interface_match(str(v), str(packet.get("in_interface") or ""))),
        ("conntrack_states", lambda v: str(packet.get("conntrack_state")) in set(v if isinstance(v, list) else str(v).split(","))),
        ("addrtype_dst_type", lambda v: str(v).upper() == "LOCAL" and packet.get("destination_class") == "host_local"),
    ):
        if key in m:
            out = fn(m[key])
            if out is None:
                return MatchEvaluation(None, [f"match_unresolved:{key}"])
            if m.get(f"{key}_negated"):
                out = not out
            if not out:
                return MatchEvaluation(False, [])
    return MatchEvaluation(True, [])


def _protocol_match(value: str, packet_protocol: str) -> bool | None:
    v = value.lower(); p = packet_protocol.lower()
    if v in {"all", "0"}: return True
    if p == "tcp" and v in {"tcp", "6"}: return True
    if v in {"udp", "17", "icmp", "1", "icmpv6", "ipv6-icmp", "58"}: return False
    return None


def _port_match(value: object, packet_port: int) -> bool | None:
    text = str(value)
    if text.isdigit(): return int(text) == packet_port
    if ":" not in text or text.count(":") != 1: return None
    a,b = text.split(":",1)
    if (a and not a.isdigit()) or (b and not b.isdigit()): return None
    start = int(a) if a else 0; end = int(b) if b else 65535
    if not 0 <= start <= end <= 65535: return None
    return start <= packet_port <= end


def _interface_match(pattern: str, interface: str) -> bool | None:
    if not pattern or not interface: return None
    if pattern.endswith("+"): return interface.startswith(pattern[:-1])
    return pattern == interface


def _ip_match(ip: str, pattern: str) -> bool | None:
    try: return ipaddress.ip_address(ip) in ipaddress.ip_network(pattern, strict=False)
    except ValueError: return None
