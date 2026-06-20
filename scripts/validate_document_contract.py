#!/usr/bin/env python3
"""Validate repository document and version contracts without runtime imports."""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FILES = (
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "VERSION",
    "pyproject.toml",
    "mpf/__init__.py",
    "docs/INDEX.md",
    "docs/PHASE_STATUS.md",
    "docs/DEBUG_LOG.md",
    "docs/history/PHASE_STATUS_LEGACY_0.1.302.md",
    "docs/PRD.md",
    "docs/GUIDELINES.md",
    "docs/SAFETY.md",
    "docs/ARCHITECTURE.md",
    "docs/ROADMAP.md",
    "docs/REMAINING_PHASE_PLAN.md",
    "docs/AI_PHASE_10_TASK.md",
    "docs/WORKER_POLICY.md",
    "docs/CONTROL_RULES.md",
    "docs/PRODUCT_ROLES_AND_UX.md",
    "docs/HISTORICAL_COMPATIBILITY_ANCHORS.md",
    "docs/ADR/0001-runtime-first-service-layer-boundary.md",
    ".github/PULL_REQUEST_TEMPLATE/runtime-first.md",
    ".github/workflows/ci.yml",
)
LEGACY_ARCHIVES = {
    "docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md": (
        "# Non-authorizing historical snapshot\n\n"
        "This file preserves the complete prior active `docs/REMAINING_PHASE_PLAN.md` as historical planning context for audit and continuity. "
        "It is non-authorizing and must not override `AGENTS.md`, the active `docs/PHASE_STATUS.md`, or current canonical contracts.\n\n"
        "---\n"
    ),
    "docs/history/AI_PHASE_10_TASK_LEGACY_0.1.303.md": (
        "# Non-authorizing historical snapshot\n\n"
        "This file preserves the complete prior active `docs/AI_PHASE_10_TASK.md` as historical Phase 10 task context for audit and continuity. "
        "It is non-authorizing and must not override `AGENTS.md`, the active `docs/PHASE_STATUS.md`, or current canonical contracts.\n\n"
        "---\n"
    ),
}
ACTIVE_REDIRECTS = {
    "docs/REMAINING_PHASE_PLAN.md": "docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md",
    "docs/AI_PHASE_10_TASK.md": "docs/history/AI_PHASE_10_TASK_LEGACY_0.1.303.md",
}
STALE_ACTIVE_DOCS = (
    "docs/REMAINING_PHASE_PLAN.md",
    "docs/AI_PHASE_10_TASK.md",
    "docs/WORKER_POLICY.md",
    "docs/CONTROL_RULES.md",
    "docs/PRODUCT_ROLES_AND_UX.md",
)
STALE_ACTIVE_PATTERNS = (
    "Current Position",
    "Current Position update",
    "Active Target Position",
    "Current boundary",
    "current_working_phase: Phase",
    "Current accepted phase is Phase",
    "Current working phase is Phase",
    "Repository version after this PR is 0.1.",
    "Current repository state:",
    "At the time this contract is added, the working phase is:",
    "Phase 5 is **DB-only**",
    "Strictly forbidden in Phase 5",
)
INIT_STALE_PATTERNS = (
    "Current repository state:",
    "Phase 11",
    "Phase 12",
    "controlled_cli_limited",
    "worker enforcement",
    "unrestricted production expansion",
)
ENTRYPOINTS = ("README.md", "AGENTS.md", "docs/INDEX.md")
LINK_CHECK_FILES = ("AGENTS.md", "README.md", "docs/INDEX.md", "CONTRIBUTING.md")
CANONICAL_INDEX_ROUTES = (
    "docs/PRD.md",
    "docs/GUIDELINES.md",
    "docs/ROADMAP.md",
    "docs/HISTORICAL_COMPATIBILITY_ANCHORS.md",
    "docs/ADR/0001-runtime-first-service-layer-boundary.md",
)
STATIC_CANONICAL_DOCS = (
    "docs/PRD.md",
    "docs/GUIDELINES.md",
    "docs/ROADMAP.md",
    "docs/HISTORICAL_COMPATIBILITY_ANCHORS.md",
    "docs/ADR/0001-runtime-first-service-layer-boundary.md",
    "docs/ARCHITECTURE.md",
    "docs/SAFETY.md",
)
SNAPSHOT_KEYS = (
    "current_accepted_phase",
    "current_working_phase",
    "next_required_step",
    "production_traffic",
    "customer_onboarding_allowed",
    "phase12_start_allowed",
    "firewall_apply_allowed",
    "abuse_automation_allowed",
    "worker_enforcement_allowed",
    "ui_allowed",
    "telegram_allowed",
)


