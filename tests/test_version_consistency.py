from __future__ import annotations

from pathlib import Path
import tomllib

import mpf


EXPECTED_VERSION = "0.1.280"


def test_version_sources_are_consistent() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    version_file = (repo_root / "VERSION").read_text(encoding="utf-8").strip()
    pyproject_data = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_version = pyproject_data["project"]["version"]
    assert version_file == pyproject_version == mpf.__version__
    assert version_file == EXPECTED_VERSION


def test_ci_dev_extra_installs_pytest() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject_data = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = pyproject_data["project"]["optional-dependencies"]["dev"]
    assert any(dependency.startswith("pytest") for dependency in dev_dependencies)


def test_lifecycle_execution_evidence_doc_contains_expected_result() -> None:
    text = Path("docs/PHASE_11_FARM5_0_1_279_LIFECYCLE_EXECUTION_EVIDENCE.md").read_text(encoding="utf-8")
    assert "repository_version: 0.1.279" in text
    assert "PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY" in text
    assert "production_customer_lifecycle_execution: READY" in text
