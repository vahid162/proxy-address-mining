#!/usr/bin/env python3
"""Validate runtime-first governance fields in a pull request body."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PR_CLASSES = (
    "implementation",
    "controlled-runtime",
    "verifier-doctor-package",
    "runtime-first bundle",
    "acceptance-review",
    "evidence/docs exception",
    "governance-documentation",
)
STRICT_RUNTIME_CLASSES = set(PR_CLASSES) - {"governance-documentation"}
REQUIRED_STRICT_SECTIONS = (
    "PR class",
    "Current blocker(s) being addressed",
    "next_required_step before this PR",
    "next_required_step after this PR",
    "Runtime deliverable(s) in this PR",
    "Why this is not another report-only PR",
    "If evidence/docs exception",
)
REQUIRED_GOVERNANCE_SECTIONS = ("Why", "What", "How to test", "PR class")
RUNTIME_CLASSES = set(PR_CLASSES) - {"evidence/docs exception", "governance-documentation"}
GENERIC_AI_SUMMARY_HEADINGS = {"motivation", "description", "testing"}
VERSION_LINE_RE = re.compile(r"(?m)^Version:\s*\d+\.\d+\.\d+\s*->\s*\d+\.\d+\.\d+\s*$")
REQUIRED_VALIDATOR_COMMAND = "python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md"
CHECKBOX_RE = re.compile(r"(?im)^\s*[-*]\s*\[[ xX]\]\s*(.+?)\s*$")
REQUIRED_PR_BODY_TEMPLATE = """## Why

<1-2 lines explaining why this PR is needed now.>

## What

- <2-5 concrete changes.>
- <Name the runtime/verifier/doctor/package/acceptance artifact, not only docs.>

## How to test

- python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
- python -m pytest -q <targeted tests>
- python -m pytest -q

Version: X.Y.Z -> A.B.C

Risk + Rollback

<Only include when risk exists. Explain rollback in one line.>

## PR class

- [ ] implementation
- [ ] controlled-runtime
- [ ] verifier-doctor-package
- [ ] runtime-first bundle
- [ ] acceptance-review
- [ ] evidence/docs exception
- [ ] governance-documentation

## Current blocker(s) being addressed

<Concrete blocker from farm5 evidence, PHASE_STATUS, progression code, verifier, or doctor.>

## next_required_step before this PR

<Current next_required_step before this PR.>

## next_required_step after this PR

<Expected next_required_step after this PR.>

## Runtime deliverable(s) in this PR

- <Operator-reviewable runtime/verifier/doctor/package/acceptance artifact.>

## Why this is not another report-only PR

<Explain the executable artifact or tested runtime-first bundle created by this PR.>

## If evidence/docs exception

- Why runtime-first work is unsafe, blocked, or technically impossible:
- Exact next runtime-first PR that must follow:
"""
GOVERNANCE_PR_BODY_TEMPLATE = """<!--
Governance/documentation is only for completed repository-governance outcomes such as CI, templates, validators, AI instructions, or documentation contracts.
It must not be used for runtime/evidence work or to bypass an active runtime blocker.
-->

## Why

<1-2 lines explaining why this governance/documentation PR is needed now.>

## What

- <2-5 concrete governance/documentation changes.>

## How to test

- python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
- python -m pytest -q <targeted tests>
- python -m pytest -q

## PR class

