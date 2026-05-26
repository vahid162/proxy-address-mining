from __future__ import annotations
import hashlib,json
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def build_phase11e_limited_activation_execution_package_report(config: MPFConfig, **k: object)->dict[str,object]:
    del config; b=[]
    for c in ["operator_confirmed","i_understand_package_only","i_understand_no_activation_performed","i_understand_no_db_mutation","i_understand_no_firewall_apply","i_understand_no_production_traffic","i_understand_no_miner_traffic","i_understand_no_abuse_automation","i_understand_phase11_not_accepted"]:
        if k.get(c) is not True: b.append(f"missing_confirmation:{c}")
    p=Path(str(k.get('limited_activation_decision_json','')))
    try:d=json.loads(p.read_text())
    except Exception:d=None; b.append('decision_json_invalid')
    if d is not None and _sha(p)!=str(k.get('limited_activation_decision_json_sha256','')): b.append('decision_hash_mismatch')
    if isinstance(d,dict) and d.get('final_decision')!='PHASE11E_LIMITED_ACTIVATION_DECISION_READY': b.append('decision_not_ready')
    ready=not b
    ops=["mpf customer activate --customer-key limited-btc-001  # run only after operator review"]
    post=["mpf production phase11e-limited-activation-post-evidence --activation-execution-json <path> --activation-execution-json-sha256 <sha> --operator <op> --reason <reason> --operator-confirmed --i-understand-post-evidence-only --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-production-traffic-expansion --i-understand-no-miner-traffic-expansion --output json"]
    rb=["mpf production phase11e-limited-activation-rollback-package --expected-version {v} --limited-activation-decision-json <decision.json> --limited-activation-decision-json-sha256 <sha> --operator <op> --reason <reason> --operator-confirmed --i-understand-rollback-package-only --i-understand-no-rollback-performed --i-understand-no-db-mutation --i-understand-no-firewall-apply --output json".format(v=k.get('expected_version',__version__))]
    return {"component":"phase11e_limited_activation_execution_package","expected_version":str(k.get('expected_version',__version__)),"repository_version":__version__,"candidate_customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010","package_ready":ready,"activation_performed":False,"mutation_performed":False,"db_activation_allowed":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"abuse_automation_enabled":False,"phase11_accepted":False,"operator_commands":ops,"preflight_commands":["scripts/verify_current_phase_gate.sh"],"post_activation_evidence_commands":post,"rollback_commands":rb,"stop_conditions":["any blocker","public exposure","unknown artifacts"],"blockers":sorted(set(b)),"warnings":[],"next_required_step":"operator_review_then_controlled_activation" if ready else "fix_blockers_and_regenerate","final_decision":"PHASE11E_LIMITED_ACTIVATION_EXECUTION_PACKAGE_READY" if ready else "BLOCKED"}
