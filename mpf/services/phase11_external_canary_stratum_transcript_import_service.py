from __future__ import annotations

import getpass
import hashlib
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import phase11_live_canary_evidence_collector_service
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence

MAX_RAW_LEN = 512
MAX_MESSAGES = 64
ALLOWED_FARM5_BASELINE = "0.1.168"


def _bounded_raw(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value[:MAX_RAW_LEN]


def _norm_msg(msg: dict[str, object]) -> dict[str, object]:
    return {
        "direction": msg.get("direction"),
        "method": msg.get("method"),
        "id": msg.get("id"),
        "result_present": bool(msg.get("result_present")),
        "result_true": msg.get("result") is True,
        "error_is_null": bool(msg.get("error_is_null")),
        "worker_name": msg.get("worker_name"),
        "raw": _bounded_raw(msg.get("raw")),
    }


def _classify_forwarder_pool_seen(*, source_ip: str | None, source_port: int | None, forwarder_logs: str | None) -> bool:
    if not forwarder_logs or not source_ip or not source_port:
        return False
    endpoint = f"{source_ip}:{source_port}"
    backend_pat = re.compile(rf"{re.escape(endpoint)}.*172\.18\.0\.3:60010|172\.18\.0\.3:60010.*{re.escape(endpoint)}")
    pool_pat = re.compile(rf"{re.escape(endpoint)}.*bitcoin\.viabtc\.io:3333|bitcoin\.viabtc\.io:3333.*{re.escape(endpoint)}")
    has_backend = any(backend_pat.search(line) for line in forwarder_logs.splitlines())
    has_pool = any(pool_pat.search(line) for line in forwarder_logs.splitlines())
    return bool(has_backend and has_pool)


def build_phase11_external_canary_stratum_transcript_import_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, transcript_json: Path, collect_live: bool = False) -> dict[str, object]:
    raw_obj = json.loads(transcript_json.read_text(encoding="utf-8"))
    blockers: list[str] = []
    warnings: list[str] = []

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")
    if farm5_baseline_version != ALLOWED_FARM5_BASELINE:
        blockers.append("farm5_baseline_version_not_allowed")

    messages_raw = raw_obj.get("messages") if isinstance(raw_obj, dict) else None
    messages = [_norm_msg(m) for m in (messages_raw if isinstance(messages_raw, list) else [])[:MAX_MESSAGES] if isinstance(m, dict)]
    worker_name = raw_obj.get("worker_name") if isinstance(raw_obj, dict) else None
    connect_port = raw_obj.get("connect_port") if isinstance(raw_obj, dict) else None
    source_ip = raw_obj.get("source_ip_observed_by_operator") if isinstance(raw_obj, dict) else None
    source_port = raw_obj.get("source_port_observed_by_operator") if isinstance(raw_obj, dict) else None

    subscribe_ok = any(m.get("direction") == "rx" and bool(m.get("result_present")) and bool(m.get("error_is_null")) and m.get("id") == 1 for m in messages)
    authorize_ok = any(m.get("direction") == "rx" and bool(m.get("result_true")) and bool(m.get("error_is_null")) and m.get("id") == 2 for m in messages)
    set_diff_seen = any(m.get("direction") == "rx" and m.get("method") == "mining.set_difficulty" for m in messages)
    notify_seen = any(m.get("direction") == "rx" and m.get("method") == "mining.notify" for m in messages)

    norm = {
        "customer_key": customer_key, "lane": lane, "port": port, "connect_port": connect_port,
        "worker_name": worker_name, "source_ip": source_ip, "source_port": source_port, "messages": messages,
    }
    transcript_hash = hashlib.sha256(json.dumps(norm, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    worker_reference = f"external_canary_stratum:{customer_key}:{lane}:{port}:{transcript_hash}"

    scope_ok = customer_key == "canary-btc-001" and lane == "btc" and port == 20001 and connect_port == 20001 and worker_name == "canary-btc-001.worker-001"
    if not scope_ok:
        blockers.append("transcript_scope_mismatch")
    if not subscribe_ok:
        blockers.append("missing_evidence:stratum_subscribe_ok")
    if not authorize_ok:
        blockers.append("missing_evidence:stratum_authorize_ok")

    live_ev = Phase11CanaryAcceptanceEvidence()
    forwarder_pool_seen = False
    bridge_loopback_seen = False
    if collect_live:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(
            config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version
        )
        live_ev = Phase11CanaryAcceptanceEvidence.from_dict(live.get("evidence", {}))
        req_checks = {
            "canary_customer_db_visible": live_ev.canary_customer_db_visible,
            "canary_nat_rule_present": live_ev.canary_nat_rule_present,
            "canary_nat_rule_count_eq_1": live_ev.canary_nat_rule_count == 1,
            "canary_nat_target_present": bool(live_ev.canary_nat_target),
            "mpf_nat_pre_exists": live_ev.mpf_nat_pre_exists,
            "prerouting_hook_present": live_ev.prerouting_hook_present,
            "no_extra_customer_nat_rules": live_ev.no_extra_customer_nat_rules,
            "no_unexpected_mpf_firewall_references": live_ev.no_unexpected_mpf_firewall_references,
            "bridge_healthy": live_ev.bridge_healthy,
            "bridge_reachable_from_forwarder": live_ev.bridge_reachable_from_forwarder,
        }
        for k, ok in req_checks.items():
            if not ok:
                blockers.append(f"collect_live_check_failed:{k}")

        fw_logs = ""
        src = live.get("source_artifacts")
        if isinstance(src, dict):
            fw_logs = str(src.get("forwarder_logs", ""))
        forwarder_pool_seen = _classify_forwarder_pool_seen(
            source_ip=source_ip if isinstance(source_ip, str) else None,
            source_port=source_port if isinstance(source_port, int) else None,
            forwarder_logs=fw_logs,
        )
        bridge_loopback_seen = bool(live_ev.bridge_loopback_seen)

    ready = bool(scope_ok and subscribe_ok and authorize_ok and transcript_hash and worker_reference and not blockers)

    evidence = Phase11CanaryVisibilityEvidence(
        captured_at=str(raw_obj.get("captured_at") or datetime.now(UTC).isoformat()),
        captured_by=str(raw_obj.get("captured_by") or getpass.getuser()),
        evidence_source="live_source_backed_external_canary_stratum_transcript",
        evidence_reference=worker_reference,
        customer_key=customer_key,
        lane=lane,
        port=port,
        backend_target=live_ev.canary_nat_target,
        worker_visibility_ok=ready,
        worker_reference=worker_reference if ready else None,
        stratum_subscribe_ok=subscribe_ok,
        stratum_authorize_ok=authorize_ok,
        stratum_set_difficulty_seen=set_diff_seen,
        stratum_notify_seen=notify_seen,
        forwarder_pool_seen=forwarder_pool_seen,
        bridge_loopback_seen=bridge_loopback_seen,
        source_query_or_artifact=f"transcript_json:{transcript_json}",
    )

    return {
        "component": "phase11_external_canary_stratum_transcript_import",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "connect_host": raw_obj.get("connect_host"),
        "connect_port": connect_port,
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
            "worker_visibility_ok": ready,
            "worker_reference": evidence.worker_reference,
            "unique_worker_count": 1 if ready else 0,
            "unique_workers": [worker_name] if ready else [],
            "stratum_subscribe_ok": subscribe_ok,
            "stratum_authorize_ok": authorize_ok,
            "stratum_set_difficulty_seen": set_diff_seen,
            "stratum_notify_seen": notify_seen,
            "forwarder_pool_seen": forwarder_pool_seen,
            "bridge_loopback_seen": bridge_loopback_seen,
            "evidence_source": evidence.evidence_source,
            "evidence_reference": evidence.evidence_reference,
        },
        "generated_evidence": asdict(evidence),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "final_decision": "WORKER_STRATUM_EVIDENCE_READY" if ready else "BLOCKED",
    }


def write_external_stratum_transcript_evidence_json(*, report: dict[str, object], path: Path, overwrite: bool = False) -> None:
    if not path.parent.exists():
        raise ValueError("parent directory does not exist")
    if path.exists() and not overwrite:
        raise ValueError("evidence json path already exists; pass overwrite")
    obj = report.get("generated_evidence")
    if not isinstance(obj, dict):
        raise ValueError("generated_evidence missing")
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
