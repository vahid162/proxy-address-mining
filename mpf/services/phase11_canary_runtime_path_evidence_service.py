from __future__ import annotations

import getpass
import json
import ipaddress
import re
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import phase11_live_canary_evidence_collector_service
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence

ALLOWED_SOURCE = "live_source_backed_canary_runtime_path"


def _read_file(path: Path) -> tuple[bool, str]:
    try:
        return True, path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError):
        return False, ""


def _run(cmd: list[str]) -> tuple[bool, str]:
    try:
        cp = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except (FileNotFoundError, PermissionError, subprocess.SubprocessError, OSError):
        return False, ""
    if cp.returncode != 0:
        return False, ""
    return True, f"{cp.stdout}\n{cp.stderr}"


def _parse_conntrack_tuples(line: str) -> list[dict[str, str]]:
    tuples: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for token in line.split():
        if "=" not in token:
            continue
        k, v = token.split("=", 1)
        if k == "src" and current.get("src") is not None:
            tuples.append(current)
            current = {}
        if k in {"src", "dst", "sport", "dport"}:
            current[k] = v
    if current:
        tuples.append(current)
    return tuples[:2]


def _is_private_ip(ip: str | None) -> bool:
    if not ip:
        return False
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def _classify_conntrack(text: str, *, port: int, backend_target: str | None, source_ip: str | None, source_port: int | None) -> tuple[bool, list[str], dict[str, object]]:
    diagnostics: dict[str, object] = {
        "conntrack_log_lines_sampled": 0,
        "conntrack_assured_lines_sampled": 0,
        "conntrack_candidate_lines_sampled": 0,
        "conntrack_correlation_mode": "strict_source_match",
        "transcript_source_endpoint": f"{source_ip}:{source_port}" if source_ip and source_port else None,
        "conntrack_public_source_endpoint": None,
        "conntrack_public_dest_endpoint": None,
        "conntrack_backend_endpoint": None,
        "conntrack_transcript_endpoint_private": _is_private_ip(source_ip),
        "conntrack_source_endpoint_mismatch_tolerated": False,
        "conntrack_matched_line_sample": None,
    }
    lines = [ln for ln in text.splitlines() if "tcp" in ln.lower()]
    diagnostics["conntrack_log_lines_sampled"] = len(lines)
    if not lines:
        return False, ["generic_conntrack_line_not_enough"], diagnostics
    assured = [ln for ln in lines if "ASSURED" in ln]
    diagnostics["conntrack_assured_lines_sampled"] = len(assured)
    if not assured:
        return False, ["missing_conntrack_assured_canary_flow"], diagnostics

    backend_host, _, backend_port = (backend_target or "").rpartition(":")
    candidates: list[tuple[str, dict[str, str], dict[str, str]]] = []
    for ln in assured:
        tups = _parse_conntrack_tuples(ln)
        if len(tups) < 2:
            continue
        orig, reply = tups[0], tups[1]
        if orig.get("dport") != str(port):
            continue
        if backend_host and reply.get("src") != backend_host:
            continue
        if backend_port and reply.get("sport") != backend_port:
            continue
        candidates.append((ln, orig, reply))
    diagnostics["conntrack_candidate_lines_sampled"] = len(candidates)
    if not candidates:
        return False, ["missing_conntrack_assured_canary_flow"], diagnostics

    private_src = _is_private_ip(source_ip) and source_port is not None
    matched = None
    if source_ip and source_port is not None and not private_src:
        exact = [c for c in candidates if c[1].get("src") == source_ip and c[1].get("sport") == str(source_port)]
        if exact:
            matched = exact[0]
        elif len(candidates) == 1:
            matched = candidates[0]
            diagnostics["conntrack_source_endpoint_mismatch_tolerated"] = True
            diagnostics["conntrack_correlation_mode"] = "nat_aware_unique_public_port_backend"
        else:
            return False, ["ambiguous_conntrack_canary_flow"], diagnostics
    else:
        matched = candidates[0]
        if source_ip and source_port is not None:
            diagnostics["conntrack_source_endpoint_mismatch_tolerated"] = True
            diagnostics["conntrack_correlation_mode"] = "nat_aware_public_port_backend"

    ln, orig, reply = matched
    diagnostics["conntrack_public_source_endpoint"] = f"{orig.get('src')}:{orig.get('sport')}"
    diagnostics["conntrack_public_dest_endpoint"] = f"{orig.get('dst')}:{orig.get('dport')}"
    diagnostics["conntrack_backend_endpoint"] = f"{reply.get('src')}:{reply.get('sport')}"
    diagnostics["conntrack_matched_line_sample"] = ln[:240]
    return True, [], diagnostics


