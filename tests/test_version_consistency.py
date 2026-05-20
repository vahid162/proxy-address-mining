from __future__ import annotations

from pathlib import Path
import tomllib

import mpf


EXPECTED_VERSION = "0.1.152"


def test_version_sources_are_consistent() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    version_file = (repo_root / "VERSION").read_text(encoding="utf-8").strip()

    pyproject_data = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_version = pyproject_data["project"]["version"]

    package_version = mpf.__version__

    assert version_file == pyproject_version == package_version
    assert version_file == EXPECTED_VERSION
