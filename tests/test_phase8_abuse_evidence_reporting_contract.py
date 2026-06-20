import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase8_abuse_evidence_reporting_contract_service import build_phase8_abuse_evidence_reporting_contract_report


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase8_abuse_evidence_reporting_service_and_contract() -> None:
    r = build_phase8_abuse_evidence_reporting_contract_report(load_config(example_config_path()))
    assert r["component"] == "phase8_abuse_evidence_reporting_contract"
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False
    assert r["phase8_acceptance_allowed"] is False
    assert r["state_machine_contract_present"] is True
    assert r["state_machine_contract_fail_closed"] is True
    assert r["abuse_runner_authorized"] is False
    assert r["abuse_automation_authorized"] is False
    assert r["abuse_state_db_reads_authorized"] is False
    assert r["abuse_state_db_writes_authorized"] is False
    assert r["policy_event_db_reads_authorized"] is False
    assert r["policy_event_db_writes_authorized"] is False
    assert r["conntrack_live_read_authorized"] is False
    assert r["firewall_counter_live_read_authorized"] is False
    assert r["hard_block_authorized"] is False
    assert r["soft_block_authorized"] is False
    assert r["pause_automation_authorized"] is False
    assert r["blockers"] == ["readme_current_gate_aligned_missing_or_failed", "index_current_gate_aligned_missing_or_failed"]

    c = r["abuse_evidence_reporting_contract"]
    assert c["evidence_sources"]["allowed_in_this_pr"] == ["repository_docs", "static_contracts", "config_read_only"]
    assert "flow_sessions" in c["evidence_sources"]["allowed_future_sources"]
    assert "live_conntrack" in c["evidence_sources"]["forbidden_in_this_pr"]
    assert c["customer_evaluation_report_shape"]["transition_allowed_in_this_pr"] is False
    assert c["customer_evaluation_report_shape"]["hardening_allowed_in_this_pr"] is False
    assert c["coverage_report_shape"]["silent_skip_allowed"] is False
    assert c["missing_evidence_report_shape"]["missing_evidence_hardens"] is False
    assert c["failure_modes"]["farms_over_alone_does_not_harden"] is True
    assert c["failure_modes"]["worker_over_alone_does_not_harden"] is True


def test_phase8_abuse_evidence_reporting_cli_and_blockers() -> None:
    runner = CliRunner()
    human = runner.invoke(app, ["phase8", "abuse-evidence-reporting-contract", "--config", str(example_config_path())])
    assert human.exit_code == 0
    js = runner.invoke(app, ["phase8", "abuse-evidence-reporting-contract", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    j = json.loads(js.stdout)
    assert j["final_decision"] == "BLOCKED"
    assert j["execution_allowed"] is False
    assert j["abuse_runner_authorized"] is False
    assert j["abuse_state_db_reads_authorized"] is False
    assert j["conntrack_live_read_authorized"] is False
    assert j["hard_block_authorized"] is False
    assert j["soft_block_authorized"] is False
    assert j["pause_automation_authorized"] is False
    assert j["blockers"] == ["readme_current_gate_aligned_missing_or_failed", "index_current_gate_aligned_missing_or_failed"]

    cfg = load_config(example_config_path())
    cfg.firewall.apply_mode = "manual_apply"
    r1 = build_phase8_abuse_evidence_reporting_contract_report(cfg)
    assert "apply_mode_plan_only_missing_or_failed" in r1["blockers"]
    cfg = load_config(example_config_path())
    cfg.proxy.runtime_activation_allowed = True
    r2 = build_phase8_abuse_evidence_reporting_contract_report(cfg)
    assert "runtime_activation_disabled_missing_or_failed" in r2["blockers"]


def test_phase8_abuse_evidence_reporting_static_safety() -> None:
    text = Path("mpf/services/phase8_abuse_evidence_reporting_contract_service.py").read_text(encoding="utf-8").lower()
    banned = ["subprocess.run", "subprocess.popen", "os.system", "open(", "\"w\"", "write_text", "psycopg.connect", "insert into", "update", "delete from", "select ", "alembic", "migration", "create_engine", "session.add", "session.commit"]
    for b in banned:
        assert b not in text
