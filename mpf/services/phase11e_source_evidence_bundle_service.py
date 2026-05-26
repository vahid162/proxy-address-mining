from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig

EXPECTED={"customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}

def _sha(p: Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()

def _load_json(p: Path, miss: str, invalid: str, blockers: list[str]):
    if not p.exists() or not p.is_file(): blockers.append(miss); return None
    try: obj=json.loads(p.read_text(encoding='utf-8'))
    except Exception: blockers.append(invalid); return None
    if not isinstance(obj, dict): blockers.append(invalid); return None
    return obj

def build_phase11e_source_evidence_bundle_report(config: MPFConfig, **kwargs: object)->dict[str, object]:
    del config
    blockers=[]; warnings=[]
    for c in ["operator_confirmed","i_understand_read_only","i_understand_no_activation","i_understand_no_firewall_apply","i_understand_no_db_mutation","i_understand_no_restart","i_understand_no_abuse_automation"]:
        if kwargs.get(c) is not True: blockers.append(f"missing_confirmation:{c}")
    expected_version=str(kwargs.get("expected_version", __version__))
    vis_path=Path(str(kwargs.get("visibility_bundle_json","")))
    vis=_load_json(vis_path,"visibility_bundle_missing","visibility_bundle_invalid",blockers)
    vis_sha=str(kwargs.get("visibility_bundle_json_sha256",""))
    if vis is not None and _sha(vis_path)!=vis_sha: blockers.append("visibility_bundle_hash_mismatch")

    phase_status=kwargs.get("phase_status") if isinstance(kwargs.get("phase_status"), dict) else {}
    mpf_doctor=kwargs.get("mpf_doctor") if isinstance(kwargs.get("mpf_doctor"), dict) else {}
    db_status=kwargs.get("db_status") if isinstance(kwargs.get("db_status"), dict) else {}
    proxy_doctor=kwargs.get("proxy_doctor") if isinstance(kwargs.get("proxy_doctor"), dict) else {}
    lanes=kwargs.get("lanes") if isinstance(kwargs.get("lanes"), list) else []
    customers=kwargs.get("customers") if isinstance(kwargs.get("customers"), list) else []
    current_artifact=kwargs.get("current_controlled_artifact_gate") if isinstance(kwargs.get("current_controlled_artifact_gate"), dict) else {}

    if vis is not None:
        if vis.get("expected_version")!="0.1.218": blockers.append("unsupported_source_visibility_bundle_version")
        if vis.get("candidate_customer_key")!=EXPECTED["customer_key"] or vis.get("candidate_lane")!=EXPECTED["lane"] or vis.get("candidate_public_port")!=EXPECTED["public_port"] or vis.get("candidate_backend_target")!=EXPECTED["backend_target"]:
            blockers.append("visibility_bundle_scope_mismatch")
        for f in ("production_traffic_enabled","miner_traffic_allowed","phase11_accepted","db_activation_allowed","mutation_performed"):
            if vis.get(f) is not False: blockers.append("visibility_bundle_safety_boundary_open"); break

    if phase_status and phase_status.get("production_traffic") not in ("none", False): blockers.append("unsafe_phase_status_production_traffic")
    if current_artifact and current_artifact.get("unknown_mpf_artifacts") not in ([], None): blockers.append("unknown_mpf_artifacts")
    if current_artifact and current_artifact.get("production_gates_remain_closed") is not True: blockers.append("production_gates_not_closed")

    active=[c.get("customer_key") for c in customers if isinstance(c,dict) and c.get("is_active") is True and c.get("lane_enabled", True) is True]
    paused=[c.get("customer_key") for c in customers if isinstance(c,dict) and c.get("customer_key")==EXPECTED["customer_key"] and c.get("is_paused") is True]
    disabled=[l.get("lane") for l in lanes if isinstance(l,dict) and l.get("enabled") is False]

    ready=len(blockers)==0
    return {
      "component":"phase11e_source_evidence_bundle","expected_version":expected_version,"repository_version":__version__,
      "source_visibility_bundle_version":vis.get("expected_version") if isinstance(vis,dict) else None,
      "source_visibility_bundle_repository_version":vis.get("repository_version") if isinstance(vis,dict) else None,
      "candidate_customer_key":EXPECTED["customer_key"],"candidate_lane":EXPECTED["lane"],"candidate_public_port":EXPECTED["public_port"],"candidate_backend_target":EXPECTED["backend_target"],
      "visibility_bundle_sha256":vis_sha,"phase_status":phase_status,"mpf_doctor":mpf_doctor,"db_status":db_status,"proxy_doctor":proxy_doctor,
      "lanes":lanes,"customers":customers,"active_enabled_lane_customers":active,"paused_candidate_customers":paused,"disabled_lanes":disabled,
      "current_controlled_artifact_gate":current_artifact,
      "runtime_order_observations":kwargs.get("runtime_order_observations",{}),"exposure_observations":kwargs.get("exposure_observations",{}),"abuse_contract_observations":kwargs.get("abuse_contract_observations",{}),
      "source_files":kwargs.get("source_files",[]),"source_hashes":kwargs.get("source_hashes",{}),
      "production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False,
      "blockers":sorted(set(blockers)),"warnings":sorted(set(warnings)),"final_decision":"PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY" if ready else "BLOCKED"
    }
