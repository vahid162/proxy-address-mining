from __future__ import annotations

import hashlib
import ipaddress
from collections import Counter
from typing import Any

from mpf.domain.firewall import (
    FirewallApplyContract,
    FirewallPlanMessage,
    FirewallPlanResult,
    FirewallRestoreChain,
    FirewallRestorePayload,
    FirewallRestoreRule,
    FirewallRestoreTable,
    FirewallRestoreValidationResult,
)

_ALLOWED_TABLES = {"filter", "nat"}
_SUPPORTED_KINDS = {
    "backend_guard",
    "customer_dispatch",
    "customer_connlimit_reject",
    "customer_hashlimit_reject",
    "customer_accounting_in",
    "customer_accounting_out",
    "customer_whitelist_allow",
    "customer_whitelist_reject",
    "customer_nat_redirect",
    "customer_pause_reject",
    "customer_expired_reject",
}


def _message(code: str, message: str, severity: str = "error") -> FirewallPlanMessage:
    return FirewallPlanMessage(code=code, message=message, severity=severity)


def _normalize_key(rule_key: str) -> str:
    return rule_key[4:] if rule_key.startswith("mpf:") else rule_key


def _comment(rule: Any) -> str:
    return f'mpf:{_normalize_key(rule.rule_key)}'


def _require_int(value: object, name: str) -> int:
    try:
        out = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}_invalid") from exc
    if out <= 0:
        raise ValueError(f"{name}_invalid")
    return out


def _validate_backend_host(value: object) -> str:
    raw = str(value or "")
    ip = ipaddress.ip_address(raw)
    if ip.version != 4 or ip.is_loopback or ip.is_unspecified or ip.is_multicast or not ip.is_private:
        raise ValueError("backend_target_host_invalid")
    return raw


def _validate(plan: FirewallPlanResult) -> FirewallRestoreValidationResult:
    errors: list[FirewallPlanMessage] = []
    warnings: list[FirewallPlanMessage] = []
    if plan.apply_mode != "plan_only":
        errors.append(_message("invalid_apply_mode", f"expected plan_only, got {plan.apply_mode}"))
    if plan.runtime_change != "no":
        errors.append(_message("invalid_runtime_change", f"expected no, got {plan.runtime_change}"))
    if plan.errors:
        errors.append(_message("plan_has_errors", "plan contains errors; payload rendering blocked"))

    desired_chains = {(c.table, c.chain) for c in plan.chains}
    for c in plan.chains:
        if c.table not in _ALLOWED_TABLES:
            errors.append(_message("forbidden_table", f"managed chain table forbidden: {c.table}"))
        if not c.chain.startswith("MPF"):
            errors.append(_message("non_mpf_chain_managed", f"non-MPF chain rendered as managed: {c.chain}"))
    for key, count in Counter(r.rule_key for r in plan.rules).items():
        if count > 1:
            errors.append(_message("duplicate_rule_key", f"duplicate rendered rule key: {key}"))
    for r in plan.rules:
        if r.table not in _ALLOWED_TABLES:
            errors.append(_message("forbidden_table", f"rule {r.rule_key} table forbidden: {r.table}"))
        if (r.table, r.chain) not in desired_chains and r.chain.startswith("MPF"):
            # parent hook/prerequisite rules are rendered separately by Phase 11 delta logic.
            pass
        if not r.chain.startswith("MPF"):
            errors.append(_message("non_mpf_chain_rule", f"rule {r.rule_key} targets non-MPF chain {r.chain}"))
        if r.rule_kind not in _SUPPORTED_KINDS:
            errors.append(_message("unsupported_rule_kind", f"unsupported rule kind: {r.rule_kind}"))
        if r.rule_kind == "customer_nat_redirect" and not (r.table == "nat" and r.chain == "MPF_NAT_PRE"):
            errors.append(_message("nat_redirect_chain_invalid", f"customer_nat_redirect must be nat:MPF_NAT_PRE; got {r.table}:{r.chain}"))
        if r.rule_kind == "backend_guard" and not (r.table == "filter" and r.chain == "MPF_GUARD"):
            errors.append(_message("backend_guard_chain_invalid", f"backend_guard must be filter:MPF_GUARD; got {r.table}:{r.chain}"))
        if r.customer_key and r.customer_key.startswith("deleted"):
            errors.append(_message("deleted_customer_rule", f"rule {r.rule_key} appears to belong to deleted customer"))
        try:
            _render_rule_line(r)
        except Exception as exc:  # noqa: BLE001 - convert to validation error.
            errors.append(_message("typed_rule_incomplete", f"{r.rule_key}: {exc}"))
    return FirewallRestoreValidationResult(renderable=len(errors) == 0, warnings=warnings, errors=errors)


def _base(rule: Any) -> str:
    return f'-A {rule.chain} -p tcp --dport {_require_int(rule.customer_port or rule.match_json.get("port"), "customer_port")} -m comment --comment "{_comment(rule)}"'


