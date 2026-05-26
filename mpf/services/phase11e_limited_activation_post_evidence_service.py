from __future__ import annotations
import hashlib,json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def _load(p:Path,b:list[str],m:str):
    try:return json.loads(p.read_text())
    except Exception:b.append(m);return None

def build_phase11e_limited_activation_post_evidence_report(config: MPFConfig, **k: object)->dict[str,object]:
    del config; b=[]
    for c in ["operator_confirmed","i_understand_post_evidence_only","i_understand_no_db_mutation","i_understand_no_firewall_apply","i_understand_no_production_traffic_expansion","i_understand_no_miner_traffic_expansion"]:
        if k.get(c) is not True: b.append(f"missing_confirmation:{c}")
    p=Path(str(k.get('activation_execution_json',''))); ex=_load(p,b,'activation_execution_missing_or_invalid')
    if ex is not None and _sha(p)!=str(k.get('activation_execution_json_sha256','')): b.append('activation_execution_hash_mismatch')
    if isinstance(ex,dict) and ex.get('candidate_customer_key')!='limited-btc-001': b.append('scope_mismatch')
    ready=not b
    return {"component":"phase11e_limited_activation_post_evidence","expected_version":str(k.get('expected_version',__version__)),"repository_version":__version__,"candidate_customer_key":"limited-btc-001","read_only":True,"mutation_performed":False,"blockers":sorted(set(b)),"warnings":[],"final_decision":"PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY" if ready else "BLOCKED"}
