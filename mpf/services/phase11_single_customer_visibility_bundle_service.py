from __future__ import annotations
import json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig

def _load(p: Path | None):
    if p is None or not p.exists():
        return {}
    return json.loads(p.read_text(encoding='utf-8'))

def build_phase11_single_customer_visibility_bundle_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    runtime = _load(kwargs.get("runtime_path_evidence_json"))
    stratum = _load(kwargs.get("stratum_transcript_evidence_json"))
    blockers=[]
    if runtime.get("runtime_path_evidence_ready") is not True: blockers.append("runtime_path_evidence_not_ready")
    if stratum.get("stratum_transcript_ready") is not True: blockers.append("stratum_transcript_not_ready")
    ready = not blockers
    return {"component":"phase11_single_customer_visibility_bundle","expected_version":str(kwargs.get("expected_version","0.1.206")),"repository_version":__version__,"candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"usage_visibility_ready":ready,"reject_session_ip_worker_visibility_ready":ready,"post_apply_firewall_artifact_visibility_ready":runtime.get("post_apply_evidence_ready") is True,"rollback_readiness_reference_ready":True,"runtime_path_evidence_link":runtime.get("final_decision"),"stratum_transcript_link":stratum.get("final_decision"),"visibility_bundle_ready":ready,"abuse_1h_coverage_ready":False,"restart_container_order_ready":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,"next_required_step":"phase11e_abuse_restart_acceptance_pr" if ready else "none","blockers":blockers,"warnings":[],"final_decision":"PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY" if ready else "BLOCKED"}
