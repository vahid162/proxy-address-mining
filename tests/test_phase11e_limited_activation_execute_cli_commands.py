from __future__ import annotations
import json
from pathlib import Path
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from mpf.services import phase11e_limited_activation_execute_service,phase11e_limited_activation_rollback_execute_service,phase11e_limited_activation_post_evidence_collect_service
RUN=CliRunner()
def _common(tmp_path:Path):
 p=tmp_path/'x.json';p.write_text('{}');return str(p)
def test_new_cli_commands_write_out_json_without_duplicate_kwargs(monkeypatch,tmp_path):
 p=_common(tmp_path);out=tmp_path/'out.json'
 cases=[(['production','phase11e-limited-activation-execute','--expected-version','x','--limited-activation-decision-json',p,'--limited-activation-decision-json-sha256','x','--limited-activation-execution-package-json',p,'--limited-activation-execution-package-json-sha256','x','--limited-activation-rollback-package-json',p,'--limited-activation-rollback-package-json-sha256','x','--artifact-gate-json',p,'--artifact-gate-json-sha256','x','--operator','o','--reason','r'],phase11e_limited_activation_execute_service,'build_phase11e_limited_activation_execute_report'),(['production','phase11e-limited-activation-rollback-execute','--expected-version','x','--activation-execution-json',p,'--activation-execution-json-sha256','x','--limited-activation-rollback-package-json',p,'--limited-activation-rollback-package-json-sha256','x','--artifact-gate-json',p,'--artifact-gate-json-sha256','x','--operator','o','--reason','r'],phase11e_limited_activation_rollback_execute_service,'build_phase11e_limited_activation_rollback_execute_report'),(['production','phase11e-limited-activation-post-evidence-collect','--expected-version','x','--activation-execution-json',p,'--activation-execution-json-sha256','x','--artifact-gate-json',p,'--artifact-gate-json-sha256','x','--operator','o','--reason','r'],phase11e_limited_activation_post_evidence_collect_service,'build_phase11e_limited_activation_post_evidence_collect_report')]
 for args,module,name in cases:
  monkeypatch.setattr(module,name,lambda config,**kwargs:{'final_decision':'BLOCKED','blockers':['test']})
  result=RUN.invoke(app,[*args,'--out-json',str(out),'--output','json','--config','configs/mpf.example.yaml']);assert result.exit_code==0,result.stdout;assert json.loads(out.read_text())['final_decision']=='BLOCKED'

def _execute_args(tmp_path:Path):
 import hashlib
 scope={'candidate_customer_key':'limited-btc-001','lane':'btc','public_port':20101,'backend_target':'172.18.0.3:60010'}
 def add(name,payload,args):
  p=tmp_path/f'{name}.json';p.write_text(json.dumps(payload));args += [f'--{name.replace("_","-")}-json',str(p),f'--{name.replace("_","-")}-json-sha256',hashlib.sha256(p.read_bytes()).hexdigest()]
 args=['production','phase11e-limited-activation-execute','--expected-version',__import__('mpf').__version__]
 add('limited_activation_decision',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_DECISION_READY',**scope},args);add('limited_activation_execution_package',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_EXECUTION_PACKAGE_READY',**scope},args);add('limited_activation_rollback_package',{'final_decision':'PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY',**scope},args);add('artifact_gate',{'final_decision':'PASS_NO_CUSTOMER_ARTIFACTS','unknown_mpf_artifacts':[],'forbidden_public_runtime_exposure':False,'production_gates_remain_closed':True},args)
 return args+['--operator','op','--reason','r','--output','json','--config','configs/mpf.example.yaml']
def test_execute_cli_missing_confirmations_is_blocked_not_traceback(monkeypatch,tmp_path):
 from types import SimpleNamespace
 monkeypatch.setattr(phase11e_limited_activation_execute_service.customer_read_service,'list_customer_status',lambda *a,**k:SimpleNamespace(ok=True,customers=[]))
 result=RUN.invoke(app,_execute_args(tmp_path));assert result.exit_code==0,result.stdout;assert json.loads(result.stdout)['final_decision']=='BLOCKED'
def test_execute_cli_wrong_hash_is_blocked_not_traceback(monkeypatch,tmp_path):
 from types import SimpleNamespace
 monkeypatch.setattr(phase11e_limited_activation_execute_service.customer_read_service,'list_customer_status',lambda *a,**k:SimpleNamespace(ok=True,customers=[]))
 args=_execute_args(tmp_path);i=args.index('--artifact-gate-json-sha256');args[i+1]='wrong'
 result=RUN.invoke(app,args);assert result.exit_code==0,result.stdout;assert json.loads(result.stdout)['final_decision']=='BLOCKED'
