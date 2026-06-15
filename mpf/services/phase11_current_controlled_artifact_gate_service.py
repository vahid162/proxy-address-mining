from __future__ import annotations

import re

from mpf import __version__
from mpf.services.phase11_controlled_artifact_taxonomy import (
    OFFICIAL_CONTROLLED_CHAINS,
    classify_controlled_artifact,
    is_mpf_like_chain,
)

_ALLOWED = {
    20001: {"customer": "canary-btc-001", "chain": "MPFC_20001", "out_chain": "MPFO_20001"},
    20101: {"customer": "limited-btc-001", "chain": "MPFC_20101", "out_chain": "MPFO_20101"},
}
_ALLOWED_CUSTOMERS = {v["customer"]: port for port, v in _ALLOWED.items()}
_ALLOWED_SUFFIXES = {
    "customer_dispatch",
    "customer_connlimit_reject",
    "customer_hashlimit_reject",
    "customer_accounting_in",
    "customer_accounting_out",
    "customer_whitelist_allow",
    "customer_whitelist_reject",
    "customer_nat_redirect",
}
_BACKEND_GUARD_RE = re.compile(r"^mpf:backend_guard:btc:60010$")
_HOOK_RE = re.compile(r"^mpf:hook:(nat_prerouting|filter_input|verified_user_forward_post_dnat:(backend_guard|accounting|customers))$")


def _phase_gate_ok(phase_status_text: str) -> bool:
    required = (
        "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5",
        "current_working_phase: Phase 11 operational completion — Full CLI Production Operations",
        "production_traffic: controlled_cli_limited",
        "firewall_apply_allowed: controlled",
        "abuse_automation_allowed: controlled_operator_gated",
        "customer_onboarding_allowed: controlled_cli_limited",
        "worker_enforcement_allowed: no",
        "ui_allowed: no",
        "telegram_allowed: no",
        "phase12_start_allowed: no",
    )
    return all(x in phase_status_text for x in required)


def _parse_chain_decl(line: str) -> str | None:
    m = re.search(r"^-N\s+(\S+)", line)
    if m:
        return m.group(1)
    m = re.search(r"^:(\S+)\s+-\s+\[\d+:\d+\]", line)
    return m.group(1) if m else None


def _parse_comment_text(line: str) -> str | None:
    m = re.search(r'--comment\s+"([^"]+)"', line)
    return m.group(1) if m else None


def _parse_customer_comment(comment: str | None) -> tuple[str, str] | None:
    m = re.match(r"^mpf:([^:]+):(customer_[a-z_]+)$", comment or "")
    return (m.group(1), m.group(2)) if m else None


def _dport(line: str) -> int | None:
    m = re.search(r"--dport\s+(\d+)\b", line)
    return int(m.group(1)) if m else None


def _target(line: str) -> str | None:
    m = re.search(r"--to-destination\s+([0-9.]+:\d+)", line)
    return m.group(1) if m else None


def _validate_rule(chain: str, line: str, expected_backend_target: str | None) -> tuple[list[str], list[str]]:
    unknown: list[str] = []
    allowed: list[str] = []
    comment = _parse_comment_text(line)
    classification = classify_controlled_artifact(chain=chain, comment=comment)
    if classification == "unknown_mpf_artifact":
        unknown.append(f"unknown_rule:{chain}:{comment or 'no_comment'}")
        return unknown, allowed
    if classification != "official_phase11_controlled_artifact" and any(token in line for token in ("MPF", "mpf:", "customer_")):
        unknown.append(f"unknown_rule:{chain}:{comment or 'no_comment'}")
        return unknown, allowed

    customer_comment = _parse_customer_comment(comment)
    port = _dport(line)
    if customer_comment:
        customer, suffix = customer_comment
        if customer not in _ALLOWED_CUSTOMERS:
            unknown.append(f"unknown_customer_key:{customer}")
            return unknown, allowed
        expected_port = _ALLOWED_CUSTOMERS[customer]
        if suffix not in _ALLOWED_SUFFIXES:
            unknown.append(f"unexpected_comment_suffix:{suffix}")
        if suffix == "customer_nat_redirect":
            if chain != "MPF_NAT_PRE" or "-j DNAT" not in line:
                unknown.append(f"nat_comment_in_unexpected_chain:{chain}")
            if port != expected_port:
                unknown.append(f"nat_port_mismatch:{customer}:{port}")
            target = _target(line)
            if expected_backend_target is None:
                unknown.append(f"dnat_target_unresolved:{expected_port}->{target or 'missing'}")
            elif target != expected_backend_target:
                unknown.append(f"dnat_target_mismatch:{expected_port}->{target or 'missing'}")
            if not unknown:
                allowed.append(f"dnat:{expected_port}->{target}")
        else:
            if port is not None and port not in {expected_port, 60010}:
                unknown.append(f"customer_port_mismatch:{customer}:{port}")
            expected_chains = {"MPF_CUSTOMERS", "MPF_ACCT_IN", "MPF_ACCT_OUT", _ALLOWED[expected_port]["chain"], _ALLOWED[expected_port]["out_chain"]}
            if chain not in expected_chains and not chain.startswith("MPFL_"):
                unknown.append(f"customer_rule_unexpected_chain:{customer}:{chain}")
            if not unknown:
                allowed.append(f"comment:{customer}:{suffix}")
        return unknown, allowed

    if comment:
        if _BACKEND_GUARD_RE.match(comment):
            if port not in {None, 60010}:
                unknown.append(f"backend_guard_port_mismatch:{port}")
            elif chain not in {"MPF_GUARD", "DOCKER-USER", "INPUT", "MPF_INPUT"}:
                unknown.append(f"backend_guard_unexpected_chain:{chain}")
            else:
                allowed.append(f"comment:{comment}")
            return unknown, allowed
        if _HOOK_RE.match(comment):
            allowed.append(f"comment:{comment}")
            return unknown, allowed
        if "mpf:" in comment or "customer_" in comment:
            unknown.append(f"unknown_comment:{comment}")
            return unknown, allowed

    if chain == "MPF_NAT_PRE" and ("-j DNAT" not in line or _target(line) is None):
        unknown.append("mpf_nat_pre_non_dnat_or_incomplete_rule")
    elif is_mpf_like_chain(chain):
        if chain in OFFICIAL_CONTROLLED_CHAINS:
            allowed.append(f"chain_ref:{chain}")
        else:
            unknown.append(f"unknown_chain_ref:{chain}")
    return unknown, allowed


