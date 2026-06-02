from __future__ import annotations

from pathlib import Path
import tomllib

import mpf


EXPECTED_VERSION = "0.1.235"


def test_version_sources_are_consistent() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    version_file = (repo_root / "VERSION").read_text(encoding="utf-8").strip()

    pyproject_data = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_version = pyproject_data["project"]["version"]

    package_version = mpf.__version__

    assert version_file == pyproject_version == package_version
    assert version_file == EXPECTED_VERSION


def test_package_docstring_matches_phase11_accepted_phase12_working_gate() -> None:
    doc = mpf.__doc__ or ""

    assert "Phase 11 — Production / Customer Activation Gate accepted on farm5" in doc
    assert "Phase 12 — Worker Policy Enforcement is the current working phase" in doc
    assert "controlled_cli_limited for the limited BTC scope only" in doc
    assert "UI, Telegram, worker enforcement, unrestricted production expansion, and unrestricted miner expansion remain closed" in doc
    assert "Importing this package performs no DB, firewall, conntrack, Docker, or systemd mutation" in doc
    assert "Phase 10 Session / Worker / Policy / Share Timeline accepted" not in doc
    assert "Phase 11 Production / Customer Activation Gate planning/readiness" not in doc
