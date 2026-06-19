from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_runtime_first_pr_body.py"


def test_validator_print_template_command_outputs_runtime_first_sections() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--print-template"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert "## Why" in result.stdout
    assert "## PR class" in result.stdout
    assert "## Runtime deliverable(s) in this PR" in result.stdout
    assert "## If evidence/docs exception" in result.stdout
    assert "governance-documentation" in result.stdout


def test_validator_print_template_governance_documentation_outputs_minimal_sections() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--print-template", "governance-documentation"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert "## Why" in result.stdout
    assert "## What" in result.stdout
    assert "## How to test" in result.stdout
    assert "- [x] governance-documentation" in result.stdout
    assert "Version: X.Y.Z" not in result.stdout
