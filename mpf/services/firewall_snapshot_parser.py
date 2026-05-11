from __future__ import annotations

import hashlib
import shlex

from mpf.domain.firewall import FirewallLiveRuleSnapshot, FirewallLiveSnapshot


def parse_iptables_save_text(text: str) -> FirewallLiveSnapshot:
    chains: list[tuple[str, str]] = []
    rules: list[FirewallLiveRuleSnapshot] = []
    table: str | None = None
    rule_indexes: dict[tuple[str, str], int] = {}

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("*"):
            table = line[1:]
            continue
        if line == "COMMIT":
            table = None
            continue
        if table is None:
            continue

        if line.startswith(":"):
            chain = line[1:].split(" ", 1)[0]
            if chain.startswith("MPF"):
                chains.append((table, chain))
            continue

        if line.startswith("-A "):
            try:
                parts = shlex.split(line, posix=True)
            except ValueError:
                continue
            if len(parts) < 2:
                continue
            chain = parts[1]
            if not chain.startswith("MPF"):
                continue
            comment = _extract_comment(parts)
            per_chain_idx = rule_indexes.get((table, chain), 0)
            rule_indexes[(table, chain)] = per_chain_idx + 1
            rule_key = comment if comment and comment.startswith("mpf:") else _synthetic_rule_key(table=table, chain=chain, rule_index=per_chain_idx, line=line)
            match_json: dict[str, object] = {}
            action_json: dict[str, object] = {}
            _extract_protocol(parts, match_json)
            _extract_source(parts, match_json)
            _extract_destination_port(parts, match_json)
            _extract_target_backend(parts, action_json)
            rules.append(FirewallLiveRuleSnapshot(rule_key=rule_key, table=table, chain=chain, match_json=match_json, action_json=action_json))

    return FirewallLiveSnapshot(chains=chains, rules=rules)


def parse_iptables_save_file(path: str) -> FirewallLiveSnapshot:
    with open(path, "r", encoding="utf-8") as f:
        return parse_iptables_save_text(f.read())


def _extract_comment(parts: list[str]) -> str | None:
    for i, token in enumerate(parts):
        if token == "--comment" and i + 1 < len(parts):
            return parts[i + 1]
    return None


def _extract_protocol(parts: list[str], match_json: dict[str, object]) -> None:
    value = _extract_flag_value(parts, "-p")
    if value is not None:
        match_json["protocol"] = value


def _extract_source(parts: list[str], match_json: dict[str, object]) -> None:
    value = _extract_flag_value(parts, "-s") or _extract_flag_value(parts, "--source")
    if value is not None:
        match_json["source"] = value


def _extract_destination_port(parts: list[str], match_json: dict[str, object]) -> None:
    value = _extract_flag_value(parts, "--dport") or _extract_flag_value(parts, "--destination-port")
    if value is not None:
        match_json["port"] = _parse_int_or_string(value)


def _extract_target_backend(parts: list[str], action_json: dict[str, object]) -> None:
    to_ports = _extract_flag_value(parts, "--to-ports")
    if to_ports is not None:
        action_json["target_backend"] = _parse_int_or_string(to_ports)
        return

    to_destination = _extract_flag_value(parts, "--to-destination")
    if to_destination is None:
        return
    host_or_port = to_destination.rsplit(":", 1)[-1]
    action_json["target_backend"] = _parse_int_or_string(host_or_port)


def _extract_flag_value(parts: list[str], flag: str) -> str | None:
    try:
        idx = parts.index(flag)
    except ValueError:
        return None
    if idx + 1 >= len(parts):
        return None
    return parts[idx + 1]


def _parse_int_or_string(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def _synthetic_rule_key(table: str, chain: str, rule_index: int, line: str) -> str:
    short_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()[:8]
    return f"mpf:auto:{table}:{chain}:{rule_index}:{short_hash}"
