from __future__ import annotations

import getpass
import hashlib
import json
import re
import shlex
import shutil
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service, phase11_live_canary_evidence_collector_service
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence


def _run_filter_chain(port: int) -> tuple[list[str], str]:
    cmd = ["iptables", "-t", "filter", "-vnL", f"MPFC_{port}", "--line-numbers"]
    if shutil.which("iptables") is None:
        return [], "iptables filter chain unavailable"
    cp = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if cp.returncode != 0:
        return [], f"iptables filter chain nonzero:{cp.returncode}"
    return cp.stdout.splitlines(), " ".join(cmd)


def _extract_count(lines: list[str], customer_key: str, suffix: str) -> int | None:
    marker = f"mpf:{customer_key}:{suffix}"
    for ln in lines:
        if marker not in ln:
            continue
        parts = ln.split()
        if len(parts) < 3:
            continue
        try:
            return int(parts[1])
        except ValueError:
            return None
    return None


def build_phase11_canary_reject_counters_visibility_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, collect_live: bool = False) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    live_ev = Phase11CanaryAcceptanceEvidence()
    if collect_live:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(
            config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version
        )
        live_ev = Phase11CanaryAcceptanceEvidence.from_dict(live.get("evidence", {}))

    customers = customer_read_service.list_customer_status(config, include_deleted=False, limit=1000)
    active = customers.customers if customers.ok else []
    customer_db_visible = any(c.customer_key == customer_key and c.lane == lane and c.port == port for c in active)
    if not customer_db_visible:
        blockers.append("missing_canary_customer_db_visibility")
    if not live_ev.canary_nat_rule_present:
        blockers.append("missing_canary_nat_rule")
    if live_ev.canary_nat_rule_count != 1:
        blockers.append("canary_nat_rule_not_exactly_one")
    if live_ev.canary_nat_target and live_ev.canary_nat_target != "172.18.0.3:60010":
        blockers.append("canary_nat_target_mismatch")
    if not live_ev.no_extra_customer_nat_rules:
        blockers.append("extra_customer_nat_rules_present")
    if not live_ev.no_unexpected_mpf_firewall_references:
        blockers.append("unexpected_mpf_firewall_references")
    if not live_ev.proxy_doctor_ok:
        blockers.append("proxy_doctor_not_ok")

    capture_ts = datetime.now(UTC).isoformat()
    lines, src_query = _run_filter_chain(port) if collect_live else ([], "no-collect-live")
    connlimit = _extract_count(lines, customer_key, "customer_connlimit_reject")
    hashlimit = _extract_count(lines, customer_key, "customer_hashlimit_reject")
    pause_reject = _extract_count(lines, customer_key, "customer_pause_reject")
    block_reject = _extract_count(lines, customer_key, "customer_block_reject")

    counts_found = all(v is not None for v in (connlimit, hashlimit, pause_reject, block_reject))
    reject_ok = bool(collect_live and counts_found and not blockers)
    if not counts_found:
        blockers.append("missing_source_backed_canary_reject_counters")
    reject_ref = None
    if reject_ok:
        seed = f"{customer_key}:{lane}:{port}:{live_ev.canary_nat_target}:{connlimit}:{hashlimit}:{pause_reject}:{block_reject}"
        reject_ref = f"iptables_filter_counter:{customer_key}:{lane}:{port}:{hashlib.sha256(seed.encode()).hexdigest()[:12]}"

    total_reject = int((connlimit or 0) + (hashlimit or 0) + (pause_reject or 0) + (block_reject or 0))

    evidence = Phase11CanaryVisibilityEvidence(
        captured_at=capture_ts,
        captured_by=getpass.getuser(),
        evidence_source="live_source_backed_canary_reject_counters",
        evidence_reference=reject_ref,
        customer_key=customer_key,
        lane=lane,
        port=port,
        backend_target=live_ev.canary_nat_target,
        reject_visibility_ok=reject_ok,
        reject_reference=reject_ref,
        source_query_or_artifact=src_query,
    )

    final = "REJECT_COUNTERS_VISIBILITY_READY" if reject_ok else ("BLOCKED" if any(x in blockers for x in ["canary_nat_rule_not_exactly_one", "extra_customer_nat_rules_present", "unexpected_mpf_firewall_references"]) else "MISSING_REJECT_COUNTERS_VISIBILITY")

    return {
        "component": "phase11_canary_reject_counters_visibility",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "backend_target": live_ev.canary_nat_target,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "production_traffic_enabled": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "no_onboarding_authorized": True,
        "customer_db_visible": customer_db_visible,
        "canary_nat_rule_present": live_ev.canary_nat_rule_present,
        "canary_nat_rule_count": live_ev.canary_nat_rule_count,
        "canary_nat_target": live_ev.canary_nat_target,
        "no_extra_customer_nat_rules": live_ev.no_extra_customer_nat_rules,
        "no_unexpected_mpf_firewall_references": live_ev.no_unexpected_mpf_firewall_references,
        "proxy_doctor_ok": live_ev.proxy_doctor_ok,
        "reject_evidence": {
            "captured_at": capture_ts,
            "captured_by": getpass.getuser(),
            "evidence_source": "iptables_filter_counter" if counts_found else "missing_exact_reject_counter_source",
            "evidence_reference": reject_ref,
            "customer_key": customer_key,
            "lane": lane,
            "port": port,
            "backend_target": live_ev.canary_nat_target,
            "reject_visibility_ok": reject_ok,
            "reject_reference": reject_ref,
            "reject_counter_source": "MPFC_port_rule_comments",
            "connlimit_reject_count": int(connlimit or 0),
            "hashlimit_reject_count": int(hashlimit or 0),
            "pause_reject_count": int(pause_reject or 0),
            "block_reject_count": int(block_reject or 0),
            "total_reject_count": total_reject,
            "source_query_or_artifact": src_query,
        },
        "generated_evidence": asdict(evidence),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "missing_visibility_primitives": [] if reject_ok else ["reject_counters_visibility"],
        "next_required_step": "unique_workers_visibility" if reject_ok else "reject_counters_visibility",
        "final_decision": final,
    }


def write_reject_counters_evidence_json(*, report: dict[str, object], path: Path, overwrite: bool = False) -> None:
    if not path.parent.exists():
        raise ValueError("parent directory does not exist")
    if path.exists() and not overwrite:
        raise ValueError("evidence json path already exists; pass overwrite")
    obj = report.get("generated_evidence")
    if not isinstance(obj, dict):
        raise ValueError("generated_evidence missing")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
