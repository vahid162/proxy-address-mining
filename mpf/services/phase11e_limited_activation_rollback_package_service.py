from __future__ import annotations
import hashlib,json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def build_phase11e_limited_activation_rollback_package_report(config: MPFConfig, **k: object)->dict[str,object]:
    del config; b=[]
    for c in ["operator_confirmed","i_understand_rollback_package_only","i_understand_no_rollback_performed","i_understand_no_db_mutation","i_understand_no_firewall_apply"]:
        if k.get(c) is not True: b.append(f"missing_confirmation:{c}")
    p=Path(str(k.get('limited_activation_decision_json','')))
    try:d=json.loads(p.read_text())
    except Exception:d=None; b.append('decision_json_invalid')
    if d is not None and _sha(p)!=str(k.get('limited_activation_decision_json_sha256','')): b.append('decision_hash_mismatch')
    if isinstance(d,dict) and d.get('final_decision')!='PHASE11E_LIMITED_ACTIVATION_DECISION_READY': b.append('decision_not_ready')
    ready=not b
    return {"component":"phase11e_limited_activation_rollback_package","expected_version":str(k.get('expected_version',__version__)),"repository_version":__version__,"candidate_customer_key":"limited-btc-001","rollback_plan":["verify limited-btc-001 status","pause limited-btc-001 if needed","verify canary-btc-001 preserved","verify no unknown artifacts","verify no public backend exposure","collect post-rollback evidence"],"mutation_performed":False,"blockers":sorted(set(b)),"warnings":[],"final_decision":"PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY" if ready else "BLOCKED"}
