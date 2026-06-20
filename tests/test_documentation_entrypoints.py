from pathlib import Path


def test_docs_index_is_concise_task_routed_entrypoint():
    text = Path("docs/INDEX.md").read_text()
    assert text.startswith("# Documentation Index\n")
    for heading in (
        "## Authority order",
        "## Required reading",
        "## Core contracts",
        "## Task routing",
        "## Historical references",
    ):
        assert heading in text
    for expected in (
        "`AGENTS.md` = AI operating instructions",
        "`docs/PHASE_STATUS.md` = only dynamic project-state authority",
        "`docs/SAFETY.md` = safety restrictions",
        "`docs/ARCHITECTURE.md` = architecture boundaries",
        "`CHANGELOG.md` = release history",
        "`docs/history/` = non-authorizing historical context",
    ):
        assert expected in text


def test_docs_index_does_not_duplicate_dynamic_or_historical_detail():
    text = Path("docs/INDEX.md").read_text()
    for forbidden in (
        "current_accepted_phase:",
        "current_working_phase:",
        "next_required_step",
        "farm5 0.1.",
        "docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md",
        "docs/PHASE_11_FARM5_",
        "production_traffic=",
        "customer_onboarding_allowed=",
    ):
        assert forbidden not in text


def test_legacy_archives_have_required_notice():
    notice = (
        "# Historical Reference\n\n"
        "This file preserves the former active document for historical context.\n\n"
        "It is non-authorizing.\n"
        "Current dynamic project state is defined only by `docs/PHASE_STATUS.md`.\n"
        "Current AI instructions are defined by root `AGENTS.md`.\n\n"
    )
    for path in (
        Path("docs/history/README_LEGACY_0.1.299.md"),
        Path("docs/history/INDEX_LEGACY_0.1.299.md"),
    ):
        assert path.read_text().startswith(notice)
