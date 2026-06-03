from __future__ import annotations

import re

from mpf import __version__

_ALLOWED = {
    20001: {"customer": "canary-btc-001", "chain": "MPFC_20001"},
    20101: {"customer": "limited-btc-001", "chain": "MPFC_20101"},
}
_ALLOWED_CHAINS = {"MPFC_20001", "MPFC_20101", "MPF_NAT_PRE"}
_ALLOWED_TARGET = "172.18.0.3:60010"
_ALLOWED_SUFFIXES = {"customer_connlimit_reject", "customer_hashlimit_reject", "customer_nat_redirect"}


def _phase_gate_ok(phase_status_text: str) -> bool:
    pre = (
        "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5",
        "current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness",
        "production_traffic: none", "firewall_apply_allowed: no", "abuse_automation_allowed: no", "customer_onboarding_allowed: db_only",
    )
    post = (
        "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5",
        "current_working_phase: Phase 11 operational completion — Full CLI Production Operations",
        "production_traffic: controlled_cli_limited", "firewall_apply_allowed: controlled", "abuse_automation_allowed: controlled_operator_gated",
        "customer_onboarding_allowed: controlled_cli_limited", "worker_enforcement_allowed: no", "ui_allowed: no", "telegram_allowed: no",
        "phase12_start_allowed: no",
    )
    return all(x in phase_status_text for x in pre) or all(x in phase_status_text for x in post)


def _parse_chain_decl(line: str) -> str | None:
    m = re.search(r"^-N\s+(\S+)", line)
    if m:
        return m.group(1)
    m = re.search(r"^:(\S+)\s+-\s+\[\d+:\d+\]", line)
    return m.group(1) if m else None


def _parse_comment(line: str) -> tuple[str, str] | None:
    m = re.search(r'--comment\s+"mpf:([^:\"]+):(customer_[a-z_]+)"', line)
    if not m:
        return None
    return m.group(1), m.group(2)


def build_phase11_current_controlled_artifact_gate_report(*, iptables_save_text: str, ip6tables_save_text: str = "", phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
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

    for ln in lines:
        ch = _parse_chain_decl(ln)
        if not ch:
            continue
        if ch.startswith(("MPF", "MPFBTC", "MPFC_", "MPFO_")) and ch not in _ALLOWED_CHAINS:
            unknown.append(f"unknown_chain:{ch}")
        elif ch in _ALLOWED_CHAINS:
            allowed.append(f"chain:{ch}")

    for ln in lines:
        if not ln.startswith("-A "):
            continue
        cm = re.search(r"^-A\s+(\S+)", ln)
        if not cm:
            continue
        chain = cm.group(1)

        cmt = _parse_comment(ln)
        dport_m = re.search(r"--dport\s+(\d+)\b", ln)
        dport = int(dport_m.group(1)) if dport_m else None

        if chain in {"MPFC_20001", "MPFC_20101"}:
            expected_port = 20001 if chain == "MPFC_20001" else 20101
            exp = _ALLOWED[expected_port]
            if dport != expected_port:
                unknown.append(f"chain_port_mismatch:{chain}:{dport}")
            if cmt is None:
                unknown.append(f"missing_or_invalid_comment:{chain}")
            else:
                customer, suffix = cmt
                if suffix not in {"customer_connlimit_reject", "customer_hashlimit_reject"}:
                    unknown.append(f"unexpected_comment_suffix:{suffix}")
                if customer != exp["customer"]:
                    unknown.append(f"unknown_customer_key:{customer}")
                else:
                    allowed.append(f"comment:{customer}:{suffix}")

        if chain == "MPF_NAT_PRE":
            tm = re.search(r"--to-destination\s+([0-9.]+:\d+)", ln)
            if "-j DNAT" not in ln or not tm or dport is None:
                unknown.append("mpf_nat_pre_non_dnat_or_incomplete_rule")
                continue
            target = tm.group(1)
            if dport not in _ALLOWED:
                unknown.append(f"mpf_nat_pre_unknown_port:{dport}")
                continue
            exp = _ALLOWED[dport]
            if target != _ALLOWED_TARGET:
                unknown.append(f"dnat_target_mismatch:{dport}->{target}")
            if cmt is None:
                unknown.append("missing_or_invalid_nat_comment")
            else:
                customer, suffix = cmt
                if suffix != "customer_nat_redirect":
                    unknown.append(f"unexpected_comment_suffix:{suffix}")
                if customer != exp["customer"]:
                    unknown.append(f"unknown_customer_key:{customer}")
            if target == _ALLOWED_TARGET and cmt and cmt[0] == exp["customer"] and cmt[1] == "customer_nat_redirect":
                allowed.append(f"dnat:{dport}->{target}")

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
        "current_phase_gate_ok": phase_ok,
        "known_controlled_artifacts_present": known_present,
        "allowed_controlled_artifacts": sorted(set(allowed)),
        "unknown_mpf_artifacts": unknown,
        "forbidden_public_runtime_exposure": False,
        "production_gates_remain_closed": True,
        "blockers": sorted(set(blockers + (["unknown_mpf_artifacts_detected"] if unknown else []))),
        "warnings": sorted(set(warnings)),
        "next_required_step": "phase11e_runtime_stratum_evidence_collection" if decision.startswith("PASS") else "remove_unknown_artifacts_and_recheck",
        "final_decision": decision,
    }
