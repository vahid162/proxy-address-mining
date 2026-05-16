from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.abuse_dry_run_evaluator import *
from mpf.interfaces.cli import app
from mpf.services.phase8_abuse_dry_run_evaluator_service import build_phase8_abuse_dry_run_evaluator_report


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")



def _mk(state='normal', es='complete', hot=5, active=5, ips=1, workers=1):
    now = datetime(2026,1,1)
    return AbuseDryRunInput(AbusePolicySnapshot(10,3,100,10,20), AbuseEvidenceSnapshot(None,None,'s',1,active,hot,ips,workers,es,'synthetic',now,100,[]), AbuseStateSnapshot(state, now-timedelta(seconds=3600), now, now-timedelta(seconds=1000), None), now)


def test_domain_and_service_and_cli() -> None:
    assert evaluate_abuse_dry_run(_mk()).decision == 'stays_normal'
    assert evaluate_abuse_dry_run(_mk(hot=11)).decision == 'would_enter_over_tracking'
    assert evaluate_abuse_dry_run(_mk(ips=10)).would_harden is False
    assert evaluate_abuse_dry_run(_mk(workers=20)).would_harden is False
    assert evaluate_abuse_dry_run(_mk(es='missing',hot=None,active=None)).would_transition is False
    assert evaluate_abuse_dry_run(_mk(es='stale')).would_transition is False
    assert evaluate_abuse_dry_run(_mk(es='partial')).would_harden is False
    assert evaluate_abuse_dry_run(_mk(state='over_tracking',hot=11,active=11)).decision in {'continues_over_tracking','would_harden_after_sustained_miner_abuse'}
    assert evaluate_abuse_dry_run(_mk(state='hard')).decision == 'hard_requires_manual_unhard_future_gated'
    x = _mk(state='weird'); assert evaluate_abuse_dry_run(x).decision == 'evaluation_blocked_unknown_state'

    r = build_phase8_abuse_dry_run_evaluator_report(load_config(example_config_path()))
    assert r['component'] == 'phase8_abuse_dry_run_evaluator' and r['final_decision'] == 'BLOCKED'
    assert r['execution_allowed'] is False and r['phase8_acceptance_allowed'] is False and r['synthetic_scenarios_passed'] is True
    assert r['abuse_runner_authorized'] is False and r['abuse_automation_authorized'] is False and r['blockers'] == []

    runner = CliRunner()
    out = runner.invoke(app, ['phase8','abuse-dry-run-evaluator','--config',str(example_config_path())])
    assert out.exit_code == 0 and 'component: phase8_abuse_dry_run_evaluator' in out.stdout
    js = runner.invoke(app, ['phase8','abuse-dry-run-evaluator','--config',str(example_config_path()),'--output','json'])
    data = json.loads(js.stdout)
    assert data['final_decision'] == 'BLOCKED' and data['execution_allowed'] is False and data['blockers'] == []


def test_docs_and_safety_and_version() -> None:
    assert Path('VERSION').read_text().strip() == '0.1.113'
    assert '0.1.113' in Path('pyproject.toml').read_text() and '0.1.113' in Path('mpf/__init__.py').read_text()
    ps = Path('docs/PHASE_STATUS.md').read_text(); rp = Path('docs/REMAINING_PHASE_PLAN.md').read_text(); ai = Path('docs/AI_PHASE_8_TASK.md').read_text()
    assert 'current_accepted_phase: Phase 7' in ps and 'Phase 8 Abuse Dry-Run Evaluator Boundary' in ps and 'synced to 0.1.110' in ps
    assert 'synced to 0.1.111' not in ps and 'synced to 0.1.112' not in ps and 'synced to 0.1.113' not in ps
    assert 'synthetic/in-memory examples only' in ps and 'does not evaluate real customers' in ps and 'does not read live conntrack' in ps
    assert 'Current target is Phase 8 abuse dry-run evaluator package.' in rp and 'version after this PR is 0.1.113' in rp
    assert 'Current Phase 8 Step — Abuse Dry-Run Evaluator' in ai and 'transition_allowed=false' in ai
    for f in ['mpf/domain/abuse_dry_run_evaluator.py','mpf/services/phase8_abuse_dry_run_evaluator_service.py']:
        txt = Path(f).read_text().lower()
        for bad in ['subprocess.run','subprocess.popen','os.system','psycopg.connect','write_text','session.commit']:
            assert bad not in txt
