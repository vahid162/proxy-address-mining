from pathlib import Path
import tomllib

from typer.testing import CliRunner

from mpf.__init__ import __version__
from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.firewall_no_customer_apply_package_service import build_no_customer_apply_package_report

EXPECTED_VERSION = "0.1.136"


def example_config_path() -> Path:
    return Path("configs/mpf.example.yaml")


def _cfg():
    return load_config(example_config_path())


def test_version_consistency():
    assert Path("VERSION").read_text().strip() == EXPECTED_VERSION
    assert tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"] == EXPECTED_VERSION
    assert __version__ == EXPECTED_VERSION
    r = CliRunner().invoke(app, ["--version"])
    assert EXPECTED_VERSION in r.output


def test_package_default_report():
    r = build_no_customer_apply_package_report(_cfg())
    assert r["component"] == "firewall_no_customer_apply_package"
    assert r["final_decision"] == "BLOCKED"
    assert r["authorization_status"] == "PACKAGE_DEFINED_NOT_EXECUTABLE"
    assert r["execution_allowed"] is False
    assert r["apply_decision"] == r["verify_decision"] == r["rollback_decision"] == "BLOCKED"
    assert all(i["executable"] is False and i["executed"] is False for i in r["modeled_sequence"])
