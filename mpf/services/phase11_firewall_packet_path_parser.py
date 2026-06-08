"""Complete-enough iptables-save parser for packet-path proof evidence."""
from __future__ import annotations

import hashlib
import shlex
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass(frozen=True)
class ParsedRule:
    table: str
    chain: str
    rule_index: int
    raw: str
    argv: list[str]
    jump_target: str | None
    jump_kind: str | None
    terminal_verdict: str | None
    rule_hash: str
    match: dict[str, Any] = field(default_factory=dict)
    comment: str | None = None

@dataclass(frozen=True)
class ParsedChain:
    table: str
    name: str
    order: int
    built_in: bool
    policy: str | None

@dataclass(frozen=True)
class ParsedFirewall:
    source_sha256: str
    tables: list[str]
    chains: list[ParsedChain]
    rules: list[ParsedRule]
    input_policy: str | None
    forward_policy: str | None
    prerouting_order: list[str]
    docker_chains_present: list[str]
    mpf_chains_present: list[str]
    unknown_mpf_artifacts: list[str]
    ipv6_mpf_or_customer_artifacts_present: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

_TERMINAL = {"ACCEPT", "DROP", "REJECT", "DNAT", "SNAT", "MASQUERADE", "RETURN"}
_ALLOWED_MPF = {"MPF_NAT_PRE", "MPFC_20001", "MPFC_20101"}


def parse_iptables_save_topology(text: str, *, ipv6: bool = False) -> ParsedFirewall:
    errors: list[str] = []
    if not text.strip():
        errors.append("empty_required_ruleset")
    tables: list[str] = []
    chains: list[ParsedChain] = []
    rules: list[ParsedRule] = []
    seen_chains: set[tuple[str, str]] = set()
    committed: set[str] = set()
    table: str | None = None
    order = 0
    per_chain: dict[tuple[str, str], int] = {}
    mpf_unknown: list[str] = []
    mpf_present: set[str] = set()
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("*"):
            if table is not None:
                errors.append(f"nested_table:{lineno}:{line}")
            table = line[1:]
            tables.append(table)
            continue
        if line == "COMMIT":
            if table is None:
                errors.append(f"commit_without_table:{lineno}")
            else:
                committed.add(table)
            table = None
            continue
        if table is None:
            errors.append(f"line_outside_table:{lineno}:{line[:40]}")
            continue
        if line.startswith(":"):
            parts = line[1:].split()
            if len(parts) < 2:
                errors.append(f"malformed_chain:{lineno}")
                continue
            name, policy = parts[0], parts[1]
            key = (table, name)
            if key in seen_chains:
                errors.append(f"duplicate_chain:{table}:{name}")
            seen_chains.add(key)
            built_in = policy != "-"
            chains.append(ParsedChain(table=table, name=name, order=order, built_in=built_in, policy=None if policy == "-" else policy))
            order += 1
            if name.startswith(("MPF", "MPFBTC", "MPFC_", "MPFO_")):
                mpf_present.add(name)
                if name not in _ALLOWED_MPF:
                    mpf_unknown.append(f"unknown_chain:{table}:{name}")
            continue
        if line.startswith("-A "):
            try:
                argv = shlex.split(line, posix=True)
            except ValueError as exc:
                errors.append(f"malformed_rule:{lineno}:{exc}")
                continue
            if len(argv) < 3:
                errors.append(f"malformed_rule:{lineno}")
                continue
            chain = argv[1]
            key = (table, chain)
            idx = per_chain.get(key, 0)
            per_chain[key] = idx + 1
            jump = _flag(argv, "-j") or _flag(argv, "--jump")
            goto = _flag(argv, "-g") or _flag(argv, "--goto")
            target = jump or goto
            jump_kind = "goto" if goto else "jump" if jump else None
            terminal = target if target in _TERMINAL else None
            comment = _flag(argv, "--comment")
            match = _extract_match(argv)
            if chain.startswith(("MPF", "MPFBTC", "MPFC_", "MPFO_")) and chain not in _ALLOWED_MPF:
                mpf_unknown.append(f"unknown_rule_chain:{table}:{chain}:{idx}")
            if comment and ("mpf:" in comment or "customer_" in comment) and chain not in _ALLOWED_MPF:
                mpf_unknown.append(f"unknown_mpf_comment:{table}:{chain}:{idx}:{comment}")
            rules.append(ParsedRule(table=table, chain=chain, rule_index=idx, raw=line, argv=argv, jump_target=target, jump_kind=jump_kind, terminal_verdict=terminal, rule_hash=hashlib.sha256(line.encode()).hexdigest(), match=match, comment=comment))
            continue
        errors.append(f"unsupported_line:{lineno}:{line[:40]}")
    if table is not None:
        errors.append(f"missing_commit:{table}")
    for t in tables:
        if t not in committed:
            errors.append(f"missing_commit:{t}")
    input_policy = _policy(chains, "filter", "INPUT")
    forward_policy = _policy(chains, "filter", "FORWARD")
    docker = sorted({c.name for c in chains if c.name.startswith("DOCKER")})
    prerouting_order = [r.jump_target or r.terminal_verdict or "" for r in rules if r.table == "nat" and r.chain == "PREROUTING"]
    ipv6_mpf = ipv6 and any(("MPF" in r.raw or "mpf:" in r.raw or "customer_" in r.raw) for r in rules)
    return ParsedFirewall(
        source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        tables=tables,
        chains=chains,
        rules=rules,
        input_policy=input_policy,
        forward_policy=forward_policy,
        prerouting_order=prerouting_order,
        docker_chains_present=docker,
        mpf_chains_present=sorted(mpf_present),
        unknown_mpf_artifacts=sorted(set(mpf_unknown)),
        ipv6_mpf_or_customer_artifacts_present=ipv6_mpf,
        errors=sorted(set(errors)),
    )


def _flag(argv: list[str], name: str) -> str | None:
    try:
        idx = argv.index(name)
    except ValueError:
        return None
    return argv[idx + 1] if idx + 1 < len(argv) else None


def _extract_match(argv: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for flag, key in (("-s", "source"), ("--source", "source"), ("-d", "destination"), ("--destination", "destination"), ("-p", "protocol"), ("-i", "in_interface"), ("--in-interface", "in_interface"), ("-o", "out_interface"), ("--out-interface", "out_interface"), ("--dport", "destination_port"), ("--destination-port", "destination_port"), ("--ctorigdst", "conntrack_original_destination"), ("--ctorigdstport", "conntrack_original_destination_port")):
        val = _flag(argv, flag)
        if val is not None:
            out[key] = int(val) if key.endswith("port") and val.isdigit() else val
    if "--ctorigdst" in argv or "--ctorigdstport" in argv:
        out["conntrack_original_destination_match"] = True
    return out


def _policy(chains: list[ParsedChain], table: str, chain: str) -> str | None:
    for item in chains:
        if item.table == table and item.name == chain:
            return item.policy
    return None
