from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.health import HealthStatus
from mpf.interfaces.cli import app
from mpf.services import proxy_doctor_service

RUNNER = CliRunner()
EXAMPLE_CONFIG = Path("configs/mpf.example.yaml")
COMPOSE_TEMPLATE = Path("compose/mpf-proxy.compose.yaml")


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
    assert checks["firewall_apply_mode_plan_only"].status == HealthStatus.OK


def test_proxy_doctor_sees_compose_template() -> None:
    report = proxy_doctor_service.run(EXAMPLE_CONFIG)
    checks = {check.key: check for check in report.checks}
    assert checks["compose_file_exists"].status == HealthStatus.OK
    assert checks["compose_runtime_profile_guard"].status == HealthStatus.OK
    assert checks["backend_docker_publish_mode.v2raya_ui"].status == HealthStatus.OK
    assert checks["backend_docker_publish_mode.btc"].status == HealthStatus.OK
    assert checks["healthcheck_state"].status == HealthStatus.OK
    assert checks["no_customer_nat_redirects"].status == HealthStatus.OK


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


def test_compose_template_runtime_services_are_profile_guarded() -> None:
    text = COMPOSE_TEMPLATE.read_text(encoding="utf-8")
    assert "phase4-runtime" in text
    assert "docker compose up" not in text


def test_public_backend_publish_in_compose_is_critical(tmp_path: Path) -> None:
    compose_path = tmp_path / "mpf-proxy.compose.yaml"
    compose_text = COMPOSE_TEMPLATE.read_text(encoding="utf-8").replace(
        '"127.0.0.1:60010:60010"',
        '"0.0.0.0:60010:60010"',
    )
    compose_path.write_text(compose_text, encoding="utf-8")

    config_path = tmp_path / "mpf.yaml"
    config_text = EXAMPLE_CONFIG.read_text(encoding="utf-8").replace(
        "compose/mpf-proxy.compose.yaml",
        str(compose_path),
    )
    config_path.write_text(config_text, encoding="utf-8")

    report = proxy_doctor_service.config_check(config_path)
    checks = {check.key: check for check in report.checks}
    assert checks["backend_docker_publish_mode.btc"].status == HealthStatus.CRITICAL


def test_public_v2raya_publish_in_compose_is_critical(tmp_path: Path) -> None:
    compose_path = tmp_path / "mpf-proxy.compose.yaml"
    compose_text = COMPOSE_TEMPLATE.read_text(encoding="utf-8").replace(
        '"127.0.0.1:2015:2017"',
        '"0.0.0.0:2015:2017"',
    )
    compose_path.write_text(compose_text, encoding="utf-8")

    config_path = tmp_path / "mpf.yaml"
    config_text = EXAMPLE_CONFIG.read_text(encoding="utf-8").replace(
        "compose/mpf-proxy.compose.yaml",
        str(compose_path),
    )
    config_path.write_text(config_text, encoding="utf-8")

    report = proxy_doctor_service.config_check(config_path)
    checks = {check.key: check for check in report.checks}
    assert checks["backend_docker_publish_mode.v2raya_ui"].status == HealthStatus.CRITICAL
