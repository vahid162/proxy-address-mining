import hashlib, json
from types import SimpleNamespace
import pytest
from mpf import __version__
from mpf.services import phase11_controlled_boundary_acceptance_decision_service as service

SCOPE={"candidate_customer_key":"limited-btc-001","lane":"btc","public_port":20101,"backend_target":"172.18.0.3:60010"}
def _write(path,payload): path.write_text(json.dumps(payload)+"\n"); return str(path),hashlib.sha256(path.read_bytes()).hexdigest()
def _package(): return {**SCOPE,"final_decision":"PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY","limited_acceptance_decision_ready":True,"source_evidence_ready":True,"artifact_gate_passed":True,"abuse_readiness_ready":True,"restart_container_order_ready":True,"current_phase_gate_ok":True,"controlled_boundary_acceptance_package_ready":True,"controlled_boundary_acceptance_decision_pr_ready":True,"phase11_final_acceptance_allowed":False,"production_expansion_allowed":False,"miner_traffic_expansion_allowed":False,"abuse_automation_allowed":False,"ui_allowed":False,"telegram_allowed":False,"mutation_performed":False,"db_mutation_performed":False,"firewall_apply_performed":False,"conntrack_flush_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False,"phase11_accepted":False,"blockers":[],"warnings":[]}
def _run(tmp_path, changes=None, bad_hash=False):
 p=tmp_path/'package.json'; payload=_package(); payload.update(changes or {}); path,sha=_write(p,payload); kwargs={"expected_version":__version__,"controlled_boundary_package_json":path,"controlled_boundary_package_json_sha256":"0"*64 if bad_hash else sha,"operator":"operator","reason":"read-only"}; kwargs.update({name:True for name in service.CONFIRMATIONS}); service.validate_current_phase_gate=lambda blockers: None; return service.build_phase11_controlled_boundary_acceptance_decision_report(SimpleNamespace(),**kwargs)
def test_ready_path_keeps_all_dangerous_gates_closed(tmp_path):
 r=_run(tmp_path); assert r['final_decision']=='PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_DECISION_READY'; assert r['next_required_step']=='phase11_final_acceptance_pr_readiness'; assert r['phase11_final_acceptance_pr_readiness_allowed'] is True
 for key in ('phase11_final_acceptance_allowed','production_expansion_allowed','miner_traffic_expansion_allowed','abuse_automation_allowed','ui_allowed','telegram_allowed','mutation_performed','db_mutation_performed','firewall_apply_performed','conntrack_flush_performed','docker_restart_performed','systemd_restart_performed','phase11_accepted'): assert r[key] is False
@pytest.mark.parametrize('changes',[{'final_decision':'BLOCKED'},{'production_expansion_allowed':True},{'candidate_customer_key':'wrong'}])
def test_blocks_package_not_ready_open_flag_or_scope_mismatch(tmp_path,changes): assert _run(tmp_path,changes)['final_decision']=='BLOCKED'
def test_blocks_hash_mismatch(tmp_path): assert 'controlled_boundary_package_json_hash_mismatch' in _run(tmp_path,bad_hash=True)['blockers']
