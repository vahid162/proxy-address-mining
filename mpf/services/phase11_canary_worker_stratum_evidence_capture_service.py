from __future__ import annotations

import getpass
import hashlib
import json
import socket
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service, phase11_live_canary_evidence_collector_service
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence


def _read_only_docker_logs(container: str, lines: int = 200) -> str:
    cp = subprocess.run(["docker", "logs", "--tail", str(lines), container], check=False, capture_output=True, text=True)
    if cp.returncode != 0:
        return ""
    return f"{cp.stdout}\n{cp.stderr}"


def _send_line(sock: socket.socket, payload: dict[str, object]) -> None:
    sock.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))


def _recv_json_line(sock: socket.socket) -> dict[str, object] | None:
    buf = b""
    while True:
        chunk = sock.recv(1)
        if not chunk:
            return None
        buf += chunk
        if chunk == b"\n":
            break
    try:
        return json.loads(buf.decode("utf-8", errors="replace").strip())
    except json.JSONDecodeError:
        return None


def build_phase11_canary_worker_stratum_evidence_capture_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, connect_host: str, connect_port: int, worker_name: str, timeout_seconds: int = 8, wait_notify_seconds: int = 8, collect_live: bool = False) -> dict[str, object]:
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

    probe_started_at = datetime.now(UTC).isoformat()
    subscribe_ok = False
    authorize_ok = False
    set_diff_seen = False
    notify_seen = False
    transcript: list[str] = []

    try:
        with socket.create_connection((connect_host, connect_port), timeout=float(timeout_seconds)) as sock:
            sock.settimeout(float(timeout_seconds))
            subscribe = {"id": 1, "method": "mining.subscribe", "params": ["mpf-phase11-probe/0.1"]}
            _send_line(sock, subscribe)
            transcript.append("tx:mining.subscribe")
            sub_resp = _recv_json_line(sock)
            transcript.append(f"rx_subscribe:{bool(sub_resp)}")
            subscribe_ok = bool(sub_resp and sub_resp.get("error") in (None, False) and sub_resp.get("result"))

            authorize = {"id": 2, "method": "mining.authorize", "params": [worker_name, "x"]}
            _send_line(sock, authorize)
            transcript.append("tx:mining.authorize")
            auth_resp = _recv_json_line(sock)
            transcript.append(f"rx_authorize:{bool(auth_resp)}")
            authorize_ok = bool(auth_resp and auth_resp.get("error") in (None, False) and auth_resp.get("result") is True)

            sock.settimeout(float(wait_notify_seconds))
            end = datetime.now(UTC).timestamp() + float(wait_notify_seconds)
            while datetime.now(UTC).timestamp() < end:
                try:
                    msg = _recv_json_line(sock)
                except socket.timeout:
                    break
                if not msg:
                    break
                m = msg.get("method")
                if m == "mining.set_difficulty":
                    set_diff_seen = True
                    transcript.append("rx:mining.set_difficulty")
                elif m == "mining.notify":
                    notify_seen = True
                    transcript.append("rx:mining.notify")
                else:
                    transcript.append("rx:other")
    except Exception as exc:  # noqa: BLE001
        blockers.append("stratum_probe_connection_or_protocol_failure")
        warnings.append(f"probe_error:{type(exc).__name__}")

    probe_finished_at = datetime.now(UTC).isoformat()
    if not subscribe_ok:
        blockers.append("missing_evidence:stratum_subscribe_ok")
    if not authorize_ok:
        blockers.append("missing_evidence:stratum_authorize_ok")
    if subscribe_ok and authorize_ok and not notify_seen:
        warnings.append("stratum_notify_not_seen_within_timeout")

    forwarder_pool_seen = False
    bridge_loopback_seen = False
    source_artifacts: list[str] = [f"socket:{connect_host}:{connect_port}"]
    if collect_live:
        fw_logs = _read_only_docker_logs("mpf-forwarder-btc")
        br_logs = _read_only_docker_logs("mpf-v2raya-socks-bridge")
        if worker_name in fw_logs and "bitcoin.viabtc.io:3333" in fw_logs:
            forwarder_pool_seen = True
            source_artifacts.append("docker_logs:mpf-forwarder-btc")
        else:
            warnings.append("forwarder_pool_seen_not_proven_from_source")
        if "127.0.0.1:20170" in br_logs:
            bridge_loopback_seen = True
            source_artifacts.append("docker_logs:mpf-v2raya-socks-bridge")
        else:
            warnings.append("bridge_loopback_seen_not_proven_from_source")

    transcript_hash = hashlib.sha256("\n".join(transcript).encode("utf-8")).hexdigest()[:16]
    worker_visibility_ok = bool(subscribe_ok and authorize_ok)
    worker_reference = f"live_canary_worker_stratum:{customer_key}:{lane}:{port}:{transcript_hash}" if worker_visibility_ok else None

    evidence = Phase11CanaryVisibilityEvidence(
        captured_at=probe_finished_at,
        captured_by=getpass.getuser(),
        evidence_source="live_source_backed_canary_worker_stratum",
        evidence_reference=worker_reference,
        customer_key=customer_key,
        lane=lane,
        port=port,
        backend_target=live_ev.canary_nat_target,
        worker_visibility_ok=worker_visibility_ok,
        worker_reference=worker_reference,
        stratum_subscribe_ok=subscribe_ok,
        stratum_authorize_ok=authorize_ok,
        stratum_set_difficulty_seen=set_diff_seen,
        stratum_notify_seen=notify_seen,
        forwarder_pool_seen=forwarder_pool_seen,
        bridge_loopback_seen=bridge_loopback_seen,
        source_query_or_artifact=",".join(source_artifacts),
    )

    return {
        "component": "phase11_canary_worker_stratum_evidence_capture",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "connect_host": connect_host,
        "connect_port": connect_port,
        "backend_target": live_ev.canary_nat_target,
        "probe_started_at": probe_started_at,
        "probe_finished_at": probe_finished_at,
        "transcript_hash": transcript_hash,
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
        "worker_evidence": {
            "worker_visibility_ok": worker_visibility_ok,
            "worker_reference": worker_reference,
            "unique_worker_count": 1 if worker_visibility_ok else 0,
            "unique_workers": [worker_name] if worker_visibility_ok else [],
            "stratum_subscribe_ok": subscribe_ok,
            "stratum_authorize_ok": authorize_ok,
            "stratum_set_difficulty_seen": set_diff_seen,
            "stratum_notify_seen": notify_seen,
            "forwarder_pool_seen": forwarder_pool_seen,
            "bridge_loopback_seen": bridge_loopback_seen,
            "evidence_source": "live_source_backed_canary_worker_stratum",
            "evidence_reference": worker_reference,
            "source_query_or_artifact": source_artifacts,
            "connect_host": connect_host,
            "connect_port": connect_port,
            "probe_started_at": probe_started_at,
            "probe_finished_at": probe_finished_at,
            "transcript_hash": transcript_hash,
        },
        "generated_evidence": asdict(evidence),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "final_decision": "WORKER_STRATUM_EVIDENCE_READY" if worker_visibility_ok else "BLOCKED",
    }


def write_worker_stratum_evidence_json(*, report: dict[str, object], path: Path, overwrite: bool = False) -> None:
    if not path.parent.exists():
        raise ValueError("parent directory does not exist")
    if path.exists() and not overwrite:
        raise ValueError("evidence json path already exists; pass overwrite")
    obj = report.get("generated_evidence")
    if not isinstance(obj, dict):
        raise ValueError("generated_evidence missing")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
