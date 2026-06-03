import hashlib,json
from types import SimpleNamespace
import pytest
from mpf import __version__
from mpf.services import phase11_final_acceptance_service as service
from tests.test_phase11_controlled_boundary_acceptance_decision_service import SCOPE,_package
from tests.test_phase11_final_acceptance_pr_readiness_service import _decision

def write(path,payload): path.write_text(json.dumps(payload)+'\n'); return str(path),hashlib.sha256(path.read_bytes()).hexdigest()
def readiness(): return {**SCOPE,'final_decision':'PHASE11_FINAL_ACCEPTANCE_PR_READINESS_READY','controlled_boundary_decision_ready':True,'controlled_boundary_package_ready':True,'final_acceptance_pr_ready':True,'proposed_next_current_accepted_phase':'Phase 11 — Production / Customer Activation Gate accepted on farm5','proposed_next_current_working_phase':'Phase 11 operational completion — Full CLI Production Operations','proposed_next_production_traffic':'controlled_cli_limited','proposed_next_firewall_apply_allowed':'controlled','proposed_next_abuse_automation_allowed':'controlled_operator_gated','proposed_next_phase12_start_allowed':'no','proposed_next_customer_onboarding_allowed':'controlled_cli_limited','proposed_next_worker_enforcement_allowed':'no','proposed_next_ui_allowed':'no','proposed_next_telegram_allowed':'no','blockers':[],'warnings':[]}
def run(tmp_path,rchange=None,dchange=None,pchange=None,bad_hash=False):
 r=readiness();r.update(rchange or {}); d=_decision();d.update(dchange or {}); p=_package();p.update(pchange or {})
 rp,rs=write(tmp_path/'r.json',r);dp,ds=write(tmp_path/'d.json',d);pp,ps=write(tmp_path/'p.json',p)
 kw={'expected_version':__version__,'final_acceptance_pr_readiness_json':rp,'final_acceptance_pr_readiness_json_sha256':'0'*64 if bad_hash else rs,'controlled_boundary_decision_json':dp,'controlled_boundary_decision_json_sha256':ds,'controlled_boundary_package_json':pp,'controlled_boundary_package_json_sha256':ps,'operator':'op','reason':'read-only'};kw.update({x:True for x in service.CONFIRMATIONS}); return service.build_phase11_final_acceptance_report(SimpleNamespace(),**kw)
def test_accepted_path(tmp_path):
 r=run(tmp_path); assert r['final_decision']=='PHASE11_FINAL_ACCEPTANCE_ACCEPTED'; assert r['phase11_accepted'] is True and r['phase12_accepted'] is False; assert r['worker_enforcement_allowed']==r['ui_allowed']==r['telegram_allowed']=='no'; assert r['stable_runtime_backend']=='127.0.0.1:60010'; assert r['abuse_automation_allowed']=='controlled_operator_gated'; assert r['phase12_start_allowed']=='no'; assert r['next_required_step']=='implement_controlled_abuse_operational_core'
@pytest.mark.parametrize('rc,dc,pc', [({'final_decision':'BLOCKED'},None,None),(None,{'final_decision':'BLOCKED'},None),(None,None,{'final_decision':'BLOCKED'}),({'candidate_customer_key':'wrong'},None,None)])
def test_blocked_inputs(tmp_path,rc,dc,pc): assert run(tmp_path,rc,dc,pc)['final_decision']=='BLOCKED'
def test_hash_mismatch(tmp_path): assert 'final_acceptance_pr_readiness_json_hash_mismatch' in run(tmp_path,bad_hash=True)['blockers']
