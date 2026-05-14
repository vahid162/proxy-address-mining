from pathlib import Path

from mpf.config import load_config
from mpf.services import firewall_no_customer_apply_acceptance_gate_service, firewall_no_customer_apply_scaffold_service
from mpf.services.firewall_no_customer_apply_execution_gate_service import build_no_customer_apply_execution_gate_report


def example_config_path() -> Path:
    return Path('configs/mpf.example.yaml')


def test_execution_gate_default_report():
    cfg = load_config(example_config_path())
    r = build_no_customer_apply_execution_gate_report(cfg)
    assert r["component"] == "firewall_no_customer_apply_execution_gate"
    assert r["final_decision"] == "BLOCKED"
    assert r["authorization_status"] == "NOT_ACCEPTED_FOR_EXECUTION"
    assert r["execution_allowed"] is False
    assert r["apply_decision"] == "BLOCKED"
    assert r["verify_decision"] == "BLOCKED"
    assert r["rollback_decision"] == "BLOCKED"
    assert all(i["status"] in {"PASS", "BLOCKED"} for i in r["execution_readiness_checklist"])
    for key in (
        "live_firewall_write_allowed",
        "live_firewall_apply_allowed",
        "live_firewall_verify_allowed",
        "live_firewall_rollback_allowed",
        "iptables_restore_allowed",
        "iptables_restore_executed",
        "subprocess_firewall_calls_allowed",
        "subprocess_firewall_calls_executed",
        "real_adapter_allowed",
        "real_adapter_executed",
        "restore_point_write_allowed",
        "restore_point_written",
        "lock_acquisition_allowed",
        "lock_acquired",
        "db_apply_record_write_allowed",
        "db_apply_record_written",
        "db_mutation",
        "filesystem_write_executed",
        "customer_nat_allowed",
        "customer_nat_changed",
        "customer_firewall_rules_allowed",
        "customer_firewall_rules_changed",
        "production_traffic_changed",
        "usage_automation_allowed",
        "abuse_automation_allowed_runtime",
        "ui_allowed_runtime",
        "telegram_allowed_runtime",
    ):
        assert r[key] is False


def test_scaffold_dependency_iptables_restore_allowed_blocked(monkeypatch):
    cfg = load_config(example_config_path())
    orig = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report
    monkeypatch.setattr(
        firewall_no_customer_apply_scaffold_service,
        "build_no_customer_apply_scaffold_report",
        lambda *a, **k: {**orig(*a, **k), "iptables_restore_allowed": True},
    )
    r = build_no_customer_apply_execution_gate_report(cfg)
    assert r["no_customer_apply_scaffold_mutation_flags_false"] is False
    assert "scaffold mutation flag is true" in r["blockers"]


def test_scaffold_dependency_db_mutation_blocked(monkeypatch):
    cfg = load_config(example_config_path())
    orig = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report
    monkeypatch.setattr(
        firewall_no_customer_apply_scaffold_service,
        "build_no_customer_apply_scaffold_report",
        lambda *a, **k: {**orig(*a, **k), "db_mutation": True},
    )
    r = build_no_customer_apply_execution_gate_report(cfg)
    assert r["no_customer_apply_scaffold_mutation_flags_false"] is False
    assert "scaffold mutation flag is true" in r["blockers"]


def test_acceptance_dependency_iptables_restore_allowed_blocked(monkeypatch):
    cfg = load_config(example_config_path())
    orig = firewall_no_customer_apply_acceptance_gate_service.build_no_customer_apply_acceptance_gate_report
    monkeypatch.setattr(
        firewall_no_customer_apply_acceptance_gate_service,
        "build_no_customer_apply_acceptance_gate_report",
        lambda *a, **k: {**orig(*a, **k), "iptables_restore_allowed": True},
    )
    r = build_no_customer_apply_execution_gate_report(cfg)
    assert r["no_customer_apply_acceptance_gate_mutation_flags_false"] is False
    assert "acceptance gate mutation flag is true" in r["blockers"]


def test_acceptance_dependency_db_mutation_blocked(monkeypatch):
    cfg = load_config(example_config_path())
    orig = firewall_no_customer_apply_acceptance_gate_service.build_no_customer_apply_acceptance_gate_report
    monkeypatch.setattr(
        firewall_no_customer_apply_acceptance_gate_service,
        "build_no_customer_apply_acceptance_gate_report",
        lambda *a, **k: {**orig(*a, **k), "db_mutation": True},
    )
    r = build_no_customer_apply_execution_gate_report(cfg)
    assert r["no_customer_apply_acceptance_gate_mutation_flags_false"] is False
    assert "acceptance gate mutation flag is true" in r["blockers"]
