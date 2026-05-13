from pathlib import Path


def test_changelog_heading_and_0185_order() -> None:
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert text.startswith("# Changelog")
    header_pos = text.find("# Changelog")
    v85_pos = text.find("## 0.1.85 - 2026-05-13")
    assert v85_pos > header_pos

    pre_header = text[:header_pos]
    assert "## 0." not in pre_header