def _classify_forwarder(text: str, *, source_ip: str | None, source_port: int | None, backend_target: str, pool_host: str, pool_port: int) -> tuple[bool, list[str], dict[str, object]]:
    diagnostics: dict[str, object] = {
        "forwarder_log_lines_sampled": 0,
        "forwarder_pool_host_seen": False,
        "forwarder_backend_target_seen": False,
        "forwarder_endpoint_seen": False,
        "forwarder_backend_local_ports_sample": [],
        "forwarder_pool_local_ports_sample": [],
        "forwarder_matched_local_ports_sample": [],
        "forwarder_correlation_mode": "exact_same_line",
    }
    endpoint = f"{source_ip}:{source_port}" if source_ip and source_port else None
    if source_ip and not source_port:
        return False, ["forwarder_source_endpoint_mismatch"], diagnostics
    if not text.strip():
        return False, ["forwarder_log_read_failed"], diagnostics
    lines = text.splitlines()
    diagnostics["forwarder_log_lines_sampled"] = len(lines)
    backend_port = backend_target.rpartition(":")[2]
    backend_ports, pool_ports = set(), set()
    for ln in lines:
        has_pool = f"{pool_host}:{pool_port}" in ln
        has_backend = backend_target in ln or (backend_port and f"- 127.0.0.1:{backend_port}" in ln)
        has_endpoint = endpoint in ln if endpoint else False
        diagnostics["forwarder_pool_host_seen"] = bool(diagnostics["forwarder_pool_host_seen"] or has_pool)
        diagnostics["forwarder_backend_target_seen"] = bool(diagnostics["forwarder_backend_target_seen"] or has_backend)
        diagnostics["forwarder_endpoint_seen"] = bool(diagnostics["forwarder_endpoint_seen"] or has_endpoint)
        if has_backend and has_pool and (has_endpoint or endpoint is None):
            return True, [], diagnostics
        mb = re.search(r"127\.0\.0\.1:(\d+)\s+-\s+127\.0\.0\.1:" + re.escape(backend_port), ln) if backend_port else None
        if mb:
            backend_ports.add(mb.group(1))
        mp = re.search(r"127\.0\.0\.1:(\d+)\s+(<->|>-<)\s+" + re.escape(f"{pool_host}:{pool_port}"), ln)
        if mp:
            pool_ports.add(mp.group(1))
    matched = sorted(backend_ports & pool_ports)
    diagnostics["forwarder_backend_local_ports_sample"] = sorted(backend_ports)[:5]
    diagnostics["forwarder_pool_local_ports_sample"] = sorted(pool_ports)[:5]
    diagnostics["forwarder_matched_local_ports_sample"] = matched[:5]
    if matched:
        diagnostics["forwarder_correlation_mode"] = "multiline_local_ephemeral_port"
        return True, [], diagnostics
    if diagnostics["forwarder_pool_host_seen"] and diagnostics["forwarder_backend_target_seen"]:
        return False, ["forwarder_pool_and_backend_seen_without_correlation"], diagnostics
    return False, ["missing_forwarder_pool_correlation"], diagnostics


def _classify_bridge(text: str, *, backend_target: str, bridge_target: str) -> tuple[bool, list[str]]:
    if not text.strip():
        return False, ["bridge_log_read_failed"]
    for ln in text.splitlines():
        if bridge_target in ln and "127.0.0.1:20170" in ln and backend_target.split(":")[0] in ln:
            return True, []
    return False, ["missing_bridge_loopback_correlation"]


