from pathlib import Path
from mpf.config import load_config
from mpf.services.firewall_apply_gate_readiness_service import build_apply_gate_readiness_report
from pathlib import Path

def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")
from typer.testing import CliRunner
from mpf.interfaces.cli import app

def test_apply_gate_has_new_summaries():
    r=build_apply_gate_readiness_report(load_config(example_config_path()))
    assert 'no_customer_apply_package_summary' in r
    assert 'no_customer_apply_execution_acceptance_summary' in r
    assert r['final_decision']=='BLOCKED'

def test_gate_review_human_has_new_summaries():
    res=CliRunner().invoke(app,['firewall','gate-review','--config',str(example_config_path()),'--source','config-only'])
    assert 'no_customer_apply_package: summary' in res.output
    assert 'no_customer_apply_execution_acceptance: summary' in res.output

def test_static_safety_patterns_absent():
    for p in ['mpf/services/firewall_no_customer_apply_package_service.py','mpf/services/firewall_no_customer_apply_execution_acceptance_service.py']:
        t=Path(p).read_text().lower()
        for bad in ['subprocess.run','os.system','open(..., "w")','write_text','psycopg.connect','insert into','update','delete from','alembic','migration']:
            assert bad not in t


def test_remaining_plan_has_single_finite_path():
    txt=Path("docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md").read_text(encoding="utf-8")
    assert txt.count("## Finite Remaining Path")==1

def test_ai_phase6_task_mentions_new_commands_and_no_stale_target():
    txt=Path("docs/AI_PHASE_6_TASK.md").read_text(encoding="utf-8")
    assert "mpf firewall no-customer-apply-package" in txt
    assert "mpf firewall no-customer-apply-execution-acceptance" in txt
    assert "After PR #94" not in txt
    assert "Next planning target is Phase 6 Dedicated Apply Gate Proposal/Review." not in txt

def test_execution_acceptance_current_state_checks_server_state():
    from mpf.services import firewall_no_customer_apply_execution_acceptance_service as s
    txt=Path("mpf/services/firewall_no_customer_apply_execution_acceptance_service.py").read_text(encoding="utf-8")
    assert "server_state" in txt
    r=s.build_no_customer_apply_execution_acceptance_report(load_config(example_config_path()))
    items={x["item"] for x in r["execution_acceptance_checklist"]}
    assert "separate_operator_runtime_execution_approval_still_required" in items
