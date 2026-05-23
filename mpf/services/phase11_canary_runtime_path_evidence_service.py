from __future__ import annotations

import getpass
import json
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


def _classify_conntrack(text: str, *, port: int, backend_target: str | None, source_ip: str | None, source_port: int | None) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    lines = [ln for ln in text.splitlines() if "tcp" in ln.lower()]
    if not lines:
        return False, ["generic_conntrack_line_not_enough"]
    assured = [ln for ln in lines if "ASSURED" in ln]
    if not assured:
        return False, ["missing_conntrack_assured_canary_flow"]
    for ln in assured:
        if f"dport={port}" not in ln and "dport=60010" not in ln:
            continue
        if backend_target and backend_target.split(":")[0] not in ln:
            blockers.append("conntrack_backend_target_mismatch")
            continue
        if source_ip and f"src={source_ip}" not in ln:
            blockers.append("conntrack_source_endpoint_mismatch")
            continue
        if source_port and f"sport={source_port}" not in ln:
            blockers.append("conntrack_source_endpoint_mismatch")
            continue
        return True, []
    return False, blockers or ["missing_conntrack_assured_canary_flow"]


def _classify_forwarder(text: str, *, source_ip: str | None, source_port: int | None, backend_target: str, pool_host: str, pool_port: int) -> tuple[bool, list[str]]:
    endpoint = f"{source_ip}:{source_port}" if source_ip and source_port else None
    if source_ip and not source_port:
        return False, ["forwarder_source_endpoint_mismatch"]
    if not text.strip():
        return False, ["forwarder_log_read_failed"]
    for ln in text.splitlines():
        has_backend = backend_target in ln
        has_pool = f"{pool_host}:{pool_port}" in ln
        has_endpoint = endpoint in ln if endpoint else False
        if has_backend and has_pool and (has_endpoint or endpoint is None):
            return True, []
    return False, ["missing_forwarder_pool_correlation"]


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

    c_ok, c_b = _classify_conntrack(conntrack_text, port=port, backend_target=backend_target, source_ip=source_ip if isinstance(source_ip, str) else None, source_port=int(source_port) if isinstance(source_port, int) else None)
    f_ok, f_b = _classify_forwarder(forwarder_text, source_ip=source_ip if isinstance(source_ip, str) else None, source_port=int(source_port) if isinstance(source_port, int) else None, backend_target=backend_target, pool_host=pool_host, pool_port=pool_port)
    b_ok, b_b = _classify_bridge(bridge_text, backend_target=backend_target, bridge_target=bridge_target)
    blockers.extend(c_b + f_b + b_b)

    ref = f"runtime_path:{customer_key}:{lane}:{port}:{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    ev = Phase11CanaryVisibilityEvidence(captured_at=datetime.now(UTC).isoformat(), captured_by=getpass.getuser(), evidence_source=ALLOWED_SOURCE, evidence_reference=ref, customer_key=customer_key, lane=lane, port=port, backend_target=backend_target, conntrack_assured=c_ok, forwarder_pool_seen=f_ok, bridge_loopback_seen=b_ok, source_query_or_artifact=",".join(source_parts))
    return {"component":"phase11_canary_runtime_path_evidence","expected_version":expected_version,"repository_version":__version__,"farm5_baseline_version":farm5_baseline_version,"customer_key":customer_key,"lane":lane,"public_port":port,"backend_target":backend_target,"mutation_performed":False,"db_mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"conntrack_mutation_performed":False,"docker_mutation_performed":False,"production_traffic_enabled":False,"phase11_accepted":False,"limited_onboarding_allowed":False,"no_onboarding_authorized":True,"generated_evidence":asdict(ev),"blockers":sorted(set(blockers)),"final_decision":"RUNTIME_PATH_EVIDENCE_READY" if (c_ok and f_ok and b_ok and not blockers) else "BLOCKED"}


def write_runtime_path_evidence_json(*, report: dict[str, object], path: Path, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise ValueError("evidence json path already exists; pass overwrite")
    obj = report.get("generated_evidence")
    if not isinstance(obj, dict):
        raise ValueError("generated_evidence missing")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