@dataclass(frozen=True)
class ValidationResult:
    violations: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.violations


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_code_fences(markdown: str) -> str:
    lines: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def _markdown_links(markdown: str) -> list[str]:
    text = _strip_code_fences(markdown)
    return [m.group(1).strip() for m in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text)]


def _is_ignored_link(target: str) -> bool:
    lower = target.lower()
    return lower.startswith(("http://", "https://", "mailto:")) or target.startswith("#")


def _link_path(target: str) -> str:
    target = target.split()[0]
    target = target.split("#", 1)[0]
    return target


def _version_from_init(text: str) -> str | None:
    match = re.search(r'(?m)^__version__\s*=\s*["\']([^"\']+)["\']\s*$', text)
    return match.group(1) if match else None



def _validate_phase_status(root_path: Path, violations: list[str]) -> None:
    path = root_path / "docs/PHASE_STATUS.md"
    if not path.is_file():
        return
    text = _read(path)
    if not text.startswith("# PHASE STATUS\n"):
        violations.append("docs/PHASE_STATUS.md must start with '# PHASE STATUS'")
    first_title = text.lstrip().splitlines()[0] if text.strip() else ""
    if first_title != "# PHASE STATUS":
        violations.append("docs/PHASE_STATUS.md must not have release notes or historical narrative before '# PHASE STATUS'")
    required = (
        "Authority and scope",
        "Repository state",
        "Current phase and authorization",
        "Next required step",
        "Required evidence before runtime action",
        "Active task documents",
        "Historical records",
    )
    for heading in required:
        if f"## {heading}" not in text:
            violations.append(f"docs/PHASE_STATUS.md missing required heading: {heading}")


def _validate_legacy_phase_status(root_path: Path, violations: list[str]) -> None:
    path = root_path / "docs/history/PHASE_STATUS_LEGACY_0.1.302.md"
    if not path.is_file():
        return
    text = _read(path)
    required_prefix = (
        "# Non-authorizing historical snapshot\n\n"
        "This file preserves the complete prior active `docs/PHASE_STATUS.md` as historical context for audit and continuity. "
        "It is non-authorizing and must not override `AGENTS.md`, the active `docs/PHASE_STATUS.md`, or current canonical contracts.\n\n"
        "---\n"
    )
    if not text.startswith(required_prefix):
        violations.append("docs/history/PHASE_STATUS_LEGACY_0.1.302.md must begin with the non-authorizing notice and separator")


def _validate_retired_phase_snapshots(root_path: Path, violations: list[str]) -> None:
    for rel, prefix in LEGACY_ARCHIVES.items():
        path = root_path / rel
        if not path.is_file():
            violations.append(f"Missing required non-authorizing archive: {rel}")
            continue
        text = _read(path)
        if not text.startswith(prefix):
            violations.append(f"{rel} must begin with the required non-authorizing notice and separator")

    for rel, archive in ACTIVE_REDIRECTS.items():
        path = root_path / rel
        if not path.is_file():
            continue
        text = _read(path)
        lower = text.lower()
        if "docs/PHASE_STATUS.md" not in text:
            violations.append(f"{rel} must route current state to docs/PHASE_STATUS.md")
        if archive not in text:
            violations.append(f"{rel} must link to preserved archive: {archive}")
        if "compatibility" not in lower or ("historical" not in lower and "non-authorizing" not in lower):
            violations.append(f"{rel} must state its historical/non-authorizing compatibility purpose")

    for rel in STALE_ACTIVE_DOCS:
        path = root_path / rel
        if not path.is_file():
            continue
        text = _read(path)
        for pattern in STALE_ACTIVE_PATTERNS:
            if pattern in text:
                violations.append(f"{rel} contains stale active-state snapshot marker: {pattern}")

    init_path = root_path / "mpf/__init__.py"
    if init_path.is_file():
        text = _read(init_path)
        if "docs/PHASE_STATUS.md" not in text:
            violations.append("mpf/__init__.py must point runtime authorization to docs/PHASE_STATUS.md")
        if "Importing this package performs no DB, firewall, conntrack, Docker, or systemd mutation." not in text:
            violations.append("mpf/__init__.py must preserve the non-mutating import guarantee")
        for pattern in INIT_STALE_PATTERNS:
            if pattern in text:
                violations.append(f"mpf/__init__.py contains stale dynamic-state prose: {pattern}")

