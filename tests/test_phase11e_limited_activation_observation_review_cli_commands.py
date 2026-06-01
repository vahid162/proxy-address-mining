import json
from pathlib import Path
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from mpf.services import phase11e_limited_activation_observation_collect_service as obs, phase11e_limited_activation_acceptance_review_service as review
runner=CliRunner()
def _pairs(names,tmp_path):
 args=[]
 for name in names:
  p=tmp_path/f'{name}.json'; p.write_text('{}'); args += [f'--{name.replace("_","-")}-json',str(p),f'--{name.replace("_","-")}-json-sha256','x']
 return args
def test_commands_write_out_json(monkeypatch,tmp_path:Path):
 monkeypatch.setattr('mpf.interfaces.cli._load',lambda *_:object())
 cases=[('phase11e-limited-activation-observation-collect',obs,'build_phase11e_limited_activation_observation_collect_report',['activation_execution','post_activation_evidence','source_evidence','artifact_gate']),('phase11e-limited-activation-acceptance-review',review,'build_phase11e_limited_activation_acceptance_review_report',['activation_execution','post_activation_evidence','observation','limited_activation_rollback_package','artifact_gate'])]
 for command,module,name,inputs in cases:
  monkeypatch.setattr(module,name,lambda *a,**k:{'final_decision':'BLOCKED'})
  out=tmp_path/f'{command}.out.json'; args=['production',command,'--expected-version','x',*_pairs(inputs,tmp_path),'--operator','o','--reason','r','--out-json',str(out),'--output','json']
  result=runner.invoke(app,args); assert result.exit_code==0, result.stdout; assert json.loads(out.read_text())['final_decision']=='BLOCKED'
def test_cli_help_lists_new_commands():
 r=runner.invoke(app,['production','--help']); assert r.exit_code==0; assert 'phase11e-limited-activation-observation-collect' in r.stdout; assert 'phase11e-limited-activation-acceptance-review' in r.stdout