def build_phase11_canary_runtime_path_evidence_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    customer_key = str(kwargs["customer_key"]); lane = str(kwargs["lane"]); port = int(kwargs["port"])
    expected_version = str(kwargs["expected_version"]); farm5_baseline_version = str(kwargs["farm5_baseline_version"])
    source_ip = kwargs.get("source_ip"); source_port = kwargs.get("source_port")
    pool_host = str(kwargs["pool_host"]); pool_port = int(kwargs["pool_port"]); bridge_target = str(kwargs["bridge_target"])
    collect_live = bool(kwargs.get("collect_live", False))
    blockers: list[str] = []
    if not (customer_key == "canary-btc-001" and lane == "btc" and port == 20001 and expected_version == __version__ and farm5_baseline_version == "0.1.168"):
        blockers.append("runtime_path_scope_mismatch")

    backend_target = kwargs.get("backend_target")
    live = None
    if collect_live or not backend_target:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version)
        backend_target = backend_target or live.get("evidence", {}).get("canary_nat_target")
    backend_target = str(backend_target or "")

    conntrack_text = ""; forwarder_text = ""; bridge_text = ""; source_parts = []
    if kwargs.get("conntrack_file"):
        ok, conntrack_text = _read_file(Path(str(kwargs["conntrack_file"])))
        if not ok:
            blockers.append("conntrack_read_failed")
        source_parts.append(f"conntrack_file:{kwargs['conntrack_file']}")
    elif collect_live:
        ok, out = _run(["conntrack", "-L", "-p", "tcp"]); conntrack_text = out
        if not ok: blockers.append("conntrack_read_failed")
        source_parts.append("conntrack -L -p tcp")
    if kwargs.get("forwarder_log_file"):
        ok, forwarder_text = _read_file(Path(str(kwargs["forwarder_log_file"])))
        if not ok:
            blockers.append("forwarder_log_read_failed")
        source_parts.append(f"forwarder_log_file:{kwargs['forwarder_log_file']}")
    elif collect_live:
        ok, out = _run(["docker", "logs", "--tail", "300", "mpf-forwarder-btc"]); forwarder_text = out
        if not ok: blockers.append("forwarder_log_read_failed")
        source_parts.append("docker logs --tail 300 mpf-forwarder-btc")
    if kwargs.get("bridge_log_file"):
        ok, bridge_text = _read_file(Path(str(kwargs["bridge_log_file"])))
        if not ok:
            blockers.append("bridge_log_read_failed")
        source_parts.append(f"bridge_log_file:{kwargs['bridge_log_file']}")
    elif collect_live:
        ok, out = _run(["docker", "logs", "--tail", "300", "mpf-v2raya-socks-bridge"]); bridge_text = out
        if not ok: blockers.append("bridge_log_read_failed")
        source_parts.append("docker logs --tail 300 mpf-v2raya-socks-bridge")

    c_ok, c_b, c_diag = _classify_conntrack(conntrack_text, port=port, backend_target=backend_target, source_ip=source_ip if isinstance(source_ip, str) else None, source_port=int(source_port) if isinstance(source_port, int) else None)
    f_ok, f_b, f_diag = _classify_forwarder(forwarder_text, source_ip=source_ip if isinstance(source_ip, str) else None, source_port=int(source_port) if isinstance(source_port, int) else None, backend_target=backend_target, pool_host=pool_host, pool_port=pool_port)
    b_ok, b_b = _classify_bridge(bridge_text, backend_target=backend_target, bridge_target=bridge_target)
    blockers.extend(c_b + f_b + b_b)

    ref = f"runtime_path:{customer_key}:{lane}:{port}:{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    source_query = ",".join(source_parts)
    ev = Phase11CanaryVisibilityEvidence(captured_at=datetime.now(UTC).isoformat(), captured_by=getpass.getuser(), evidence_source=ALLOWED_SOURCE, evidence_reference=ref, customer_key=customer_key, lane=lane, port=port, backend_target=backend_target, conntrack_assured=c_ok, forwarder_pool_seen=f_ok, bridge_loopback_seen=b_ok, source_query_or_artifact=source_query)
    diagnostics = {**c_diag, **f_diag, "source_query_or_artifact": source_query}
    return {"component":"phase11_canary_runtime_path_evidence","expected_version":expected_version,"repository_version":__version__,"farm5_baseline_version":farm5_baseline_version,"customer_key":customer_key,"lane":lane,"public_port":port,"backend_target":backend_target,"mutation_performed":False,"db_mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"conntrack_mutation_performed":False,"docker_mutation_performed":False,"production_traffic_enabled":False,"phase11_accepted":False,"limited_onboarding_allowed":False,"no_onboarding_authorized":True,"generated_evidence":asdict(ev),"diagnostics":diagnostics,"blockers":sorted(set(blockers)),"final_decision":"RUNTIME_PATH_EVIDENCE_READY" if (c_ok and f_ok and b_ok and not blockers) else "BLOCKED"}


def write_runtime_path_evidence_json(*, report: dict[str, object], path: Path, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise ValueError("evidence json path already exists; pass overwrite")
    obj = report.get("generated_evidence")
    if not isinstance(obj, dict):
        raise ValueError("generated_evidence missing")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
