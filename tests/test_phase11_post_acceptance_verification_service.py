import hashlib,json
from types import SimpleNamespace
from mpf import __version__
from mpf.services import phase11_post_acceptance_verification_service as service

def write(path,payload): path.write_text(json.dumps(payload)+'\n'); return str(path),hashlib.sha256(path.read_bytes()).hexdigest()
def run(tmp_path,artifact=None):
 a={'final_decision':'PHASE11_FINAL_ACCEPTANCE_ACCEPTED','phase11_accepted':True}; g={'final_decision':'PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS','unknown_mpf_artifacts':[],'forbidden_public_runtime_exposure':False}; g.update(artifact or {})
 ap,ash=write(tmp_path/'a.json',a);gp,gsh=write(tmp_path/'g.json',g); kw={'expected_version':__version__,'final_acceptance_json':ap,'final_acceptance_json_sha256':ash,'artifact_gate_json':gp,'artifact_gate_json_sha256':gsh,'operator':'op','reason':'read-only'};kw.update({x:True for x in service.CONFIRMATIONS}); return service.build_phase11_post_acceptance_verification_report(SimpleNamespace(),**kw)
def test_ready_path(tmp_path):
 r=run(tmp_path); assert r['final_decision']=='PHASE11_POST_ACCEPTANCE_VERIFICATION_READY'; assert r['artifact_gate_passed'] is True
 for k in ('mutation_performed','db_mutation_performed','firewall_apply_performed','conntrack_flush_performed','docker_restart_performed','systemd_restart_performed'): assert r[k] is False
def test_blocks_unsafe_artifact(tmp_path): assert run(tmp_path,{'unknown_mpf_artifacts':['bad']})['final_decision']=='BLOCKED'
def test_blocks_wrong_phase(tmp_path,monkeypatch):
 monkeypatch.setattr(service,'validate_current_phase_gate',lambda blockers,requirements: blockers.append('current_phase_gate_open'))
 assert run(tmp_path)['final_decision']=='BLOCKED'
