from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.health import HealthStatus
from mpf.interfaces.cli import app
from mpf.services import proxy_doctor_service

RUNNER = CliRunner()
EXAMPLE_CONFIG = Path("configs/mpf.example.yaml")


def test_proxy_read_only_commands_are_available() -> None:
    for args in (["proxy", "doctor"], ["proxy", "status"], ["proxy", "config-check"]):
        result = RUNNER.invoke(app, [*args, "--config", str(EXAMPLE_CONFIG)])
        assert result.exit_code == 0
        assert "final_verdict:" in result.output


def test_proxy_runtime_commands_are_not_available() -> None:
    forbidden = [
        ["proxy", "start"],
        ["proxy", "up"],
        ["proxy", "restart"],
        ["proxy", "apply"],
        ["proxy", "stop"],
    ]
    for args in forbidden:
        result = RUNNER.invoke(app, args)
        assert result.exit_code != 0


def test_proxy_config_check_accepts_localhost_ui_bind() -> None:
    report = proxy_doctor_service.config_check(EXAMPLE_CONFIG)
    checks = {check.key: check for check in report.checks}
    assert checks["v2raya_ui_local_only"].status == HealthStatus.OK
    assert checks["proxy.runtime_activation_allowed"].status == HealthStatus.OK


def test_proxy_doctor_marks_missing_compose_file_as_not_ok() -> None:
    report = proxy_doctor_service.run(EXAMPLE_CONFIG)
    checks = {check.key: check for check in report.checks}
    assert checks["compose_file_exists"].status in {HealthStatus.WARN, HealthStatus.CRITICAL}
    assert checks["compose_file_exists"].status != HealthStatus.OK


def test_public_v2raya_bind_is_critical(tmp_path: Path) -> None:
    config_path = tmp_path / "mpf.yaml"
    text = EXAMPLE_CONFIG.read_text(encoding="utf-8").replace("ui_bind_host: 127.0.0.1", "ui_bind_host: 0.0.0.0")
    config_path.write_text(text, encoding="utf-8")

    report = proxy_doctor_service.config_check(config_path)
    checks = {check.key: check for check in report.checks}
    assert checks["v2raya_ui_local_only"].status == HealthStatus.CRITICAL


def test_public_forwarder_bind_is_critical(tmp_path: Path) -> None:
    config_path = tmp_path / "mpf.yaml"
    text = EXAMPLE_CONFIG.read_text(encoding="utf-8").replace("bind_host: 127.0.0.1", "bind_host: 0.0.0.0")
    config_path.write_text(text, encoding="utf-8")

    cfg = load_config(config_path)
    checks = proxy_doctor_service.build_checks(cfg)
    by_key = {check.key: check for check in checks}
    assert by_key["lane.btc.forwarder_bind"].status == HealthStatus.CRITICAL
