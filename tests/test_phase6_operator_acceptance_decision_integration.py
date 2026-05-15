import json
from typer.testing import CliRunner

from mpf.interfaces.cli import app
from tests.test_smoke import example_config_path


def test_operator_acceptance_decision_cli_and_integrations() -> None:
    runner = CliRunner()
    h = runner.invoke(app, ['phase6', 'operator-acceptance-decision', '--config', str(example_config_path())])
    assert h.exit_code == 0
    j = runner.invoke(app, ['phase6', 'operator-acceptance-decision', '--config', str(example_config_path()), '--output', 'json'])
    assert j.exit_code == 0
    d = json.loads(j.stdout)
    assert d['component'] == 'phase6_operator_acceptance_decision'

    agr = runner.invoke(app, ['firewall', 'apply-gate-readiness', '--config', str(example_config_path()), '--output', 'json'])
    ad = json.loads(agr.stdout)
    assert 'phase6_operator_acceptance_decision_summary' in ad

    gr = runner.invoke(app, ['firewall', 'gate-review', '--config', str(example_config_path()), '--source', 'config-only', '--output', 'json'])
    gd = json.loads(gr.stdout)
    assert 'phase6_operator_acceptance_decision_summary' in gd['apply_gate_readiness_summary']
    assert gd['live_apply_allowed'] is False