def build_phase11_current_controlled_artifact_gate_report(*, iptables_save_text: str, ip6tables_save_text: str = "", phase_status_text: str = "", expected_version: str = __version__, expected_backend_target: str | None = None) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    unknown: list[str] = []
    allowed: list[str] = []

    phase_ok = _phase_gate_ok(phase_status_text)
    if not phase_ok:
        blockers.append("phase_gate_mismatch")
    if expected_version != __version__:
        blockers.append("wrong_expected_version")

    if re.search(r"(?:MPF|MPFBTC|MPFC_|MPFO_|\bmpf:|customer_)", ip6tables_save_text, flags=re.IGNORECASE):
        unknown.append("ipv6_mpf_or_customer_artifact_detected")

    lines = [ln.strip() for ln in iptables_save_text.splitlines() if ln.strip()]
    has_dnat = any("MPF_NAT_PRE" in ln and "-j DNAT" in ln and "--to-destination" in ln for ln in lines)
    if has_dnat and expected_backend_target is None:
        blockers.append("expected_backend_target_required")

    for ln in lines:
        ch = _parse_chain_decl(ln)
        if not ch:
            continue
        if is_mpf_like_chain(ch) and ch not in OFFICIAL_CONTROLLED_CHAINS:
            unknown.append(f"unknown_chain:{ch}")
        elif ch in OFFICIAL_CONTROLLED_CHAINS:
            allowed.append(f"chain:{ch}")

    for ln in lines:
        if not ln.startswith("-A "):
            continue
        cm = re.search(r"^-A\s+(\S+)", ln)
        if not cm:
            continue
        rule_unknown, rule_allowed = _validate_rule(cm.group(1), ln, expected_backend_target)
        unknown.extend(rule_unknown)
        allowed.extend(rule_allowed)

    unknown = sorted(set(unknown))
    known_present = bool(allowed)

    if not phase_ok or expected_version != __version__:
        decision = "BLOCKED_PHASE_GATE_MISMATCH"
    elif unknown:
        decision = "BLOCKED_UNKNOWN_MPF_ARTIFACTS"
    elif known_present:
        decision = "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS"
        warnings.append("known_controlled_phase11_artifacts_present")
    else:
        decision = "PASS_NO_CUSTOMER_ARTIFACTS"

    return {
        "component": "phase11_current_controlled_artifact_gate",
        "expected_version": expected_version,
        "repository_version": __version__,
        "expected_backend_target": expected_backend_target,
        "current_phase_gate_ok": phase_ok,
        "known_controlled_artifacts_present": known_present,
        "allowed_controlled_artifacts": sorted(set(allowed)),
        "unknown_mpf_artifacts": unknown,
        "forbidden_public_runtime_exposure": False,
        "production_gates_remain_closed": True,
        "blockers": sorted(set(blockers + (["unknown_mpf_artifacts_detected"] if unknown else []))),
        "warnings": sorted(set(warnings)),
        "next_required_step": "prepare_live_ready_controlled_artifact_reapply_package" if decision.startswith("PASS") else "remove_unknown_artifacts_and_recheck",
        "final_decision": decision,
    }
