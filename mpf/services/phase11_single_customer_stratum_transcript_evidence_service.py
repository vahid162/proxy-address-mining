from __future__ import annotations

import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

EXPECTED = {
    "customer_key": "limited-btc-001",
    "lane": "btc",
    "public_port": 20101,
    "backend_target": "172.18.0.3:60010",
}


def _base(expected_version: str, customer_key: str, lane: str, port: int, backend_target: str | None) -> dict[str, object]:
    return {
        "component": "phase11_single_customer_stratum_transcript_evidence",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": customer_key,
        "candidate_lane": lane,
        "candidate_public_port": port,
        "candidate_backend_target": backend_target,
        "stratum_transcript_ready": False,
        "runtime_path_evidence_ready": False,
        "visibility_bundle_ready": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
    }


def build_phase11_single_customer_stratum_transcript_evidence_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    expected_version = str(kwargs.get("expected_version", __version__))
    customer_key = str(kwargs.get("candidate_customer_key", EXPECTED["customer_key"]))
    lane = str(kwargs.get("candidate_lane", EXPECTED["lane"]))
    port = int(kwargs.get("candidate_public_port", EXPECTED["public_port"]))
    backend_target = kwargs.get("candidate_backend_target")
    backend_target_str = str(backend_target) if backend_target is not None else None

    result = _base(expected_version, customer_key, lane, port, backend_target_str)

    if (customer_key, lane, port) != (EXPECTED["customer_key"], EXPECTED["lane"], EXPECTED["public_port"]):
        blockers.append("candidate_scope_mismatch")
    if backend_target_str not in (None, EXPECTED["backend_target"]):
        blockers.append("candidate_scope_mismatch")

    transcript_path = Path(str(kwargs.get("transcript_json", "")))
    if not transcript_path.exists() or not transcript_path.is_file():
        blockers.append("transcript_missing")
        payload: dict[str, object] | None = None
    else:
        try:
            loaded = json.loads(transcript_path.read_text(encoding="utf-8-sig"))
        except Exception:
            blockers.append("transcript_invalid")
            loaded = None
        if loaded is not None and not isinstance(loaded, dict):
            blockers.append("transcript_invalid")
            payload = None
        else:
            payload = loaded

    if payload is not None:
        connect_port = payload.get("connect_port")
        if connect_port != EXPECTED["public_port"]:
            blockers.append("transcript_port_mismatch")

        worker_name = payload.get("worker_name")
        operator_mapped_worker = payload.get("operator_mapped_worker")
        worker_ref = worker_name if isinstance(worker_name, str) and worker_name.strip() else operator_mapped_worker
        if not isinstance(worker_ref, str) or EXPECTED["customer_key"] not in worker_ref:
            blockers.append("transcript_worker_scope_mismatch")

        messages_raw = payload.get("messages")
        messages = messages_raw if isinstance(messages_raw, list) else []
        subscribe_ok = any(
            isinstance(m, dict)
            and m.get("direction") == "rx"
            and m.get("id") == 1
            and (m.get("result_present") is True or "result" in m)
            for m in messages
        )
        authorize_ok = any(
            isinstance(m, dict)
            and m.get("direction") == "rx"
            and m.get("id") == 2
            and (m.get("result") is True or m.get("result_true") is True)
            for m in messages
        )
        diff_or_notify = any(
            isinstance(m, dict)
            and m.get("direction") == "rx"
            and m.get("method") in {"mining.set_difficulty", "mining.notify"}
            for m in messages
        )

        if not subscribe_ok:
            blockers.append("missing_subscribe")
        if not authorize_ok:
            blockers.append("missing_authorize")
        if not diff_or_notify:
            blockers.append("missing_set_difficulty_or_notify")

    ready = len(blockers) == 0
    return {
        **result,
        "stratum_transcript_ready": ready,
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "final_decision": "PHASE11_SINGLE_CUSTOMER_STRATUM_TRANSCRIPT_EVIDENCE_READY" if ready else "BLOCKED",
    }
