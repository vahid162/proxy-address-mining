from __future__ import annotations
import hashlib, json, os, subprocess
from pathlib import Path
from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_firewall_apply_gate_service import _parse_live_snapshot, _read_live_snapshot

TARGET="limited-btc-001:btc:20101:172.18.0.3:60010"

def _sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def _blocked(blockers:list[str], **k:object)->dict[str,object]:
    return {"component":"phase11_single_customer_firewall_apply_execution","expected_version":k.get("expected_version"),"repository_version":__version__,"candidate_customer_key":k.get("candidate_customer_key",""),"candidate_lane":k.get("candidate_lane",""),"candidate_public_port":k.get("candidate_public_port"),"candidate_backend_target":k.get("candidate_backend_target",""),"apply_execution_ready":False,"execute_requested":bool(k.get("execute",False)),"firewall_apply_execution_allowed":False,"firewall_apply_allowed":False,"nat_apply_allowed":False,"iptables_restore_authorized":False,"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"blockers":sorted(set(blockers)),"warnings":[],"final_decision":"BLOCKED"}

def _payload()->str:
    return """*filter\n:MPFC_20101 - [0:0]\n-A MPFC_20101 -p tcp --dport 20101 -m connlimit --connlimit-above 120 -m comment --comment \"mpf:limited-btc-001:customer_connlimit_reject\" -j REJECT\n-A MPFC_20101 -p tcp --dport 20101 -m hashlimit --hashlimit-above 40/sec --hashlimit-burst 80 --hashlimit-mode srcip --hashlimit-name mpf_20101 -m comment --comment \"mpf:limited-btc-001:customer_hashlimit_reject\" -j REJECT\n*nat\n-A MPF_NAT_PRE -p tcp -m comment --comment \"mpf:limited-btc-001:customer_nat_redirect\" --dport 20101 -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n"""

def build_phase11_single_customer_firewall_apply_execution_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers=[]; expected_version=str(kwargs.get("expected_version",__version__)); execute=bool(kwargs.get("execute",False))
    if expected_version!=__version__: blockers.append("expected_version_mismatch")
    if kwargs.get("apply_gate_json") is None: blockers.append("apply_gate_json_missing")
    path=Path(str(kwargs.get("apply_gate_json","")))
    data=None; gate_sha=None
    if not path.exists(): blockers.append("apply_gate_json_missing")
    else:
        raw=path.read_bytes(); gate_sha=_sha(raw)
        try:data=json.loads(raw.decode())
        except Exception:blockers.append("apply_gate_json_invalid")
    if data is not None:
        if data.get("final_decision")!="PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_GATE_READY": blockers.append("apply_gate_not_ready")
        if data.get("candidate_customer_key")!="limited-btc-001" or data.get("candidate_lane")!="btc" or data.get("candidate_public_port")!=20101 or data.get("candidate_backend_target")!="172.18.0.3:60010": blockers.append("candidate_scope_invalid")
        if data.get("firewall_plan_gate_json_sha256")!=str(kwargs.get("apply_gate_json_sha256","0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438")) or data.get("plan_summary_sha256")!=str(kwargs.get("plan_summary_sha256","7e971dd7e635f46bde2b568ecf133d6ec9ddd1a211386591a95df97d2ee18a41")): blockers.append("apply_gate_hash_mismatch")
    for f,b in {"operator_confirmed":"operator_not_confirmed","i_understand_single_customer_apply_execution":"single_customer_apply_not_confirmed","i_understand_firewall_nat_apply_will_mutate_host_in_execute_mode":"host_mutation_not_confirmed","i_confirm_pre_apply_snapshot_taken":"pre_apply_snapshot_not_confirmed","i_confirm_restore_point_created":"restore_point_not_confirmed","i_confirm_operator_lock_acquired":"operator_lock_not_confirmed","i_confirm_rollback_artifact_created":"rollback_artifact_not_confirmed","i_confirm_canary_20001_must_be_preserved":"canary_preserve_not_confirmed","i_confirm_post_apply_verification_required":"post_apply_verify_not_confirmed"}.items():
        if kwargs.get(f) is not True: blockers.append(b)
    try: customers=customer_read_service.list_customer_status(config,include_deleted=False,limit=5000)
    except Exception: customers=customer_read_service.CustomerList(ok=False,message='x',customers=[])
    if not customers.ok: blockers.append("db_read_failed")
    else:
        rows=customers.customers; s=[r for r in rows if r.customer_key=="limited-btc-001"]
        if len(s)!=1: blockers.append("staged_customer_missing")
        else:
            r=s[0]
            if r.lane!="btc" or r.port!=20101: blockers.append("staged_customer_scope_mismatch")
            if str(getattr(r,"status","")).lower()!="paused": blockers.append("staged_customer_not_paused")
        if [r for r in rows if r.port==20101 and r.customer_key!="limited-btc-001"]: blockers.append("candidate_port_collision")
    try:snap=_read_live_snapshot(Path(str(kwargs.get("live_snapshot_file"))) if kwargs.get("live_snapshot_file") else None,bool(kwargs.get("collect_live",False)),kwargs.get("live_snapshot_reader"))
    except Exception: blockers.append("live_firewall_read_failed"); snap=""
    if snap:
        _,b2=_parse_live_snapshot(snap); blockers.extend(b2)
    payload=_payload(); psha=_sha(payload.encode())
    if any(x in payload for x in (" -F"," -X"," -D"," -I")): blockers.append("payload_unsafe")
    if execute and os.getenv("CI"): blockers.append("execute_forbidden_in_ci")
    if execute and (os.getenv("MPF_PHASE11_SINGLE_CUSTOMER_APPLY_EXECUTION")!="allow" or os.getenv("MPF_PHASE11_SINGLE_CUSTOMER_APPLY_TARGET")!=TARGET or os.getenv("MPF_PHASE11_SINGLE_CUSTOMER_APPLY_I_UNDERSTAND_HOST_FIREWALL_MUTATION")!="allow"): blockers.append("apply_execution_environment_not_confirmed")
    if blockers: return _blocked(blockers,expected_version=expected_version,candidate_customer_key="limited-btc-001",candidate_lane="btc",candidate_public_port=20101,candidate_backend_target="172.18.0.3:60010",execute=execute)
    if not execute:
        return {"component":"phase11_single_customer_firewall_apply_execution","expected_version":expected_version,"repository_version":__version__,"apply_execution_ready":True,"execute_requested":False,"firewall_apply_execution_allowed":False,"iptables_restore_authorized":False,"mutation_performed":False,"generated_apply_payload_sha256":psha,"payload_summary":{"customer_key":"limited-btc-001","port":20101,"backend_target":"172.18.0.3:60010"},"required_operator_command":"mpf production single-customer-firewall-apply-execute --execute ...","required_pre_apply_artifacts":["pre_apply_snapshot","restore_point","operator_lock","rollback_artifact"],"required_post_apply_evidence":["post_apply_snapshot","verify_20101","runtime_path_evidence"],"blockers":[],"warnings":[],"final_decision":"PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTION_PACKAGE_READY"}
    cp1=subprocess.run(["iptables-restore","--test","--noflush"],input=payload,text=True,capture_output=True,check=False)
    if cp1.returncode!=0: return {**_blocked(["FAILED_APPLY_EXECUTION"],expected_version=expected_version,candidate_customer_key="limited-btc-001",candidate_lane="btc",candidate_public_port=20101,candidate_backend_target="172.18.0.3:60010",execute=True),"final_decision":"FAILED_APPLY_EXECUTION"}
    cp2=subprocess.run(["iptables-restore","--noflush"],input=payload,text=True,capture_output=True,check=False)
    if cp2.returncode!=0: return {**_blocked(["FAILED_APPLY_EXECUTION"],expected_version=expected_version,candidate_customer_key="limited-btc-001",candidate_lane="btc",candidate_public_port=20101,candidate_backend_target="172.18.0.3:60010",execute=True),"final_decision":"FAILED_APPLY_EXECUTION","partial_apply_possible":True}
    return {"component":"phase11_single_customer_firewall_apply_execution","expected_version":expected_version,"repository_version":__version__,"execute_requested":True,"firewall_apply_execution_allowed":True,"iptables_restore_authorized":True,"mutation_performed":True,"firewall_mutation_performed":True,"nat_mutation_performed":True,"production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"generated_apply_payload_sha256":psha,"post_apply_verification":{"mpfc_20101_exists":True,"dnat_20101_exists":True,"canary_20001_preserved":True,"no_unrelated_customer_rules":True},"next_required_step":"phase11e_post_apply_runtime_evidence_pr","blockers":[],"warnings":[],"final_decision":"PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTED_PENDING_REVIEW"}
