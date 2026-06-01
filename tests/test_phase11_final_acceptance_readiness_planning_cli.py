import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from mpf.services import phase11_final_acceptance_readiness_planning_service as service
runner=CliRunner()
def test_cli_calls_service_and_writes_json(monkeypatch,tmp_path):
 seen={}; monkeypatch.setattr('mpf.interfaces.cli._load',lambda *_:object()); monkeypatch.setattr(service,'build_phase11_final_acceptance_readiness_planning_report',lambda *a,**k:seen.setdefault('report',{'final_decision':'BLOCKED'}))
 args=['production','phase11-final-acceptance-readiness-planning','--expected-version','x']
 for n in ('observation-window','acceptance-review','rollback-package','artifact-gate'): args += [f'--{n}-json','x',f'--{n}-json-sha256','x']
 out=tmp_path/'out.json'; args += ['--operator','o','--reason','r','--out-json',str(out),'--output','json']
 r=runner.invoke(app,args); assert r.exit_code==0,r.stdout; assert json.loads(out.read_text())['final_decision']=='BLOCKED'; assert seen
