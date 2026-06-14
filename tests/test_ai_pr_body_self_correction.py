from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_runtime_first_pr_body.py"
COPILOT_INSTRUCTIONS = ROOT / ".github" / "copilot-instructions.md"


def _run_validator(tmp_path: Path, body: str) -> subprocess.CompletedProcess[str]:
    pr_body = tmp_path / "pr_body.md"
    pr_body.write_text(body, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(pr_body)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_validator_rejects_generic_ai_summary_and_prints_recovery_template(tmp_path: Path) -> None:
    body = """
### Motivation

Do a useful thing.

### Description

- A generated summary.

### Testing

- pytest passed locally.
"""
    result = _run_validator(tmp_path, body)
    assert result.returncode == 1
    assert "Generic AI-generated PR body detected" in result.stderr
    assert "Required runtime-first PR body template" in result.stderr
    assert "## PR class" in result.stderr
    assert "## Current blocker(s) being addressed" in result.stderr
    assert "gh pr create --body" not in result.stderr


def test_validator_print_template_command_outputs_copyable_runtime_first_template() -> None:
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


def test_copilot_instructions_describe_ci_failure_recovery() -> None:
    text = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "--print-template" in text
    assert "Validate runtime-first PR body" in text
    assert "copy the template printed in the CI log" in text
    assert "do not create a code-only commit just to fix the body" in text
