from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")
from mpf.interfaces.cli import app
from mpf.services import firewall_apply_gate_readiness_service


RUNNER = CliRunner()


def test_service_returns_blocked_under_current_gate() -> None:
    cfg = load_config(example_config_path())
    report = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
    assert report["final_decision"] == "BLOCKED"


def test_service_detects_dedicated_doc_and_sync_evidence() -> None:
    cfg = load_config(example_config_path())
    report = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
    assert report["documentation_boundary_present"] is True
    assert report["farm5_0_1_88_sync_evidence_present"] is True


def test_service_current_state_and_dangerous_capabilities() -> None:
    cfg = load_config(example_config_path())
    report = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
    assert report["current_state_preserved"] is True
    for key in (
        "live_firewall_read_allowed",
        "live_firewall_write_allowed",
        "iptables_save_allowed",
        "iptables_restore_allowed",
        "real_adapter_allowed",
        "subprocess_firewall_calls_allowed",
        "restore_point_write_allowed",
        "lock_acquisition_allowed",
        "db_apply_write_allowed",
        "migrations_allowed",
        "customer_nat_allowed",
        "customer_firewall_rules_allowed",
    ):
        assert report[key] is False


def test_service_fails_closed_when_phase_status_missing(tmp_path: Path) -> None:
    cfg = load_config(example_config_path())
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PHASE_6_DEDICATED_APPLY_GATE_PROPOSAL_REVIEW.md").write_text("x", encoding="utf-8")
    report = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg, repo_root=tmp_path)
    assert report["final_decision"] == "BLOCKED"
    assert any("PHASE_STATUS" in b for b in report["blockers"])


def test_service_has_no_subprocess_or_forbidden_commands() -> None:
    text = Path("mpf/services/firewall_apply_gate_readiness_service.py").read_text(encoding="utf-8").lower()
    assert "import subprocess" not in text
    assert "subprocess." not in text
    for token in ("os.system(", "popen(", "run("):
        assert token not in text


def test_cli_output_contains_required_lines() -> None:
    res = RUNNER.invoke(app, ["firewall", "apply-gate-readiness", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "final_decision: BLOCKED" in res.output
    assert "live_firewall_read_allowed: false" in res.output
    assert "iptables_save_allowed: false" in res.output
    assert "customer_nat_allowed: false" in res.output
    assert "next_operator_action:" in res.output
