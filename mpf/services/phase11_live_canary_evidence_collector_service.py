from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field

from mpf.config import MPFConfig
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence
from mpf.services import proxy_doctor_service


@dataclass(slots=True)
class Phase11LiveCanaryEvidenceCollectorReport:
    component: str = "phase11_live_canary_evidence_collector"
    expected_version: str = ""
    farm5_baseline_version: str = ""
    customer_key: str = ""
    lane: str = ""
    public_port: int = 0
    mutation_performed: bool = False
    firewall_mutation_performed: bool = False
    nat_mutation_performed: bool = False
    conntrack_mutation_performed: bool = False
    docker_mutation_performed: bool = False
    db_mutation_performed: bool = False
    evidence: Phase11CanaryAcceptanceEvidence = field(default_factory=Phase11CanaryAcceptanceEvidence)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    commands_attempted: list[str] = field(default_factory=list)
    commands_unavailable: list[str] = field(default_factory=list)
    final_decision: str = "BLOCKED"

    def to_dict(self) -> dict[str, object]:
        out = asdict(self)
        out["evidence"] = asdict(self.evidence)
        return out


def _run_read_only(report: Phase11LiveCanaryEvidenceCollectorReport, cmd: list[str]) -> str | None:
    report.commands_attempted.append(" ".join(cmd))
    if shutil.which(cmd[0]) is None:
        report.commands_unavailable.append(cmd[0])
        report.warnings.append(f"command_unavailable:{cmd[0]}")
        return None
    try:
        cp = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except OSError as exc:
        report.warnings.append(f"command_failed:{cmd[0]}:{exc}")
        return None
    if cp.returncode != 0:
        report.warnings.append(f"command_nonzero:{cmd[0]}:{cp.returncode}")
        return None
    return cp.stdout


def _collect_nat(report: Phase11LiveCanaryEvidenceCollectorReport, customer_key: str, port: int) -> None:
    save_out = _run_read_only(report, ["iptables-save", "-t", "nat"])
    chain_out = _run_read_only(report, ["iptables", "-t", "nat", "-vnL", "MPF_NAT_PRE", "--line-numbers"])
    if save_out:
        ev = report.evidence
        ev.mpf_nat_pre_exists = ":MPF_NAT_PRE" in save_out
        ev.prerouting_hook_present = "-A PREROUTING -j MPF_NAT_PRE" in save_out
        rule_pat = re.compile(rf'-A MPF_NAT_PRE -p tcp --dport {port} -m comment --comment "mpf:{re.escape(customer_key)}:customer_nat_redirect" -j DNAT --to-destination ([^\s]+)')
        matches = rule_pat.findall(save_out)
        ev.canary_nat_rule_count = len(matches)
        ev.canary_nat_rule_present = len(matches) > 0
        ev.canary_nat_target = matches[0] if matches else None
        customer_rules = re.findall(r'--comment "mpf:[^\"]+:customer_nat_redirect"', save_out)
        ev.no_extra_customer_nat_rules = len(customer_rules) == 1 and ev.canary_nat_rule_count == 1
        unexpected_refs = [ln for ln in save_out.splitlines() if "mpf:" in ln and "customer_nat_redirect" not in ln and "MPF_NAT_PRE" not in ln]
        ev.no_unexpected_mpf_firewall_references = len(unexpected_refs) == 0
    if chain_out:
        m = re.search(r"\bDNAT\b.*mpf:" + re.escape(customer_key) + r":customer_nat_redirect.*\bto:([0-9.]+:[0-9]+)", chain_out)
        if m and not report.evidence.canary_nat_target:
            report.evidence.canary_nat_target = m.group(1)
        for line in chain_out.splitlines():
            if f"mpf:{customer_key}:customer_nat_redirect" in line:
                parts = line.split()
                if len(parts) > 2:
                    try:
                        report.evidence.nat_counter_packets = int(parts[1])
                        report.evidence.nat_counter_bytes = int(parts[2])
                    except ValueError:
                        pass


def _collect_conntrack(report: Phase11LiveCanaryEvidenceCollectorReport, port: int) -> None:
    out = _run_read_only(report, ["conntrack", "-L", "-p", "tcp"])
    if out is None:
        report.warnings.append("conntrack_unavailable")
        return
    report.evidence.conntrack_assured = any(("ASSURED" in ln and (f"dport={port}" in ln or "dport=60010" in ln)) for ln in out.splitlines())


def build_phase11_live_canary_evidence_collector_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str) -> dict[str, object]:
    _ = config
    report = Phase11LiveCanaryEvidenceCollectorReport(
        expected_version=expected_version,
        farm5_baseline_version=farm5_baseline_version,
        customer_key=customer_key,
        lane=lane,
        public_port=port,
    )
    _collect_nat(report, customer_key, port)
    _collect_conntrack(report, port)

    try:
        pdr = proxy_doctor_service.run()
        report.evidence.proxy_doctor_ok = pdr.final_verdict.value == "ok"
        statuses = {c.key: c.status.value for c in pdr.checks}
        report.evidence.bridge_healthy = statuses.get("runtime_containers_running") == "ok"
        report.evidence.bridge_reachable_from_forwarder = statuses.get("bridge_forwarder_reachability") == "ok"
        report.evidence.v2raya_ui_local_only = statuses.get("backend_listener_bind_address.v2raya_ui") == "ok"
        report.evidence.btc_backend_local_only = statuses.get("backend_listener_bind_address.btc_backend") == "ok"
        report.evidence.bridge_no_host_publish = statuses.get("backend_docker_publish_mode.v2raya_socks") == "ok"
        report.evidence.forwarder_uses_bridge_upstream = statuses.get("lane.btc.forwarder_upstream_socks") == "ok"
        report.evidence.direct_v2raya_20170_blocked = statuses.get("bridge_direct_20170_blocked") == "ok"
    except Exception as exc:  # fail-closed report-only
        report.warnings.append(f"proxy_doctor_unavailable:{exc}")

    if report.evidence.mpf_nat_pre_exists and report.evidence.prerouting_hook_present and report.evidence.canary_nat_rule_present:
        report.final_decision = "EVIDENCE_COLLECTED"
    elif report.commands_attempted:
        report.final_decision = "PARTIAL_EVIDENCE"
    else:
        report.final_decision = "BLOCKED"
    return report.to_dict()


def merge_phase11_evidence(base: Phase11CanaryAcceptanceEvidence, override: Phase11CanaryAcceptanceEvidence) -> Phase11CanaryAcceptanceEvidence:
    data = asdict(base)
    for key, value in asdict(override).items():
        if data.get(key) in (None, False, 0, "") and value not in (None, ""):
            data[key] = value
    return Phase11CanaryAcceptanceEvidence.from_dict(data)
