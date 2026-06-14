from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_runtime_first_pr_body.py"
TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
COPILOT_INSTRUCTIONS = ROOT / ".github" / "copilot-instructions.md"
RULE_DOC = ROOT / "docs" / "AI_RUNTIME_FIRST_PR_FLOW_RULE.md"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED_FIELDS = [
    "PR class",
    "implementation",
    "controlled-runtime",
    "verifier-doctor-package",
    "runtime-first bundle",
    "acceptance-review",
    "evidence/docs exception",
    "Current blocker(s) being addressed",
    "next_required_step before this PR",
    "next_required_step after this PR",
    "Runtime deliverable(s) in this PR",
    "Why this is not another report-only PR",
    "If evidence/docs exception",
    "Why runtime-first work is unsafe, blocked, or technically impossible",
    "Exact next runtime-first PR that must follow",
]

PR_BODY_PREVALIDATION_PHRASES = [
    "python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md",
    "gh pr create --body-file /tmp/pr_body.md",
]


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


def _body(pr_class: str, *, deliverables: str = "- Adds a verifier primitive.", exception: str = "") -> str:
    checked = {
        "implementation": " ",
        "controlled-runtime": " ",
        "verifier-doctor-package": " ",
        "runtime-first bundle": " ",
        "acceptance-review": " ",
        "evidence/docs exception": " ",
    }
    checked[pr_class] = "x"
    return f"""
## Why

Keep runtime-first governance enforceable.

## What

- Add validation.

## How to test

python -m pytest -q tests/test_ai_runtime_first_project_governance.py

Version: 0.1.257 -> 0.1.258

## PR class
- [{checked['implementation']}] implementation
- [{checked['controlled-runtime']}] controlled-runtime
- [{checked['verifier-doctor-package']}] verifier-doctor-package
- [{checked['runtime-first bundle']}] runtime-first bundle
- [{checked['acceptance-review']}] acceptance-review
- [{checked['evidence/docs exception']}] evidence/docs exception

## Current blocker(s) being addressed

Known blocker exists and must not be bypassed by another report-only PR.

## next_required_step before this PR

implement_runtime_first_governance_guard

## next_required_step after this PR

use_validated_runtime_first_pr_body

## Runtime deliverable(s) in this PR

{deliverables}

## Why this is not another report-only PR

It adds an executable validator and tests.

## If evidence/docs exception
{exception}
"""


def test_pr_template_contains_all_runtime_first_required_fields() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    for field in REQUIRED_FIELDS:
        assert field in text


def test_pr_template_tells_ai_agents_to_prevalidate_pr_body_before_creation() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    for phrase in PR_BODY_PREVALIDATION_PHRASES:
        assert phrase in text
    assert "generic Motivation/Description/Testing-only body" in text


def test_copilot_instructions_require_body_file_validation_before_pr_creation() -> None:
    text = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    for phrase in PR_BODY_PREVALIDATION_PHRASES:
        assert phrase in text
    assert "Mandatory PR creation contract for AI agents" in text
    assert "Do not replace the validated body with an auto-generated summary" in text


def test_validator_rejects_weak_report_only_pr_body(tmp_path: Path) -> None:
    result = _run_validator(tmp_path, "## Why\n\nOnly records evidence.\n")
    assert result.returncode != 0
    assert "Missing required section" in result.stderr
    assert "Choose exactly one PR class" in result.stderr


def test_validator_rejects_evidence_docs_exception_without_hard_blocker_and_exact_next_pr(tmp_path: Path) -> None:
    body = _body("evidence/docs exception", deliverables="")
    result = _run_validator(tmp_path, body)
    assert result.returncode != 0
    assert "requires a hard blocker" in result.stderr
    assert "exact next runtime-first PR" in result.stderr


def test_validator_accepts_valid_implementation_pr_body(tmp_path: Path) -> None:
    result = _run_validator(tmp_path, _body("implementation"))
    assert result.returncode == 0, result.stderr
    assert "validation passed" in result.stdout


def test_validator_accepts_valid_runtime_first_bundle_with_multiple_related_deliverables(tmp_path: Path) -> None:
    deliverables = """
- Adds a package verifier.
- Adds a doctor guard for the same operational gate.
- Adds acceptance-review evidence for the same blocker.
"""
    result = _run_validator(tmp_path, _body("runtime-first bundle", deliverables=deliverables))
    assert result.returncode == 0, result.stderr


