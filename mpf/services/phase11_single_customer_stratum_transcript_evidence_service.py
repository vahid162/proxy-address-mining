from __future__ import annotations
import json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig

def build_phase11_single_customer_stratum_transcript_evidence_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    expected_version = str(kwargs.get("expected_version", "0.1.206"))
    p = Path(str(kwargs.get("transcript_json", "")))
    if not p.exists():
        blockers.append("transcript_missing")
        obj = {}
    else:
        obj = json.loads(p.read_text(encoding="utf-8-sig"))
    port = int(kwargs.get("candidate_public_port", 20101))
    customer_key = str(kwargs.get("candidate_customer_key", "limited-btc-001"))
    lane = str(kwargs.get("candidate_lane", "btc"))
    worker = obj.get("worker_name") if isinstance(obj, dict) else None
    connect_port = obj.get("connect_port") if isinstance(obj, dict) else None
    msgs = obj.get("messages", []) if isinstance(obj, dict) else []
    subscribe_ok = any(isinstance(m, dict) and m.get("id") == 1 and m.get("direction") == "rx" for m in msgs)
    authorize_ok = any(isinstance(m, dict) and m.get("id") == 2 and m.get("direction") == "rx" and (m.get("result") is True or m.get("result_true") is True) for m in msgs)
    diff_or_notify = any(isinstance(m, dict) and m.get("method") in {"mining.set_difficulty", "mining.notify"} for m in msgs)
    if connect_port != port: blockers.append("transcript_port_mismatch")
    if worker not in {"limited-btc-001.worker-001", None} and customer_key not in str(worker): blockers.append("transcript_worker_scope_mismatch")
    if not subscribe_ok: blockers.append("missing_subscribe")
    if not authorize_ok: blockers.append("missing_authorize")
    if not diff_or_notify: blockers.append("missing_set_difficulty_or_notify")
    ready = not blockers and customer_key=="limited-btc-001" and lane=="btc" and port==20101
    return {"component":"phase11_single_customer_stratum_transcript_evidence","expected_version":expected_version,"repository_version":__version__,"candidate_customer_key":customer_key,"candidate_lane":lane,"candidate_public_port":port,"stratum_transcript_ready":ready,"runtime_path_evidence_ready":False,"visibility_bundle_ready":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,"blockers":sorted(set(blockers if ready is False else [])),"warnings":[],"final_decision":"PHASE11_SINGLE_CUSTOMER_STRATUM_TRANSCRIPT_EVIDENCE_READY" if ready else "BLOCKED"}
