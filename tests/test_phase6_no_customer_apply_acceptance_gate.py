import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import firewall_no_customer_apply_acceptance_gate_service

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def _cfg():
    return load_config(example_config_path())


def test_service_default_report():
    r = firewall_no_customer_apply_acceptance_gate_service.build_no_customer_apply_acceptance_gate_report(_cfg())
    assert r["component"] == "firewall_no_customer_apply_acceptance_gate"
    assert r["final_decision"] == "BLOCKED"
    assert r["authorization_status"] == "ACCEPTANCE_GATE_DEFINED_NOT_EXECUTABLE"
    assert r["execution_allowed"] is False
    assert r["apply_decision"] == "BLOCKED"
    assert r["verify_decision"] == "BLOCKED"
    assert r["rollback_decision"] == "BLOCKED"


def test_checklist_and_safety_flags_false():
    r = firewall_no_customer_apply_acceptance_gate_service.build_no_customer_apply_acceptance_gate_report(_cfg())
    items = {x["item"]: x["status"] for x in r["acceptance_checklist"]}
    assert "operator_approval_required_for_future_execution" in items
    assert set(items.values()) <= {"PASS", "BLOCKED"}
    for key in (
        "live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed",
        "iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed",
        "real_adapter_allowed","real_adapter_executed","restore_point_write_allowed","restore_point_written","lock_acquisition_allowed",
        "lock_acquired","db_apply_record_write_allowed","db_apply_record_written","db_mutation","filesystem_write_executed",
    ):
        assert r[key] is False


def test_cli_json_and_static_safety():
    js = RUNNER.invoke(app, ["firewall", "no-customer-apply-acceptance-gate", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    data = json.loads(js.output)
    assert data["component"] == "firewall_no_customer_apply_acceptance_gate"
    text = Path("mpf/services/firewall_no_customer_apply_acceptance_gate_service.py").read_text(encoding="utf-8").lower()
    for bad in ("subprocess.run", "os.system", "conntrack", "docker", "systemctl", "write_text", "psycopg.connect", "insert into", "update ", "delete from", "alembic", "migration"):
        assert bad not in text
