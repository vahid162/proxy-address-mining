import json
from typer.testing import CliRunner
from mpf.interfaces.cli import app
from mpf.services import phase11_final_acceptance_pr_readiness_service as service
runner=CliRunner()
def test_cli_calls_service_layer_and_writes_json(monkeypatch,tmp_path):
 seen={}; monkeypatch.setattr('mpf.interfaces.cli._load',lambda *_:object()); monkeypatch.setattr(service,'build_phase11_final_acceptance_pr_readiness_report',lambda *a,**k:seen.setdefault('report',{'final_decision':'BLOCKED'})); out=tmp_path/'out.json'; r=runner.invoke(app,['production','phase11-final-acceptance-pr-readiness','--expected-version','x','--controlled-boundary-decision-json','x','--controlled-boundary-decision-json-sha256','x','--controlled-boundary-package-json','x','--controlled-boundary-package-json-sha256','x','--operator','o','--reason','r','--out-json',str(out),'--output','json']); assert r.exit_code==0,r.stdout; assert json.loads(out.read_text())['final_decision']=='BLOCKED'; assert seen
