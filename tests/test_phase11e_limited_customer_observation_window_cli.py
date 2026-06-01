import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from mpf.services import phase11e_limited_customer_observation_window_service as service
runner=CliRunner()
def test_cli_calls_service_and_writes_json(monkeypatch,tmp_path):
 seen={}; monkeypatch.setattr('mpf.interfaces.cli._load',lambda *_:object()); monkeypatch.setattr(service,'build_phase11e_limited_customer_observation_window_report',lambda *a,**k:seen.setdefault('report',{'final_decision':'BLOCKED'}))
 args=['production','phase11e-limited-customer-observation-window','--expected-version','x']
 for n in ('observation','acceptance-review','artifact-gate','source-evidence'): args += [f'--{n}-json','x',f'--{n}-json-sha256','x']
 out=tmp_path/'out.json'; args += ['--window-start','2026-06-01T00:00:00Z','--window-end','2026-06-01T00:00:01Z','--sample-interval-seconds','0','--min-samples','1','--operator','o','--reason','r','--out-json',str(out),'--output','json']
 r=runner.invoke(app,args); assert r.exit_code==0,r.stdout; assert json.loads(out.read_text())['final_decision']=='BLOCKED'; assert seen
