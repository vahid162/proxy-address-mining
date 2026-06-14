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
)
REQUIRED_SECTIONS = (
    "PR class",
    "Current blocker(s) being addressed",
    "next_required_step before this PR",
    "next_required_step after this PR",
    "Runtime deliverable(s) in this PR",
    "Why this is not another report-only PR",
    "If evidence/docs exception",
)
RUNTIME_CLASSES = set(PR_CLASSES) - {"evidence/docs exception"}


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
        cleaned_lines.append(stripped)
    return bool("\n".join(cleaned_lines).strip())


def _selected_classes(body: str) -> list[str]:
    selected = []
    for pr_class in PR_CLASSES:
        pattern = rf"(?im)^\s*[-*]\s*\[[xX]\]\s*{re.escape(pr_class)}\s*$"
        if re.search(pattern, body):
            selected.append(pr_class)
    return selected


def _field_after_label(body: str, label: str) -> str:
    pattern = rf"(?im)^\s*[-*]\s*{re.escape(label)}\s*(.*)$"
    match = re.search(pattern, body)
    return match.group(1).strip() if match else ""


def validate(body: str) -> list[str]:
    errors: list[str] = []
    sections = _sections(body)
    for section in REQUIRED_SECTIONS:
        if section.lower() not in sections:
            errors.append(f"Missing required section: '{section}'. Add a markdown heading named exactly this.")

    selected = _selected_classes(body)
    if not selected:
        errors.append("Choose exactly one PR class by checking one box under 'PR class'.")
    elif len(selected) > 1:
        errors.append(f"Choose only one PR class; currently checked: {', '.join(selected)}.")

    for section in (
        "Current blocker(s) being addressed",
        "next_required_step before this PR",
        "next_required_step after this PR",
    ):
        content = sections.get(section.lower(), "")
        if not _has_content(content):
            errors.append(f"Section '{section}' cannot be empty. Explain it in plain language.")

    selected_class = selected[0] if len(selected) == 1 else None
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
            errors.append(
                "Evidence/docs exception requires the exact next runtime-first PR that must follow."
            )
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_runtime_first_pr_body.py PATH_TO_PR_BODY.md", file=sys.stderr)
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
        return 1
    print("Runtime-first PR body validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