def test_validator_accepts_valid_evidence_docs_exception_only_with_hard_blocker_and_exact_next_pr(tmp_path: Path) -> None:
    exception = """
- Why runtime-first work is unsafe, blocked, or technically impossible: farm5 evidence is missing for the controlled packet-path bundle, so execution-package changes would be speculative.
- Exact next runtime-first PR that must follow: test(ai): add controlled packet-path package verifier for the collected farm5 bundle
"""
    result = _run_validator(tmp_path, _body("evidence/docs exception", deliverables="", exception=exception))
    assert result.returncode == 0, result.stderr


def test_runtime_first_rule_doc_contains_required_governance_rules() -> None:
    text = RULE_DOC.read_text(encoding="utf-8")
    for phrase in [
        "No repeated report-only PRs",
        "Known blocker and next_required_step",
        "Readiness-only counts as report-only",
        "package",
        "verifier",
        "doctor",
        "execution gate",
        "acceptance-review artifact",
        "Runtime-first bundle PRs",
        "preferred over unnecessary tiny PRs",
        "Mandatory PR body validation before PR creation",
    ]:
        assert phrase in text


def test_runtime_first_rule_doc_requires_body_file_validation_before_pr_creation() -> None:
    text = RULE_DOC.read_text(encoding="utf-8")
    for phrase in PR_BODY_PREVALIDATION_PHRASES:
        assert phrase in text
    assert "Do not create a PR with a generic" in text
    assert "This local validation is mandatory even though CI validates the PR body again" in text


def test_ci_validates_runtime_first_pr_body_before_tests() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "name: Validate runtime-first PR body" in text
    assert "types: [opened, synchronize, reopened, edited]" in text
    assert "if: github.event_name == 'pull_request'" in text
    assert "PR_BODY: ${{ github.event.pull_request.body }}" in text
    assert "python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md" in text
    assert text.index("name: Validate runtime-first PR body") < text.index("name: Run tests")



def test_validator_accepts_required_pr_271_body(tmp_path: Path) -> None:
    body = """
## Why

Prevent repeated report-only/docs-only/evidence-only PRs while allowing coherent runtime-first bundle PRs that advance multiple related deliverables safely under the current accepted gate.

## What

- Adds required runtime-first PR template fields.
- Adds an executable PR body validator.
- Wires the validator into CI for pull_request bodies before pytest.
- Adds regression tests for weak PR bodies, valid implementation PRs, valid runtime-first bundle PRs, and valid evidence/docs exceptions.
- Strengthens AGENTS.md and docs/AI_RUNTIME_FIRST_PR_FLOW_RULE.md.
- Bumps version metadata from 0.1.257 to 0.1.258.

## How to test

- python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
- python -m pytest -q tests/test_ai_runtime_first_project_governance.py
- python -m pytest -q

Version: 0.1.257 -> 0.1.258

Risk + Rollback

Low risk. This PR changes AI governance, PR validation, tests, documentation, and version metadata only. It does not change runtime behavior, DB mutation, firewall mutation, iptables-restore, Docker/systemd/conntrack behavior, production gates, Phase 12, worker enforcement, UI, or Telegram. Rollback by reverting this PR.

## PR class

- [ ] implementation
- [ ] controlled-runtime
- [x] verifier-doctor-package
- [ ] runtime-first bundle
- [ ] acceptance-review
- [ ] evidence/docs exception

## Current blocker(s) being addressed

AI agents could still create repeated report-only/docs-only/evidence-only PRs because runtime-first guidance was documented but not enforced against PR body content or CI.

## next_required_step before this PR

enforce_runtime_first_project_governance

## next_required_step after this PR

create_next_phase11_runtime_first_bundle_for_controlled_reapply_package_or_doctor_acceptance

## Runtime deliverable(s) in this PR

- Executable PR body validator.
- CI validation step for pull_request bodies.
- Regression tests for runtime-first governance.
- Updated PR template and AI governance rules.
- Runtime-first bundle support so AI can take larger coherent steps without splitting work into repeated report-only PRs.

## Why this is not another report-only PR

It adds executable validation, CI enforcement, and regression tests. It is not only documentation or evidence recording.

## If evidence/docs exception

- Why runtime-first work is unsafe, blocked, or technically impossible:
- Exact next runtime-first PR that must follow:
"""
    result = _run_validator(tmp_path, body)
    assert result.returncode == 0, result.stderr
