"""Source-aware policy routing analysis for packet-path evidence."""
from __future__ import annotations

import ipaddress
from typing import Any

SYNTHETIC_EXTERNAL_NONLOCAL_SOURCE = "198.51.100.77"
_CANONICAL = {(0, "local"), (32766, "main"), (32767, "default")}
_ALLOWED_FIELDS = {
    "priority", "pref", "table", "src", "from", "dst", "to", "fwmark", "iif", "oif", "uidrange",
    "ipproto", "sport", "dport", "protocol", "action", "goto", "not", "l3mdev", "suppress_prefixlength",
    "suppress_ifgroup", "tun_id", "realms",
}
_BLOCK_FIELDS = {"action", "goto", "not", "l3mdev", "suppress_prefixlength", "suppress_ifgroup", "tun_id", "realms"}
_SELECTOR_FIELDS = {"from", "to", "fwmark", "iif", "oif", "uidrange", "ipproto", "sport", "dport"}


def normalize_rule(rule: dict[str, Any]) -> dict[str, Any]:
    out = dict(rule)
    if "src" in out and "from" not in out:
        out["from"] = out["src"]
    if "dst" in out and "to" not in out:
        out["to"] = out["dst"]
    if "pref" in out and "priority" not in out:
        out["priority"] = out["pref"]
    return out


def policy_routing_blockers(*, topology: dict[str, Any], bridge: str, external_interfaces: list[str] | None = None) -> tuple[list[str], list[str]]:
    rules = topology.get("policy_rules", [])
    if not isinstance(rules, list):
        return ["policy_routing_rules_malformed"], []
    blockers: list[str] = []
    warnings: list[str] = []
    canonical_seen: list[tuple[int, str]] = []
    priorities: set[int] = set()
    host_sources = {str(a.get("local")) for a in topology.get("host_addresses", []) if isinstance(a, dict) and a.get("local")}
    for raw in rules:
        if not isinstance(raw, dict):
            blockers.append("policy_routing_rule_malformed")
            continue
        rule = normalize_rule(raw)
        unknown = sorted(set(rule) - _ALLOWED_FIELDS)
        if unknown:
            blockers.extend(f"policy_routing_unknown_field:{field}" for field in unknown)
            blockers.append("policy_routing_ambiguous")
        try:
            priority = int(rule.get("priority"))
        except (TypeError, ValueError):
            blockers.append("policy_routing_rule_malformed")
            continue
        if priority in priorities:
            blockers.append("policy_routing_duplicate_priority")
        priorities.add(priority)
        table = str(rule.get("table", ""))
        selectors = {k: rule.get(k) for k in _SELECTOR_FIELDS if k in rule and str(rule.get(k)) not in {"all", "0.0.0.0/0", "::/0"}}
        canonical = (priority, table) in _CANONICAL and not selectors and not any(k in rule for k in _BLOCK_FIELDS)
        if canonical:
            canonical_seen.append((priority, table))
            continue
        if any(k in rule for k in _BLOCK_FIELDS):
            blockers.extend(f"policy_routing_unsupported_field:{k}" for k in sorted(_BLOCK_FIELDS & set(rule)))
            blockers.append("policy_routing_ambiguous")
        if "protocol" in rule and str(rule.get("protocol")) != "static":
            blockers.append("policy_routing_unknown_protocol_selector")
            blockers.append("policy_routing_ambiguous")
        if not selectors:
            blockers.append("policy_routing_noncanonical_selector_free_rule")
            blockers.append("policy_routing_ambiguous")
        if "fwmark" in selectors:
            blockers.extend(["policy_routing_fwmark_selector", "policy_routing_ambiguous"])
        if "to" in selectors:
            blockers.extend(["policy_routing_destination_selector", "policy_routing_ambiguous"])
        if any(k in selectors for k in ("uidrange", "ipproto", "sport", "dport")):
            blockers.extend(["policy_routing_transport_or_uid_selector", "policy_routing_ambiguous"])
        if any(k in selectors for k in ("iif", "oif")):
            blockers.extend(["policy_routing_interface_selector", "policy_routing_ambiguous"])
        if "from" in selectors:
            src = str(selectors["from"])
            if _source_is_exact_host_local(src, host_sources):
                warnings.append(f"policy_routing_host_local_source_rule_not_applicable:{src}")
            else:
                blockers.extend(["policy_routing_unknown_source_selector", "policy_routing_ambiguous"])
    if set(canonical_seen) != _CANONICAL or len(canonical_seen) != len(_CANONICAL):
        blockers.append("policy_routing_canonical_rules_missing_or_duplicate")
    ext = external_interfaces or [str(i.get("ifname")) for i in topology.get("external_ingress_interfaces", []) if isinstance(i, dict)]
    route_map = topology.get("route_get_backend_by_ingress", {}) if isinstance(topology.get("route_get_backend_by_ingress"), dict) else {}
    for ifname in ext:
        if ifname not in route_map:
            blockers.append(f"route_get_backend_ingress_missing:{ifname}")
            continue
        route_blocker = _route_blocker(route_map.get(ifname), bridge, suffix=f":{ifname}")
        if route_blocker:
            blockers.append(route_blocker)
            blockers.append(route_blocker.split(":", 1)[0])
    if topology.get("local_source_route_divergence"):
        warnings.append("local_source_route_divergence_observed_not_applicable_to_external_nonlocal_source")
    return sorted(set(blockers)), sorted(set(warnings))


def _source_is_exact_host_local(src: str, host_sources: set[str]) -> bool:
    try:
        net = ipaddress.ip_network(src, strict=False)
    except ValueError:
        return False
    return net.prefixlen == 32 and str(net.network_address) in host_sources


def _route_blocker(rows: Any, bridge: str, *, suffix: str = "") -> str | None:
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        return "route_get_backend_ambiguous" + suffix
    typ = str(rows[0].get("type", "unicast"))
    if typ in {"unreachable", "blackhole", "prohibit", "throw"}:
        return f"route_get_backend_{typ}" + suffix
    if str(rows[0].get("dev") or "") != bridge:
        return "route_get_backend_device_mismatch" + suffix
    return None
