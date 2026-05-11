from __future__ import annotations

import hashlib

from mpf.domain.firewall import (
    FirewallLiveSnapshot,
    FirewallPlanMessage,
    FirewallRollbackArtifactContract,
    FirewallRollbackPayload,
    FirewallRollbackValidationResult,
)


def _message(code: str, message: str, severity: str = "error") -> FirewallPlanMessage:
    return FirewallPlanMessage(code=code, message=message, severity=severity)


def _validate_snapshot(snapshot: FirewallLiveSnapshot) -> FirewallRollbackValidationResult:
    errors: list[FirewallPlanMessage] = []
    if not snapshot.chains and not snapshot.rules:
        errors.append(_message("snapshot_empty", "offline snapshot contains no MPF chains/rules; rollback artifact cannot be rendered"))
    return FirewallRollbackValidationResult(renderable=len(errors) == 0, errors=errors)


def render_rollback_artifact_from_snapshot(snapshot: FirewallLiveSnapshot, source: str = "provided_snapshot") -> FirewallRollbackArtifactContract:
    contract = FirewallRollbackArtifactContract(source=source)
    validation = _validate_snapshot(snapshot)
    contract.renderable = validation.renderable
    contract.errors.extend(validation.errors)
    contract.warnings.extend(validation.warnings)
    if not validation.renderable:
        return contract

    grouped_chains: dict[str, set[str]] = {}
    for table, chain in snapshot.chains:
        grouped_chains.setdefault(table, set()).add(chain)
    for rule in snapshot.rules:
        grouped_chains.setdefault(rule.table, set()).add(rule.chain)

    lines: list[str] = ["# MPF rollback artifact only (offline, inspection-only)"]
    rule_count = 0
    for table in sorted(grouped_chains.keys()):
        lines.append(f"*{table}")
        for chain in sorted(grouped_chains[table]):
            lines.append(f":{chain} - [0:0]")
        table_rules = sorted(
            [r for r in snapshot.rules if r.table == table],
            key=lambda r: (r.chain, r.rule_key),
        )
        for rule in table_rules:
            if rule.raw_line:
                lines.append(rule.raw_line)
            else:
                lines.append(f"# rollback-preserved mpf-rule {rule.rule_key} chain={rule.chain} raw_line_missing")
            rule_count += 1
        lines.append("COMMIT")

    payload = "\n".join(lines) + "\n"
    payload_sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    source_hash = snapshot.source_snapshot_sha256 or hashlib.sha256(payload.encode("utf-8")).hexdigest()

    contract.source_snapshot_hash = source_hash
    contract.rollback_payload_sha256 = payload_sha
    contract.rollback_payload_line_count = len(lines)
    contract.rollback_payload = FirewallRollbackPayload(
        payload=payload,
        payload_sha256=payload_sha,
        payload_line_count=len(lines),
        source_snapshot_sha256=source_hash,
        table_count=len(grouped_chains),
        chain_count=sum(len(chains) for chains in grouped_chains.values()),
        rule_count=rule_count,
    )
    return contract