- [ ] implementation
- [ ] controlled-runtime
- [ ] verifier-doctor-package
- [ ] runtime-first bundle
- [ ] acceptance-review
- [ ] evidence/docs exception
- [x] governance-documentation
"""


def _normalize_heading(value: str) -> str:
    return value.strip().rstrip(":").lower()


def _sections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = _normalize_heading(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[name] = body[start:end].strip()
    return sections


def _has_content(text: str) -> bool:
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped in {"-", "*"}:
            continue
        if re.fullmatch(r"[-*]\s*\[[ xX]\]\s*.+", stripped):
            continue
        if stripped.startswith("<!--") or stripped.endswith("-->"):
            continue
        cleaned_lines.append(stripped)
    return bool("\n".join(cleaned_lines).strip())


def _selected_classes(pr_class_section: str) -> list[str]:
    selected = []
    for pr_class in PR_CLASSES:
        pattern = rf"(?im)^\s*[-*]\s*\[[xX]\]\s*{re.escape(pr_class)}\s*$"
        if re.search(pattern, pr_class_section):
            selected.append(pr_class)
    return selected


def _pr_class_options(pr_class_section: str) -> list[str]:
    return [match.group(1).strip() for match in CHECKBOX_RE.finditer(pr_class_section)]


def _field_after_label(body: str, label: str) -> str:
    pattern = rf"(?im)^\s*[-*]\s*{re.escape(label)}\s*(.*)$"
    match = re.search(pattern, body)
    return match.group(1).strip() if match else ""


def _looks_like_generic_ai_summary(sections: dict[str, str]) -> bool:
    return GENERIC_AI_SUMMARY_HEADINGS.issubset(set(sections))


def _validate_class_taxonomy(sections: dict[str, str], errors: list[str]) -> str | None:
    pr_class_section = sections.get("pr class", "")
    selected = _selected_classes(pr_class_section)
    options = _pr_class_options(pr_class_section)
    if options != list(PR_CLASSES):
        unexpected = [option for option in options if option not in PR_CLASSES]
        missing = [option for option in PR_CLASSES if option not in options]
        if unexpected:
            errors.append(
                "PR class contains unofficial checkbox option(s): " + ", ".join(unexpected) + ". "
                "Use only the official runtime-first PR class taxonomy."
            )
        if missing:
            errors.append("PR class is missing official checkbox option(s): " + ", ".join(missing) + ".")
        if not unexpected and not missing:
            errors.append("PR class checkboxes must match the official taxonomy exactly and in canonical order.")
    if not selected:
        errors.append("Choose exactly one PR class by checking one box under 'PR class'.")
    elif len(selected) > 1:
        errors.append(f"Choose only one PR class; currently checked: {', '.join(selected)}.")
    return selected[0] if len(selected) == 1 else None


def validate(body: str) -> list[str]:
    errors: list[str] = []
    sections = _sections(body)
    if _looks_like_generic_ai_summary(sections):
        errors.append(
            "Generic AI-generated PR body detected: replace Motivation/Description/Testing with "
            "the repository runtime-first PR template before creating or updating the PR."
        )

    selected_class = _validate_class_taxonomy(sections, errors)
    if selected_class == "governance-documentation":
        for section in REQUIRED_GOVERNANCE_SECTIONS:
            content = sections.get(section.lower(), "")
            if section.lower() not in sections:
                errors.append(f"Missing required section: '{section}'. Add a markdown heading named exactly this.")
            elif section != "PR class" and not _has_content(content):
                errors.append(f"Section '{section}' cannot be empty. Explain it in plain language.")
        return errors

    for section in REQUIRED_STRICT_SECTIONS:
        if section.lower() not in sections:
            errors.append(f"Missing required section: '{section}'. Add a markdown heading named exactly this.")

    if not VERSION_LINE_RE.search(body):
        errors.append("Missing required SemVer bump line: 'Version: X.Y.Z -> A.B.C'.")

    how_to_test = sections.get("how to test", "")
    if REQUIRED_VALIDATOR_COMMAND not in how_to_test:
        errors.append("Section 'How to test' must include: " f"{REQUIRED_VALIDATOR_COMMAND}")

    for section in (
        "Current blocker(s) being addressed",
        "next_required_step before this PR",
        "next_required_step after this PR",
    ):
        content = sections.get(section.lower(), "")
        if not _has_content(content):
            errors.append(f"Section '{section}' cannot be empty. Explain it in plain language.")

    if selected_class in RUNTIME_CLASSES:
        content = sections.get("runtime deliverable(s) in this pr", "")
        if not _has_content(content):
            errors.append(
                "Runtime-first PR classes must list 'Runtime deliverable(s) in this PR'. "
                "Multiple related deliverables are allowed; do not split a coherent safe bundle just to satisfy this check."
            )
    elif selected_class == "evidence/docs exception":
        blocker = _field_after_label(body, "Why runtime-first work is unsafe, blocked, or technically impossible:")
        next_pr = _field_after_label(body, "Exact next runtime-first PR that must follow:")
        if not blocker:
            errors.append(
                "Evidence/docs exception requires a hard blocker: fill in "
                "'Why runtime-first work is unsafe, blocked, or technically impossible:'."
            )
        if not next_pr:
            errors.append("Evidence/docs exception requires the exact next runtime-first PR that must follow.")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--print-template":
        print(REQUIRED_PR_BODY_TEMPLATE)
        return 0
    if len(argv) == 3 and argv[1] == "--print-template" and argv[2] == "governance-documentation":
        print(GOVERNANCE_PR_BODY_TEMPLATE)
        return 0
    if argv[1:2] == ["--print-template"]:
        print("Usage: validate_runtime_first_pr_body.py --print-template [governance-documentation]", file=sys.stderr)
        return 2
    if len(argv) != 2:
        print("Usage: validate_runtime_first_pr_body.py PATH_TO_PR_BODY.md", file=sys.stderr)
        print("       validate_runtime_first_pr_body.py --print-template [governance-documentation]", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"Error: PR body file not found: {path}", file=sys.stderr)
        return 2
    errors = validate(path.read_text(encoding="utf-8"))
    if errors:
        print("Runtime-first PR body validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("\nRequired runtime-first PR body template:", file=sys.stderr)
        print(REQUIRED_PR_BODY_TEMPLATE, file=sys.stderr)
        print(
            "\nFor completed CI/template/validator/AI-governance/documentation-contract work, use "
            "`python scripts/validate_runtime_first_pr_body.py --print-template governance-documentation`. "
            "Do not use governance-documentation for runtime/evidence work or to bypass an active runtime blocker.",
            file=sys.stderr,
        )
        print(
            "\nFix the PR body, save it to /tmp/pr_body.md, rerun this validator, then create or update the PR body with the validated text.",
            file=sys.stderr,
        )
        return 1
    print("Runtime-first PR body validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
