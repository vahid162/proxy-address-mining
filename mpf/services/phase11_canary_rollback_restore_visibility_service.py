from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import phase11_live_canary_evidence_collector_service
from mpf.services.phase11_canary_acceptance_review_service import Phase11CanaryAcceptanceEvidence
ALLOWED_SOURCE='live_source_backed_canary_rollback_restore_plan'

def build_phase11_canary_rollback_restore_visibility_report(config:MPFConfig,*,customer_key:str,lane:str,port:int,expected_version:str,farm5_baseline_version:str,collect_live:bool=False)->dict[str,object]:
    blockers=[]
    live=Phase11CanaryAcceptanceEvidence()
    if collect_live:
        live=Phase11CanaryAcceptanceEvidence.from_dict(phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(config,customer_key=customer_key,lane=lane,port=port,expected_version=expected_version,farm5_baseline_version=farm5_baseline_version).get('evidence',{}))
    if expected_version!=__version__: blockers.append('expected_version_mismatch')
    if (customer_key,lane,port)!=("canary-btc-001","btc",20001): blockers.append('canary_scope_mismatch')
    if not live.canary_nat_rule_present: blockers.append('missing_canary_nat_rule')
    if not live.mpf_nat_pre_exists: blockers.append('missing_mpf_nat_pre')
    if not live.prerouting_hook_present: blockers.append('missing_prerouting_hook')
    if not live.canary_nat_target or not live.canary_nat_target.endswith(':60010'): blockers.append('backend_target_mismatch')
    ok=not blockers
    ref=None
    if ok:
        h=hashlib.sha256(f'{customer_key}:{lane}:{port}:{live.canary_nat_target}'.encode()).hexdigest()[:12]
        ref=f'canary_rollback_restore_plan:{customer_key}:{lane}:{port}:{h}'
    return {"component":"phase11_canary_rollback_restore_visibility","expected_version":expected_version,"repository_version":__version__,"farm5_baseline_version":farm5_baseline_version,"customer_key":customer_key,"lane":lane,"public_port":port,"backend_target":live.canary_nat_target,"rollback_or_restore_plan_ok":ok,"rollback_reference":ref,"evidence_source":ALLOWED_SOURCE,"final_decision":"READY" if ok else "BLOCKED","restore_payload_renderer_present":ok,"restore_command_rendered_artifact_only":ok,"mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"conntrack_mutation_performed":False,"docker_mutation_performed":False,"db_mutation_performed":False,"blockers":sorted(set(blockers))}

def write_rollback_restore_visibility_evidence_json(*,report:dict[str,object],path:Path,overwrite:bool=False)->None:
    if path.exists() and not overwrite: raise FileExistsError(path)
    ev={"customer_key":report["customer_key"],"lane":report["lane"],"port":report["public_port"],"backend_target":report.get("backend_target"),"evidence_source":report["evidence_source"],"rollback_or_restore_plan_ok":report["rollback_or_restore_plan_ok"],"rollback_reference":report.get("rollback_reference"),"mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"conntrack_mutation_performed":False,"docker_mutation_performed":False,"db_mutation_performed":False}
    path.write_text(json.dumps(ev,indent=2),encoding='utf-8')
