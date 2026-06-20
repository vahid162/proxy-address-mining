from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import firewall_no_customer_apply_scaffold_service

RUNNER = CliRunner()


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def test_service_default_report_blocked() -> None:
    report = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report(load_config(example_config_path()))
    assert report["final_decision"] == "BLOCKED"
    assert report["authorization_status"] == "NOT_AUTHORIZED_FOR_APPLY"
    assert report["execution_allowed"] is False
    assert report["apply_decision"] == "BLOCKED"
    assert report["verify_decision"] == "BLOCKED"
    assert report["rollback_decision"] == "BLOCKED"


def test_safety_flags_false() -> None:
    report = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report(load_config(example_config_path()))
    for key in ("iptables_restore_executed", "subprocess_firewall_calls_executed", "real_adapter_executed", "restore_point_written", "lock_acquired", "db_apply_record_written", "db_mutation", "filesystem_write_executed", "customer_nat_changed", "customer_firewall_rules_changed", "production_traffic_changed"):
        assert report[key] is False


def test_cli_human_and_json() -> None:
    human = RUNNER.invoke(app, ["firewall", "no-customer-apply-scaffold", "--config", str(example_config_path())])
    assert human.exit_code == 0
    assert "component: firewall_no_customer_apply_scaffold" in human.output
    assert "final_decision: BLOCKED" in human.output
    js = RUNNER.invoke(app, ["firewall", "no-customer-apply-scaffold", "--config", str(example_config_path()), "--output", "json"])
    assert js.exit_code == 0
    assert '"iptables_restore_executed": false' in js.output


def test_missing_evidence_blockers(tmp_path: Path) -> None:
    cfg = load_config(example_config_path())
    docs = tmp_path / "docs"
    docs.mkdir()
    docs.joinpath("PHASE_STATUS.md").write_text("## Current State\n```text\ncurrent_accepted_phase: bad\n```", encoding="utf-8")
    report = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report(cfg, repo_root=tmp_path)
    assert report["final_decision"] == "BLOCKED"
    assert any("Current State" in b for b in report["blockers"])


def test_static_safety_tokens() -> None:
    text = Path("mpf/services/firewall_no_customer_apply_scaffold_service.py").read_text(encoding="utf-8").lower()
    for token in ("subprocess.run", "os.system", "iptables-restore", "conntrack", "docker", "systemctl", "write_text", "psycopg.connect", "insert into", "update ", "delete from", "alembic", "migration"):
        assert token not in text


def test_docs_regression() -> None:
    phase = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md").read_text(encoding="utf-8")
    assert "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5" in phase
    assert "### Phase 6 No-Customer Apply/Verify/Rollback Scaffold — Report-Only" in phase
    task = Path("docs/AI_PHASE_6_TASK.md").read_text(encoding="utf-8")
    assert "live firewall reads remain forbidden now." not in task
    assert "unauthorized live firewall reads remain forbidden; the explicitly gated read-only iptables-save snapshot path is authorized and evidenced." in task
    assert "normal -> over_tracking -> over_grace -> hard" in task
    assert "farms-over alone must not harden" in task
    assert "worker-over alone must not harden" in task