def _render_rule_line(rule: Any) -> FirewallRestoreRule:
    kind = rule.rule_kind
    if kind not in _SUPPORTED_KINDS:
        raise ValueError(f"unsupported_rule_kind:{kind}")
    if kind in {"customer_pause_reject", "customer_expired_reject"}:
        line = f'# mpf:planned-only {kind} {rule.chain} --comment "{_comment(rule)}"'
    elif kind == "backend_guard":
        port = _require_int(rule.backend_port or rule.match_json.get("dest_port"), "backend_port")
        line = f'-A MPF_GUARD -p tcp --dport {port} -m addrtype ! --src-type LOCAL -m comment --comment "{_comment(rule)}" -j REJECT --reject-with tcp-reset'
    elif kind == "customer_dispatch":
        jump = str(rule.action_json.get("jump_chain") or f"MPFC_{rule.customer_port}")
        if not jump.startswith("MPFC_"):
            raise ValueError("dispatch_jump_invalid")
        line = f'{_base(rule)} -j {jump}'
    elif kind == "customer_whitelist_reject":
        line = f'{_base(rule)} -j REJECT --reject-with tcp-reset'
    elif kind == "customer_connlimit_reject":
        maxconn = _require_int(rule.match_json.get("connlimit_above"), "maxconn")
        line = f'{_base(rule)} -m connlimit --connlimit-above {maxconn} --connlimit-mask 32 -j REJECT --reject-with tcp-reset'
    elif kind == "customer_hashlimit_reject":
        rate = _require_int(rule.match_json.get("hashlimit_rate_per_min"), "rate_per_min")
        burst = _require_int(rule.match_json.get("hashlimit_burst"), "burst")
        mode = str(rule.match_json.get("hashlimit_mode") or "srcip")
        name = str(rule.match_json.get("hashlimit_name") or "")
        if mode != "srcip" or not name or len(name) > 31 or any(ch.isspace() for ch in name):
            raise ValueError("hashlimit_parameters_invalid")
        line = f'{_base(rule)} -m hashlimit --hashlimit-above {rate}/minute --hashlimit-burst {burst} --hashlimit-mode {mode} --hashlimit-name {name} -j REJECT --reject-with tcp-reset'
    elif kind == "customer_whitelist_allow":
        sources = rule.match_json.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError("whitelist_sources_missing")
        lines = []
        for source in sources:
            network = ipaddress.ip_network(str(source), strict=False)
            jump = str(rule.action_json.get("jump_chain") or f"MPFO_{rule.customer_port}")
            lines.append(f'{_base(rule)} -s {network} -j {jump}')
        line = "\n".join(lines)
    elif kind in {"customer_accounting_in", "customer_accounting_out"}:
        line = f'{_base(rule)} -j RETURN'
    elif kind == "customer_nat_redirect":
        host = _validate_backend_host(rule.action_json.get("target_backend_host"))
        port = _require_int(rule.action_json.get("target_backend_port") or rule.backend_port, "backend_port")
        line = f'{_base(rule)} -j DNAT --to-destination {host}:{port}'
    else:  # pragma: no cover
        raise ValueError(f"unsupported_rule_kind:{kind}")
    if "127.0.0.1" in line:
        raise ValueError("forbidden_rendered_rule")
    return FirewallRestoreRule(table=rule.table, chain=rule.chain, rule_key=rule.rule_key, line=line)


def render_restore_contract(plan: FirewallPlanResult) -> FirewallApplyContract:
    contract = FirewallApplyContract()
    validation = _validate(plan)
    contract.warnings.extend(plan.warnings)
    contract.warnings.extend(validation.warnings)
    contract.errors.extend(plan.errors)
    contract.errors.extend(validation.errors)
    contract.renderable = validation.renderable
    contract.applyable = validation.renderable and any(r.customer_key for r in plan.rules) and not any(r.rule_kind in {"customer_pause_reject", "customer_expired_reject"} for r in plan.rules)
    contract.iptables_restore_allowed = contract.applyable
    if not validation.renderable:
        return contract

    tables: dict[str, FirewallRestoreTable] = {"filter": FirewallRestoreTable(name="filter"), "nat": FirewallRestoreTable(name="nat")}
    for table_name in ("filter", "nat"):
        chains = sorted([c for c in plan.chains if c.table == table_name and c.chain.startswith("MPF")], key=lambda c: (c.order, c.chain))
        tables[table_name].chains = [FirewallRestoreChain(table=c.table, chain=c.chain) for c in chains]

    for rule in sorted(plan.rules, key=lambda r: (r.table, r.chain, r.priority, r.rule_key)):
        rendered = _render_rule_line(rule)
        for line in rendered.line.splitlines():
            tables[rendered.table].rules.append(FirewallRestoreRule(table=rendered.table, chain=rendered.chain, rule_key=rendered.rule_key, line=line))

    payload_lines: list[str] = []
    for tname in ("filter", "nat"):
        t = tables[tname]
        if not t.chains and not t.rules:
            continue
        payload_lines.append(f"*{t.name}")
        for c in t.chains:
            payload_lines.append(f":{c.chain} {c.policy} [0:0]")
        for r in t.rules:
            payload_lines.append(r.line)
        payload_lines.append("COMMIT")
    payload = "\n".join(payload_lines) + ("\n" if payload_lines else "")
    sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    contract.restore_payload = FirewallRestorePayload(payload=payload, payload_sha256=sha, payload_line_count=len(payload_lines), tables=[tables["filter"], tables["nat"]])
    return contract
