from __future__ import annotations

import hashlib
from collections import Counter

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


def _message(code: str, message: str, severity: str = "error") -> FirewallPlanMessage:
    return FirewallPlanMessage(code=code, message=message, severity=severity)


def _normalize_key(rule_key: str) -> str:
    return rule_key[4:] if rule_key.startswith("mpf:") else rule_key


def _validate(plan: FirewallPlanResult) -> FirewallRestoreValidationResult:
    errors: list[FirewallPlanMessage] = []
    warnings: list[FirewallPlanMessage] = []
    if plan.apply_mode != "plan_only":
        errors.append(_message("invalid_apply_mode", f"expected plan_only, got {plan.apply_mode}"))
    if plan.firewall_change != "planned_only":
        errors.append(_message("invalid_firewall_change", f"expected planned_only, got {plan.firewall_change}"))
    if plan.nat_change != "planned_only":
        errors.append(_message("invalid_nat_change", f"expected planned_only, got {plan.nat_change}"))
    if plan.runtime_change != "no":
        errors.append(_message("invalid_runtime_change", f"expected no, got {plan.runtime_change}"))
    if plan.errors:
        errors.append(_message("plan_has_errors", "plan contains errors; payload rendering blocked"))

    desired_chains = {(c.table, c.chain) for c in plan.chains}
    desired_chain_names = {c.chain for c in plan.chains}
    for r in plan.rules:
        if (r.table, r.chain) not in desired_chains:
            errors.append(_message("rule_chain_missing", f"rule {r.rule_key} references missing desired chain {r.table}:{r.chain}"))
        if not r.chain.startswith("MPF"):
            errors.append(_message("non_mpf_chain_rule", f"rule {r.rule_key} targets non-MPF chain {r.chain}"))

    for key, count in Counter([r.rule_key for r in plan.rules]).items():
        if count > 1:
            errors.append(_message("duplicate_rule_key", f"duplicate rendered rule key: {key}"))

    for r in plan.rules:
        if r.rule_kind == "customer_nat_redirect" and not (r.table == "nat" and r.chain == "MPF_NAT_PRE"):
            errors.append(_message("nat_redirect_chain_invalid", f"customer_nat_redirect must be nat:MPF_NAT_PRE; got {r.table}:{r.chain}"))
        if r.rule_kind == "backend_guard" and not (r.table == "filter" and r.chain == "MPF_GUARD"):
            errors.append(_message("backend_guard_chain_invalid", f"backend_guard must be filter:MPF_GUARD; got {r.table}:{r.chain}"))
        if r.customer_key and r.customer_key.startswith("deleted"):
            errors.append(_message("deleted_customer_rule", f"rule {r.rule_key} appears to belong to deleted customer"))

    for c in desired_chain_names:
        if not c.startswith("MPF"):
            errors.append(_message("non_mpf_chain_managed", f"non-MPF chain rendered as managed: {c}"))

    return FirewallRestoreValidationResult(renderable=len(errors) == 0, warnings=warnings, errors=errors)


def _render_rule_line(rule) -> FirewallRestoreRule:
    comment = f'--comment "mpf:{_normalize_key(rule.rule_key)}"'
    if rule.rule_kind == "customer_nat_redirect":
        target = int(rule.action_json.get("target_backend", 0))
        line = f"-A {rule.chain} -p tcp --dport {int(rule.match_json['port'])} -m comment {comment} -j DNAT --to-destination 127.0.0.1:{target}"
        return FirewallRestoreRule(table="nat", chain=rule.chain, rule_key=rule.rule_key, line=line)

    if rule.rule_kind in {"customer_pause_reject", "customer_expired_reject", "customer_whitelist_allow", "customer_connlimit_reject", "customer_hashlimit_reject", "customer_accounting_in", "customer_accounting_out", "customer_dispatch", "backend_guard"}:
        line = f"# mpf:planned-only {rule.rule_kind} {rule.chain} {comment}"
        return FirewallRestoreRule(table=rule.table, chain=rule.chain, rule_key=rule.rule_key, line=line, planned_only=True)

    line = f"# mpf:planned-only unsupported_kind={rule.rule_kind} {rule.chain} {comment}"
    return FirewallRestoreRule(table=rule.table, chain=rule.chain, rule_key=rule.rule_key, line=line, planned_only=True)


def render_restore_contract(plan: FirewallPlanResult) -> FirewallApplyContract:
    contract = FirewallApplyContract()
    validation = _validate(plan)
    contract.warnings.extend(plan.warnings)
    contract.warnings.extend(validation.warnings)
    contract.errors.extend(plan.errors)
    contract.errors.extend(validation.errors)
    contract.renderable = validation.renderable
    contract.applyable = validation.renderable
    if not validation.renderable:
        return contract

    tables: dict[str, FirewallRestoreTable] = {"filter": FirewallRestoreTable(name="filter"), "nat": FirewallRestoreTable(name="nat")}
    for table_name in ("filter", "nat"):
        chains = sorted([c for c in plan.chains if c.table == table_name and c.chain.startswith("MPF")], key=lambda c: (c.order, c.chain))
        tables[table_name].chains = [FirewallRestoreChain(table=c.table, chain=c.chain) for c in chains]

    sorted_rules = sorted(plan.rules, key=lambda r: (r.table, r.chain, r.priority, r.rule_key))
    for rule in sorted_rules:
        rendered = _render_rule_line(rule)
        tables[rendered.table].rules.append(rendered)

    payload_lines: list[str] = []
    for tname in ("filter", "nat"):
        t = tables[tname]
        payload_lines.append(f"*{t.name}")
        for c in t.chains:
            payload_lines.append(f":{c.chain} {c.policy} [0:0]")
        for r in t.rules:
            payload_lines.append(r.line)
        payload_lines.append("COMMIT")
    payload = "\n".join(payload_lines) + "\n"
    sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    contract.restore_payload = FirewallRestorePayload(payload=payload, payload_sha256=sha, payload_line_count=len(payload_lines), tables=[tables["filter"], tables["nat"]])
    return contract
