from pathlib import Path


README = Path("README.md")
PHASE_STATUS = Path("docs/PHASE_STATUS.md")
README_LEGACY = Path("docs/history/README_LEGACY_0.1.299.md")
INDEX_LEGACY = Path("docs/history/INDEX_LEGACY_0.1.299.md")


def test_readme_is_concise_human_entrypoint_without_dynamic_state():
    text = README.read_text()
    assert text.startswith("# Proxy Address Mining\n")
    for link in (
        "[AGENTS.md](AGENTS.md)",
        "[Documentation index](docs/INDEX.md)",
        "[Phase status](docs/PHASE_STATUS.md)",
        "[Safety](docs/SAFETY.md)",
        "[Architecture](docs/ARCHITECTURE.md)",
        "[Changelog](CHANGELOG.md)",
        "[Version](VERSION)",
    ):
        assert link in text
    for forbidden in (
        "next_required_step",
        "farm evidence",
        "Phase 6",
        "Phase 11 operational completion",
        "production_traffic =",
        "firewall_apply_allowed =",
        "customer_onboarding_allowed =",
    ):
        assert forbidden not in text


def test_current_dynamic_state_lives_in_phase_status_not_readme():
    readme = README.read_text()
    phase_status = PHASE_STATUS.read_text()
    for expected in (
        "next_required_step",
        "production_traffic",
        "customer_onboarding_allowed",
        "Phase 11",
    ):
        assert expected in phase_status
    assert "next_required_step" not in readme
    assert "production_traffic =" not in readme
    assert "customer_onboarding_allowed =" not in readme


def test_legacy_readme_preserves_prior_dynamic_boundary_as_non_authorizing_history():
    text = README_LEGACY.read_text()
    assert text.startswith("# Historical Reference\n")
    assert "It is non-authorizing." in text
    assert "Current dynamic project state is defined only by `docs/PHASE_STATUS.md`." in text
    assert "Current AI instructions are defined by root `AGENTS.md`." in text
    assert "## Current Status" in text
    assert "## Current Accepted/Working Boundary" in text
    assert "production_traffic = controlled_cli_limited" in text
    assert "firewall_apply_allowed = controlled" in text


def test_legacy_index_preserves_prior_historical_reading_lists_as_non_authorizing_history():
    text = INDEX_LEGACY.read_text()
    assert text.startswith("# Historical Reference\n")
    assert "It is non-authorizing." in text
    assert "## Current Phase Contracts" in text
    assert "docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md" in text
    assert "docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md" in text


def test_ai_coding_rules_marks_old_phase11_stop_condition_historical():
    text = Path("docs/AI_CODING_RULES.md").read_text()
    assert "Historical pre-final-acceptance Phase 11 planning-readiness stop condition (non-authorizing reference only):" in text
    assert "\nPhase 11 planning-readiness stop condition:" not in text


def test_agents_historical_phase6_list_does_not_override_controlled_boundary():
    text = Path("docs/history/AGENTS_LEGACY_0.1.298.md").read_text()
    assert "historical Phase 6 reference only; this list does not override the accepted Phase 11 controlled boundary" in text
    assert "only controlled CLI/service-layer onboarding, planner-driven customer NAT/firewall handling" in text
    assert "Unrestricted expansion and direct or ad-hoc DB/firewall/runtime mutation remain forbidden" in text
    assert "constraints still forbidden now" not in text
