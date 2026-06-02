import hashlib,json
from types import SimpleNamespace
import pytest
from mpf import __version__
from mpf.services import phase11_final_acceptance_pr_readiness_service as service
from tests.test_phase11_controlled_boundary_acceptance_decision_service import SCOPE,_package

def _write(path,payload): path.write_text(json.dumps(payload)+'\n'); return str(path),hashlib.sha256(path.read_bytes()).hexdigest()
def _decision(): return {**SCOPE,'final_decision':'PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_DECISION_READY','controlled_boundary_package_ready':True,'controlled_boundary_acceptance_decision_ready':True,'phase11_final_acceptance_pr_readiness_allowed':True,'phase11_final_acceptance_allowed':False,'production_expansion_allowed':False,'miner_traffic_expansion_allowed':False,'abuse_automation_allowed':False,'ui_allowed':False,'telegram_allowed':False,'mutation_performed':False,'db_mutation_performed':False,'firewall_apply_performed':False,'conntrack_flush_performed':False,'docker_restart_performed':False,'systemd_restart_performed':False,'phase11_accepted':False,'blockers':[],'warnings':[]}
def _run(tmp_path,decision_changes=None,package_changes=None):
 d=_decision(); d.update(decision_changes or {}); p=_package(); p.update(package_changes or {}); dp,ds=_write(tmp_path/'decision.json',d); pp,ps=_write(tmp_path/'package.json',p); kwargs={'expected_version':__version__,'controlled_boundary_decision_json':dp,'controlled_boundary_decision_json_sha256':ds,'controlled_boundary_package_json':pp,'controlled_boundary_package_json_sha256':ps,'operator':'operator','reason':'read-only'}; kwargs.update({name:True for name in service.CONFIRMATIONS}); service.validate_current_phase_gate=lambda blockers: None; return service.build_phase11_final_acceptance_pr_readiness_report(SimpleNamespace(),**kwargs)
def test_ready_path_proposes_later_controlled_transition_without_accepting(tmp_path):
 r=_run(tmp_path); assert r['final_decision']=='PHASE11_FINAL_ACCEPTANCE_PR_READINESS_READY'; assert r['next_required_step']=='phase11_final_acceptance_pr'; assert r['phase11_accepted'] is False; assert r['current_state_changed'] is False; assert r['proposed_next_production_traffic']=='controlled_cli_limited'; assert r['proposed_next_customer_onboarding_allowed']=='controlled_cli_limited'; assert r['proposed_next_worker_enforcement_allowed']=='no'
@pytest.mark.parametrize('decision_changes,package_changes',[({'final_decision':'BLOCKED'},None),(None,{'final_decision':'BLOCKED'}),(None,{'abuse_readiness_ready':False}),(None,{'restart_container_order_ready':False})])
def test_blocks_incomplete_inputs(tmp_path,decision_changes,package_changes): assert _run(tmp_path,decision_changes,package_changes)['final_decision']=='BLOCKED'
