from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_document_contract.py"
spec = importlib.util.spec_from_file_location("validate_document_contract", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.name is not None
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo(tmp_path: Path) -> Path:
    files = {
        "AGENTS.md": "AGENTS routes dynamic state to docs/PHASE_STATUS.md. [Safety](docs/SAFETY.md)\n",
        "README.md": "README routes dynamic state to docs/PHASE_STATUS.md. [Index](docs/INDEX.md) [External](https://example.com) [Anchor](#local)\n",
        "CONTRIBUTING.md": "Contribute via [AGENTS](AGENTS.md). Ignore `code` and [mail](mailto:test@example.com).\n```\n[Broken](missing.md)\n```\n",
        "CHANGELOG.md": "# Changelog\n\n## 1.2.3\n\n- entry\n",
        "VERSION": "1.2.3\n",
        "pyproject.toml": "[project]\nname = 'x'\nversion = '1.2.3'\n",
        "mpf/__init__.py": "__version__ = '1.2.3'\n",
        "docs/INDEX.md": "Index routes dynamic state to docs/PHASE_STATUS.md and keeps [history](history/) non-authorizing. [PRD](PRD.md) [Guidelines](GUIDELINES.md) [Roadmap](ROADMAP.md) [ADR](ADR/0001-runtime-first-service-layer-boundary.md)\n",
        "docs/PHASE_STATUS.md": "state\n",
        "docs/PRD.md": "product scope routes current state to docs/PHASE_STATUS.md\n",
        "docs/GUIDELINES.md": "engineering rules route current state to docs/PHASE_STATUS.md\n",
        "docs/SAFETY.md": "safety\n",
        "docs/ARCHITECTURE.md": "architecture\n",
        "docs/ROADMAP.md": "roadmap routes current state to docs/PHASE_STATUS.md\n",
        "docs/ADR/0001-runtime-first-service-layer-boundary.md": "adr routes current state to docs/PHASE_STATUS.md\n",
        "docs/history/OLD.md": "old\n",
        ".github/PULL_REQUEST_TEMPLATE/runtime-first.md": "template\n",
        ".github/workflows/ci.yml": "name: CI\n",
    }
    for rel, text in files.items():
        write(tmp_path / rel, text)
    return tmp_path


def violations(root: Path) -> tuple[str, ...]:
    return module.validate_document_contract(root).violations


def test_valid_minimal_repository_contract_passes(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    assert violations(root) == ()


def test_missing_required_file_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "README.md").unlink()
    assert any("Missing required canonical file: README.md" in v for v in violations(root))


def test_missing_prd_or_guidelines_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "docs/PRD.md").unlink()
    assert any("Missing required canonical file: docs/PRD.md" in v for v in violations(root))
    root = make_repo(tmp_path / "second")
    (root / "docs/GUIDELINES.md").unlink()
    assert any("Missing required canonical file: docs/GUIDELINES.md" in v for v in violations(root))


def test_index_missing_canonical_route_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write(root / "docs/INDEX.md", "Index routes dynamic state to docs/PHASE_STATUS.md. [PRD](PRD.md) [Roadmap](ROADMAP.md) [ADR](ADR/0001-runtime-first-service-layer-boundary.md)\n")
    assert any("docs/INDEX.md must link to canonical route: docs/GUIDELINES.md" in v for v in violations(root))


def test_dynamic_state_assignment_in_static_canonical_contract_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write(root / "docs/PRD.md", "Product scope.\nproduction_traffic: open\n")
    assert any("docs/PRD.md:2" in v and "dynamic-state assignment" in v for v in violations(root))


def test_version_mismatch_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write(root / "mpf/__init__.py", "__version__ = '1.2.4'\n")
    assert any("Version mismatch" in v and "__version__" in v for v in violations(root))


def test_missing_changelog_heading_for_current_version_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write(root / "CHANGELOG.md", "# Changelog\n\n## 1.2.2\n\n- old\n")
    assert any("missing a top-level heading" in v for v in violations(root))


def test_dynamic_state_snapshot_in_readme_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write(root / "README.md", "See docs/PHASE_STATUS.md.\nnext_required_step: do_thing\n")
    assert any("README.md:2" in v and "dynamic-state assignment" in v for v in violations(root))


def test_broken_relative_markdown_link_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write(root / "README.md", "Dynamic state: docs/PHASE_STATUS.md. [Broken](docs/MISSING.md)\n")
    assert any("broken relative markdown link" in v for v in violations(root))


def test_external_url_and_anchor_are_ignored(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write(root / "README.md", "Dynamic state: docs/PHASE_STATUS.md. [External](https://example.com/x) [Anchor](#section)\n")
    assert violations(root) == ()


def test_historical_directory_or_authority_routing_violation_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write(root / "docs/INDEX.md", "Dynamic state comes from docs/PHASE_STATUS.md. docs/history/ is authoritative for current phase.\n")
    result = violations(root)
    assert any("docs/history/ as canonical dynamic-state authority" in v for v in result)
    write(root / "docs/INDEX.md", "Index routes dynamic state to docs/PHASE_STATUS.md.\n")
    for child in (root / "docs/history").iterdir():
        child.unlink()
    (root / "docs/history").rmdir()
    assert any("Missing required non-authorizing history directory" in v for v in violations(root))


def test_cli_exit_code_is_non_zero_on_failure_and_zero_on_success(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    ok = subprocess.run([sys.executable, str(SCRIPT), str(root)], text=True, capture_output=True, check=False)
    assert ok.returncode == 0
    assert "Document contract validation passed." in ok.stdout

    (root / "README.md").unlink()
    bad = subprocess.run([sys.executable, str(SCRIPT), str(root)], text=True, capture_output=True, check=False)
    assert bad.returncode != 0
    assert "document-contract violation:" in bad.stderr


def test_required_legacy_preservation_snapshots_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    for rel in (
        "docs/history/ARCHITECTURE_LEGACY_0.1.301.md",
        "docs/history/SAFETY_LEGACY_0.1.301.md",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert text.startswith("# Non-authorizing historical snapshot\n")
        assert "current authority is in the active canonical contracts" in text
        assert "docs/PHASE_STATUS.md" in text
        assert "\n---\n\n# " in text


def test_active_architecture_restores_durable_static_sections() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    for expected in (
        "/etc/mpf/mpf.yaml",
        "/opt/mpf-py",
        "/var/lib/mpf",
        "/var/log/mpf",
        "/var/backups/mpf",
        "lane owns the protocol or coin, backend port, firewall chain prefix, upstreams, forwarder configuration, and enabled state",
        "PostgreSQL is authoritative for production control-plane state",
        "must not become split production state",
        "Customers are service and port allocation records",
        "Future buyer-facing interfaces are read-only first",
        "Worker identity is Stratum-layer evidence",
        "cannot be implemented as firewall-only enforcement",
        "docs/ROADMAP.md",
        "docs/PHASE_STATUS.md",
    ):
        assert expected in text


def test_active_canonical_contracts_have_no_dynamic_state_assignments() -> None:
    root = Path(__file__).resolve().parents[1]
    result = module.validate_document_contract(root)
    assert not [v for v in result.violations if "dynamic-state assignment" in v]
