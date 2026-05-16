import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase8_abuse_state_machine_contract_service import (
    build_phase8_abuse_state_machine_contract_report,
)


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_phase8_abuse_state_machine_service_contract() -> None:
    r = build_phase8_abuse_state_machine_contract_report(load_config(example_config_path()))
    assert r["component"] == "phase8_abuse_state_machine_contract"
    assert r["phase"] == "Phase 8 — Abuse 1h Core"
    assert r["final_decision"] == "BLOCKED"
    assert r["contract_status"] == "ABUSE_STATE_MACHINE_CONTRACT_DEFINED_NOT_ACCEPTED"
    assert r["authorization_status"] == "PHASE8_ABUSE_STATE_MACHINE_REPORT_ONLY_RUNTIME_NOT_AUTHORIZED"
    assert r["execution_allowed"] is False
    assert r["phase8_acceptance_allowed"] is False
    assert r["abuse_state_machine_contract_defined"] is True
    assert r["abuse_state_path_defined"] is True
    assert r["abuse_transition_rules_defined"] is True
    assert r["abuse_timing_contract_defined"] is True
    assert r["abuse_hardening_contract_defined"] is True
    assert r["abuse_recovery_contract_defined"] is True
    assert r["abuse_exemption_contract_defined"] is True
    assert r["abuse_coverage_contract_defined"] is True
    assert r["abuse_runner_authorized"] is False
    assert r["abuse_automation_authorized"] is False
    assert r["abuse_state_db_writes_authorized"] is False
    assert r["abuse_event_db_writes_authorized"] is False
    assert r["hard_block_authorized"] is False
    assert r["soft_block_authorized"] is False
    assert r["pause_automation_authorized"] is False
    assert r["production_traffic_authorized"] is False
    assert r["firewall_apply_authorized"] is False
    assert r["customer_nat_authorized"] is False
    assert isinstance(r["blockers"], list)


def test_phase8_abuse_state_machine_service_content_and_cli() -> None:
    data = build_phase8_abuse_state_machine_contract_report(load_config(example_config_path()))
    c = data["abuse_state_machine_contract"]
    assert c["state_path"] == ["normal", "over_tracking", "over_grace", "hard"]
    assert c["sustained_abuse_seconds"] == 3600
    assert c["grace_seconds_default"] == 900
    assert c["hardening_basis"]["farms_over_alone_hardens"] is False
    assert c["hardening_basis"]["worker_over_alone_hardens"] is False
    assert c["coverage"]["all_active_customers_in_enabled_lanes_required"] is True
    assert c["coverage"]["silent_skip_allowed"] is False
    assert c["coverage"]["abuse_exempt_requires_reason"] is True
    assert c["coverage"]["abuse_exempt_requires_expiry"] is True
    assert c["hardening_requirements"]["evidence_required"] is True
    assert c["hardening_requirements"]["audit_event_required"] is True
    assert c["hardening_requirements"]["restore_reference_required"] is True
    assert c["hardening_requirements"]["firewall_apply_future_gated"] is True
    assert c["hardening_requirements"]["conntrack_flush_future_gated"] is True

    runner = CliRunner()
    human = runner.invoke(app, ["phase8", "abuse-state-machine-contract", "--config", str(example_config_path())])
    assert human.exit_code == 0
    js = runner.invoke(app, ["phase8", "abuse-state-machine-contract", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    j = json.loads(js.stdout)
    assert j["final_decision"] == "BLOCKED"
    assert j["execution_allowed"] is False
    assert j["phase8_acceptance_allowed"] is False
    assert j["abuse_runner_authorized"] is False
    assert j["abuse_state_db_writes_authorized"] is False
    assert j["hard_block_authorized"] is False
    assert j["soft_block_authorized"] is False
    assert j["pause_automation_authorized"] is False
    assert isinstance(j["blockers"], list)


def test_phase8_abuse_state_machine_static_safety() -> None:
    text = Path("mpf/services/phase8_abuse_state_machine_contract_service.py").read_text(encoding="utf-8").lower()
    banned = ["subprocess.run", "subprocess.popen", "os.system", "open(", "\"w\"", "write_text", "psycopg.connect", "insert into", "update", "delete from", "alembic", "migration", "create_engine", "session.add", "session.commit"]
    for b in banned:
        assert b not in text


def test_phase8_abuse_state_machine_blockers_from_config() -> None:
    cfg = load_config(example_config_path())
    cfg.firewall.apply_mode = "manual_apply"
    report = build_phase8_abuse_state_machine_contract_report(cfg)
    assert report["apply_mode_plan_only"] is False
    assert "apply_mode_plan_only_missing_or_failed" in report["blockers"]


def test_phase8_abuse_state_machine_blockers_runtime_activation() -> None:
    cfg = load_config(example_config_path())
    cfg.proxy.runtime_activation_allowed = True
    report = build_phase8_abuse_state_machine_contract_report(cfg)
    assert report["runtime_activation_disabled"] is False
    assert "runtime_activation_disabled_missing_or_failed" in report["blockers"]