def validate_document_contract(root: str | Path = ".") -> ValidationResult:
    root_path = Path(root).resolve()
    violations: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root_path / rel).is_file():
            violations.append(f"Missing required canonical file: {rel}")

    history_dir = root_path / "docs/history"
    if not history_dir.is_dir():
        violations.append("Missing required non-authorizing history directory: docs/history/")

    version_file = root_path / "VERSION"
    pyproject_file = root_path / "pyproject.toml"
    init_file = root_path / "mpf/__init__.py"
    current_version = None
    if version_file.is_file():
        current_version = _read(version_file).strip()
        if not current_version:
            violations.append("VERSION is empty")
    if pyproject_file.is_file() and current_version is not None:
        try:
            project_version = tomllib.loads(_read(pyproject_file)).get("project", {}).get("version")
        except tomllib.TOMLDecodeError as exc:
            project_version = None
            violations.append(f"pyproject.toml is invalid TOML: {exc}")
        if project_version != current_version:
            violations.append(f"Version mismatch: VERSION={current_version!r}, pyproject.toml project.version={project_version!r}")
    if init_file.is_file() and current_version is not None:
        init_version = _version_from_init(_read(init_file))
        if init_version != current_version:
            violations.append(f"Version mismatch: VERSION={current_version!r}, mpf/__init__.py __version__={init_version!r}")

    changelog = root_path / "CHANGELOG.md"
    if changelog.is_file() and current_version:
        if not re.search(rf"(?m)^##\s+{re.escape(current_version)}(?:\s|$)", _read(changelog)):
            violations.append(f"CHANGELOG.md is missing a top-level heading for current version {current_version}")

    _validate_phase_status(root_path, violations)
    _validate_legacy_phase_status(root_path, violations)
    _validate_retired_phase_snapshots(root_path, violations)

    for rel in ENTRYPOINTS:
        path = root_path / rel
        if not path.is_file():
            continue
        text = _read(path)
        if "docs/PHASE_STATUS.md" not in text and "PHASE_STATUS.md" not in text:
            violations.append(f"{rel} must explicitly route dynamic project state to docs/PHASE_STATUS.md")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if re.match(rf"^\s*({'|'.join(re.escape(k) for k in SNAPSHOT_KEYS)})\s*:", line):
                violations.append(f"{rel}:{lineno} contains forbidden dynamic-state assignment snapshot: {line.strip()}")
            lower = line.lower()
            if "docs/history" in lower and any(word in lower for word in ("authority", "authoritative", "current phase", "dynamic state")):
                if not any(word in lower for word in ("non-authorizing", "not authority", "not override", "historical", "audit", "context")):
                    violations.append(f"{rel}:{lineno} appears to use docs/history/ as canonical dynamic-state authority")


    index_path = root_path / "docs/INDEX.md"
    if index_path.is_file():
        index_links = {_link_path(link) for link in _markdown_links(_read(index_path))}
        for route in CANONICAL_INDEX_ROUTES:
            if route not in index_links and route.removeprefix("docs/") not in index_links:
                violations.append(f"docs/INDEX.md must link to canonical route: {route}")
        for route in ("docs/DEBUG_LOG.md", "docs/history/PHASE_STATUS_LEGACY_0.1.302.md"):
            if route not in index_links and route.removeprefix("docs/") not in index_links:
                violations.append(f"docs/INDEX.md must link to canonical route: {route}")

    for rel in (*STATIC_CANONICAL_DOCS, "docs/DEBUG_LOG.md"):
        path = root_path / rel
        if not path.is_file():
            continue
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if re.match(rf"^\s*({'|'.join(re.escape(k) for k in SNAPSHOT_KEYS)})\s*:", line):
                violations.append(f"{rel}:{lineno} contains forbidden dynamic-state assignment snapshot: {line.strip()}")

    for rel in LINK_CHECK_FILES:
        path = root_path / rel
        if not path.is_file():
            continue
        for target in _markdown_links(_read(path)):
            if _is_ignored_link(target):
                continue
            link = _link_path(target)
            if not link:
                continue
            resolved = (path.parent / link).resolve()
            try:
                resolved.relative_to(root_path)
            except ValueError:
                violations.append(f"{rel} has relative markdown link escaping repository: {target}")
                continue
            if not resolved.exists():
                violations.append(f"{rel} has broken relative markdown link: {target}")

    return ValidationResult(tuple(violations))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository document contracts.")
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1], help="repository root (default: script parent repository)")
    args = parser.parse_args(argv)
    result = validate_document_contract(args.root)
    if result.violations:
        for violation in result.violations:
            print(f"document-contract violation: {violation}", file=sys.stderr)
        return 1
    print("Document contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
