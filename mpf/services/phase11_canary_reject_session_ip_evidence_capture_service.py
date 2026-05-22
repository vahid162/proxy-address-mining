from __future__ import annotations

import getpass
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from ipaddress import ip_address
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service, phase11_live_canary_evidence_collector_service
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence


def _run_conntrack(port: int) -> tuple[list[str], str]:
    if shutil.which("conntrack") is None:
        return [], "conntrack -L unavailable"
    cp = subprocess.run(["conntrack", "-L", "-p", "tcp"], check=False, capture_output=True, text=True)
    if cp.returncode != 0:
        return [], f"conntrack -L nonzero:{cp.returncode}"
    scope_lines: list[str] = []
    for ln in cp.stdout.splitlines():
        # exact canary public port scope only (avoid broad backend:60010 matching)
        if f"dport={port}" in ln or f"sport={port}" in ln:
            scope_lines.append(ln)
    return scope_lines, "conntrack -L -p tcp"


def _parse_external_ips(lines: list[str]) -> list[str]:
    ips: set[str] = set()
    for ln in lines:
        m = re.search(r"\bsrc=([0-9a-fA-F:.]+)", ln)
        if not m:
            continue
        ip_s = m.group(1)
        try:
            ip_obj = ip_address(ip_s)
        except ValueError:
            continue
        # unique customer IPs should be external/public, not docker/internal/backends
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
            continue
        ips.add(ip_s)
    return sorted(ips)


def _has_hard_scope_blockers(blockers: list[str]) -> bool:
    return any(
        b in blockers
        for b in [
            "missing_canary_customer_db_visibility",
            "missing_canary_nat_rule",
            "canary_nat_rule_not_exactly_one",
            "extra_customer_nat_rules_present",
            "unexpected_mpf_firewall_references",
        ]
    )


def build_phase11_canary_reject_session_ip_evidence_capture_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, collect_live: bool = False) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    live_ev = Phase11CanaryAcceptanceEvidence()
    if collect_live:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(
            config,
            customer_key=customer_key,
            lane=lane,
            port=port,
            expected_version=expected_version,
            farm5_baseline_version=farm5_baseline_version,
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
    if not live_ev.no_extra_customer_nat_rules:
        blockers.append("extra_customer_nat_rules_present")
    if not live_ev.no_unexpected_mpf_firewall_references:
        blockers.append("unexpected_mpf_firewall_references")
    if not live_ev.proxy_doctor_ok:
        blockers.append("proxy_doctor_not_ok")

    capture_ts = datetime.now(UTC).isoformat()
    src_lines, src_query = _run_conntrack(port) if collect_live else ([], "no-collect-live")
    conntrack_query_ok = collect_live and src_query == "conntrack -L -p tcp"
    exact_scope_ok = conntrack_query_ok and not _has_hard_scope_blockers(blockers)

    recent_count = len(src_lines)
    active_count = sum(1 for ln in src_lines if "ESTABLISHED" in ln or "ASSURED" in ln)
    unique_ips = _parse_external_ips(src_lines)

    # Reject visibility must never be inferred from conntrack.
    reject_ok = False
    reject_source = "missing_exact_reject_counter_source"
    connlimit = 0
    hashlimit = 0
    pause_reject = 0
    block_reject = 0
    total_reject = 0
    blockers.append("missing_source_backed_canary_reject_counters")

    session_ok = exact_scope_ok
    ip_ok = exact_scope_ok
    if not session_ok:
        blockers.append("missing_source_backed_canary_sessions")
    if not ip_ok:
        blockers.append("missing_source_backed_canary_unique_ips")

    seed = f"{customer_key}:{lane}:{port}:{live_ev.canary_nat_target}:{capture_ts}:{recent_count}:{len(unique_ips)}"
    ref = hashlib.sha256(seed.encode()).hexdigest()[:12]
    e_ref = f"live_canary_reject_session_ip:{customer_key}:{lane}:{port}:{ref}"

    evidence = Phase11CanaryVisibilityEvidence(
        captured_at=capture_ts,
        captured_by=getpass.getuser(),
        evidence_source="live_source_backed_canary_reject_session_ip",
        evidence_reference=e_ref,
        customer_key=customer_key,
        lane=lane,
        port=port,
        backend_target=live_ev.canary_nat_target,
        reject_visibility_ok=reject_ok,
        reject_reference=None,
        session_visibility_ok=session_ok,
        session_reference=e_ref if session_ok else None,
        unique_ip_visibility_ok=ip_ok,
        unique_ip_reference=e_ref if ip_ok else None,
        source_query_or_artifact=src_query,
        total_connections=recent_count,
    )

    if reject_ok and session_ok and ip_ok:
        final = "REJECT_SESSION_IP_EVIDENCE_READY"
    elif any(x in blockers for x in ["canary_nat_rule_not_exactly_one", "extra_customer_nat_rules_present", "unexpected_mpf_firewall_references"]):
        final = "BLOCKED"
    elif session_ok or ip_ok:
        final = "PARTIAL_REJECT_SESSION_IP_EVIDENCE"
    else:
        final = "MISSING_REJECT_SESSION_IP_EVIDENCE"

    return {
        "component": "phase11_canary_reject_session_ip_evidence_capture",
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
            "evidence_source": reject_source,
            "evidence_reference": None,
            "customer_key": customer_key,
            "lane": lane,
            "port": port,
            "backend_target": live_ev.canary_nat_target,
            "reject_visibility_ok": reject_ok,
            "reject_reference": None,
            "reject_counter_source": reject_source,
            "connlimit_reject_count": connlimit,
            "hashlimit_reject_count": hashlimit,
            "pause_reject_count": pause_reject,
            "block_reject_count": block_reject,
            "total_reject_count": total_reject,
            "source_query_or_artifact": "none",
        },
        "session_ip_evidence": {
            "captured_at": capture_ts,
            "captured_by": getpass.getuser(),
            "evidence_source": "conntrack",
            "evidence_reference": e_ref,
            "customer_key": customer_key,
            "lane": lane,
            "port": port,
            "backend_target": live_ev.canary_nat_target,
            "session_visibility_ok": session_ok,
            "session_reference": e_ref if session_ok else None,
            "unique_ip_visibility_ok": ip_ok,
            "unique_ip_reference": e_ref if ip_ok else None,
            "active_session_count": active_count,
            "recent_session_count": recent_count,
            "unique_ip_count": len(unique_ips),
            "unique_ips": unique_ips,
            "source_query_or_artifact": src_query,
        },
        "generated_evidence": asdict(evidence),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "missing_visibility_primitives": [k for k, ok in [("reject_counters_visibility", reject_ok), ("active_recent_sessions_visibility", session_ok), ("unique_ips_visibility", ip_ok)] if not ok],
        "next_required_step": "unique_workers_visibility" if (reject_ok and session_ok and ip_ok) else ("reject_counters_visibility" if not reject_ok else ("active_recent_sessions_visibility" if not session_ok else "unique_ips_visibility")),
        "final_decision": final,
    }


def write_reject_session_ip_evidence_json(*, report: dict[str, object], path: Path, overwrite: bool = False) -> None:
    if not path.parent.exists():
        raise ValueError("parent directory does not exist")
    if path.exists() and not overwrite:
        raise ValueError("evidence json path already exists; pass overwrite")
    obj = report.get("generated_evidence")
    if not isinstance(obj, dict):
        raise ValueError("generated_evidence missing")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
