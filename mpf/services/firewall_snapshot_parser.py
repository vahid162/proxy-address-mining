from __future__ import annotations

from mpf.domain.firewall import FirewallLiveRuleSnapshot, FirewallLiveSnapshot


def parse_iptables_save_text(text: str) -> FirewallLiveSnapshot:
    chains: list[tuple[str, str]] = []
    rules: list[FirewallLiveRuleSnapshot] = []
    table: str | None = None

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
            parts = line.split()
            if len(parts) < 4:
                continue
            chain = parts[1]
            if not chain.startswith("MPF"):
                continue
            comment = _extract_comment(parts)
            rule_key = comment if comment and comment.startswith("mpf:") else f"mpf:auto:{table}:{chain}:{len(rules)}"
            match_json: dict[str, object] = {}
            action_json: dict[str, object] = {}
            if "--dport" in parts:
                dport_idx = parts.index("--dport")
                if dport_idx + 1 < len(parts):
                    try:
                        match_json["port"] = int(parts[dport_idx + 1])
                    except ValueError:
                        match_json["port"] = parts[dport_idx + 1]
            if "--to-ports" in parts:
                to_idx = parts.index("--to-ports")
                if to_idx + 1 < len(parts):
                    try:
                        action_json["target_backend"] = int(parts[to_idx + 1])
                    except ValueError:
                        action_json["target_backend"] = parts[to_idx + 1]
            rules.append(FirewallLiveRuleSnapshot(rule_key=rule_key, table=table, chain=chain, match_json=match_json, action_json=action_json))

    return FirewallLiveSnapshot(chains=chains, rules=rules)


def parse_iptables_save_file(path: str) -> FirewallLiveSnapshot:
    with open(path, "r", encoding="utf-8") as f:
        return parse_iptables_save_text(f.read())


def _extract_comment(parts: list[str]) -> str | None:
    for i, token in enumerate(parts):
        if token == "--comment" and i + 1 < len(parts):
            return parts[i + 1].strip('"')
    return None
