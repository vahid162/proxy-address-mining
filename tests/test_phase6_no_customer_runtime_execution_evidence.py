import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.config import load_config
from mpf.services import firewall_no_customer_runtime_execution_evidence_service


def example_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs" / "mpf.example.yaml"


def test_defaults_blocked_and_flags_false():
    report = firewall_no_customer_runtime_execution_evidence_service.build_no_customer_runtime_execution_evidence_report(load_config(example_config_path()))
    assert report["component"] == "firewall_no_customer_runtime_execution_evidence"
    assert report["final_decision"] == "BLOCKED"
    assert report["authorization_status"] == "CONTROLLED_NO_CUSTOMER_RUNTIME_EVIDENCE_DEFINED_NOT_EXECUTED"
    assert report["execution_allowed"] is False
    assert report["operator_approval_required"] is True
    assert report["fresh_farm5_runtime_execution_evidence_required"] is True
    assert report["separate_runtime_execution_pr_required"] is True
    assert report["apply_decision"] == "BLOCKED"
    assert report["verify_decision"] == "BLOCKED"
    assert report["rollback_decision"] == "BLOCKED"
    for k, v in report.items():
        if k.endswith("_allowed") or k.endswith("_executed") or k.endswith("_written") or k.endswith("_changed"):
            if k in {"operator_approval_required"}:
                continue
            assert v is False


def test_cli_json_and_human():
    runner = CliRunner()
    h = runner.invoke(app, ["firewall", "no-customer-runtime-execution-evidence", "--config", str(example_config_path())])
    assert h.exit_code == 0
    assert "component: firewall_no_customer_runtime_execution_evidence" in h.stdout
    j = runner.invoke(app, ["firewall", "no-customer-runtime-execution-evidence", "--config", str(example_config_path()), "--output", "json"])
    data = json.loads(j.stdout)
    assert data["final_decision"] == "BLOCKED"
    assert data["execution_allowed"] is False
