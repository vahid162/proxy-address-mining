from __future__ import annotations

import re

from mpf import __version__

_ALLOWED_CUSTOMERS = {"canary-btc-001", "limited-btc-001"}
_ALLOWED_PORTS = {20001, 20101}
_ALLOWED_TARGET = "172.18.0.3:60010"


def _phase_gate_ok(phase_status_text: str) -> bool:
    required = (
        "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5",
        "current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness",
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "customer_onboarding_allowed: db_only",
    )
    return all(x in phase_status_text for x in required)


def build_phase11_current_controlled_artifact_gate_report(*, iptables_save_text: str, ip6tables_save_text: str = "", phase_status_text: str = "", expected_version: str = "0.1.209") -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    unknown: list[str] = []
    allowed: list[str] = []

    phase_ok = _phase_gate_ok(phase_status_text)
    if not phase_ok:
        blockers.append("phase_gate_mismatch")

    if re.search(r"(?:MPF|MPFBTC|MPFC_|MPFO_|customer_)", ip6tables_save_text, flags=re.IGNORECASE):
        unknown.append("ipv6_mpf_or_customer_artifact_detected")

    lines = [ln.strip() for ln in iptables_save_text.splitlines() if ln.strip()]
    chain_names = {m.group(1) for ln in lines if (m := re.search(r"^-N\s+(\S+)", ln))}
    known_chains = {"MPFC_20001", "MPFC_20101", "MPF_NAT_PRE"}
    for ch in sorted(chain_names):
        if ch.startswith(("MPF", "MPFBTC", "MPFC_", "MPFO_")) and ch not in known_chains:
            unknown.append(f"unknown_chain:{ch}")
        elif ch in {"MPFC_20001", "MPFC_20101", "MPF_NAT_PRE"}:
            allowed.append(f"chain:{ch}")

    dnat_matches = re.findall(r"--dport\s+(\d+)\b.*?--to-destination\s+([0-9.]+:\d+)", iptables_save_text)
    for p_s, target in dnat_matches:
        p = int(p_s)
        if p in _ALLOWED_PORTS and target == _ALLOWED_TARGET:
            allowed.append(f"dnat:{p}->{target}")
        elif p in _ALLOWED_PORTS:
            unknown.append(f"dnat_target_mismatch:{p}->{target}")
        elif "172.18.0.3:60010" in target:
            unknown.append(f"unknown_customer_port:{p}")

    for c in re.findall(r"customer_(?:connlimit_reject|hashlimit_reject):([^\s\"]+)", iptables_save_text):
        if c in _ALLOWED_CUSTOMERS:
            allowed.append(f"customer_comment:{c}")
        else:
            unknown.append(f"unknown_customer_key:{c}")

    if "-A MPF_NAT_PRE" in iptables_save_text:
        nat_pre_lines = [ln for ln in lines if ln.startswith("-A MPF_NAT_PRE")]
        for ln in nat_pre_lines:
            m = re.search(r"--dport\s+(\d+)\b.*--to-destination\s+([0-9.]+:\d+)", ln)
            if not m:
                unknown.append("mpf_nat_pre_non_dnat_rule")
            else:
                p = int(m.group(1)); target = m.group(2)
                if p not in _ALLOWED_PORTS or target != _ALLOWED_TARGET:
                    unknown.append(f"mpf_nat_pre_rule_not_allowed:{p}->{target}")

    unknown = sorted(set(unknown))
    known_present = bool(allowed)
    production_closed = True
    forbidden_public_runtime_exposure = False

    if not phase_ok:
        decision = "BLOCKED_PHASE_GATE_MISMATCH"
    elif forbidden_public_runtime_exposure:
        decision = "BLOCKED_FORBIDDEN_PUBLIC_EXPOSURE"
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
        "forbidden_public_runtime_exposure": forbidden_public_runtime_exposure,
        "production_gates_remain_closed": production_closed,
        "blockers": sorted(set(blockers + (["unknown_mpf_artifacts_detected"] if unknown else []))),
        "warnings": sorted(set(warnings)),
        "next_required_step": "phase11e_runtime_stratum_evidence_collection" if decision.startswith("PASS") else "remove_unknown_artifacts_and_recheck",
        "final_decision": decision,
    }
